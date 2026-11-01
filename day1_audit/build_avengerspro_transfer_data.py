#!/usr/bin/env python3
"""Build audited Avengers-Pro JSONL inputs; no embeddings or router execution.

This study adapter uses origin_query when non-empty, otherwise prompt, to keep
the query convention aligned with this study's feature extractor. The upstream
AvengersProAdaptor uses BaselineRecord.prompt; this is an explicit deviation.
"""
from __future__ import annotations
import argparse, csv, json, math, random, re, sys, tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = [
    "claude-sonnet-4", "deepseek-r1-0528", "deepseek-v3.1-terminus",
    "deepseek-v3-0324", "gemini-2.5-flash", "gemini-2.5-pro", "glm-4.6",
    "gpt-5", "gpt-5-chat", "intern-s1", "kimi-k2-0905",
    "qwen3-235b-a22b-2507", "qwen3-235b-a22b-thinking-2507",
]
SOURCE = {"arenahard_coding": {"coding"}, "arenahard_math": {"math"},
          "arenahard_creative_writing": {"creative_writing"}}
TARGETS = {"gpqa": ("test", 198), "mmlupro": ("test_3000", 3000)}
FEATURES = [
    "char_count", "word_count", "line_count", "digit_count",
    "question_mark_count", "exclamation_count", "code_symbol_count",
    "contains_code_fence", "contains_url", "contains_equation_symbol",
    "contains_question_word",
]

def stop(msg): raise ValueError(msg)
def read_csv(p):
    with p.open(encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))
def read_jsonl(p):
    out=[]
    with p.open(encoding="utf-8") as f:
        for n,line in enumerate(f,1):
            if line.strip():
                try: x=json.loads(line)
                except Exception as e: stop(f"{p}:{n}: {e}")
                if not isinstance(x,dict): stop(f"{p}:{n}: expected object")
                out.append(x)
    return out
def query_of(r):
    x=r.get("origin_query")
    if not isinstance(x,str) or not x.strip(): x=r.get("prompt")
    if not isinstance(x,str) or not x.strip(): stop("Empty origin_query/prompt")
    return x
def features(s):
    return {
      "char_count":len(s),"word_count":len(re.findall(r"\b[\w']+\b",s)),
      "line_count":len(s.splitlines()),"digit_count":sum(c.isdigit() for c in s),
      "question_mark_count":s.count("?"),"exclamation_count":s.count("!"),
      "code_symbol_count":sum(s.count(c) for c in "{}[]();<>"),
      "contains_code_fence":int(chr(96)*3 in s),
      "contains_url":int(bool(re.search(r"https?://|www\.",s))),
      "contains_equation_symbol":int(bool(re.search(r"[=+\-*/^]",s))),
      "contains_question_word":int(bool(re.search(r"\b(what|why|how|when|where|which|who|explain|compare)\b",s,re.I))),
    }
def number(x,where):
    if isinstance(x,bool): stop(f"Boolean numeric value at {where}")
    try: v=float(x)
    except (TypeError,ValueError): stop(f"Missing/non-numeric {where}: {x!r}")
    if not math.isfinite(v): stop(f"Non-finite {where}")
    return v

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive",type=Path,default=ROOT/"bench-release.tar.gz")
    ap.add_argument("--metadata",type=Path,default=ROOT/"day1_audit/all_result_metadata.csv")
    ap.add_argument("--source-table",type=Path,default=ROOT/"day1_audit/prompt_feature_score_table.csv")
    ap.add_argument("--arena-jsonl",type=Path,default=ROOT/"repos/LLMRouterBench/data/ArenaHard/arena-hard-v2.jsonl")
    ap.add_argument("--output-dir",type=Path,default=ROOT/"day1_audit/avengerspro_transfer_seed42_split0.7")
    ap.add_argument("--seed",type=int,default=42)
    ap.add_argument("--train-ratio",type=float,default=.7)
    a=ap.parse_args()
    if not 0<a.train_ratio<1: stop("train ratio must be between 0 and 1")
    for p in (a.archive,a.metadata,a.source_table,a.arena_jsonl):
        if not p.is_file(): stop(f"Required file not found: {p}")
    meta=read_csv(a.metadata); table=read_csv(a.source_table)
    if not table: stop("Empty source score table")
    needed={"dataset","index","prompt_text_source",*FEATURES,*CANDIDATES}
    if needed-set(table[0]): stop(f"Source table missing columns: {sorted(needed-set(table[0]))}")
    table_by={}
    for r in table:
        k=(r["dataset"],str(r["index"]).strip())
        if k in table_by: stop(f"Duplicate source table key {k}")
        table_by[k]=r

    # Recheck the known positional ArenaHard mapping and feature agreement.
    arena=read_jsonl(a.arena_jsonl)
    if len(arena)!=750: stop(f"Expected 750 ArenaHard rows, got {len(arena)}")
    source_text={}
    counts={d:0 for d in SOURCE}
    for pos,r in enumerate(arena,1):
        sub=str(r.get("subcategory","")).strip().lower()
        ds=[d for d,subs in SOURCE.items() if sub in subs]
        if len(ds)!=1: stop(f"ArenaHard row {pos}: unknown subcategory {sub!r}")
        ds=ds[0]; counts[ds]+=1; k=(ds,str(pos))
        if k not in table_by: stop(f"Missing source table row {k}")
        q=query_of(r); got=features(q); expected=table_by[k]
        diffs=[f for f in FEATURES if int(float(expected[f]))!=got[f]]
        if diffs: stop(f"Feature mismatch {k}: {diffs}")
        source_text[k]=q
    if counts!={"arenahard_coding":253,"arenahard_math":247,"arenahard_creative_writing":250}:
        stop(f"Unexpected ArenaHard domain counts: {counts}")

    def select_meta(ds,split):
        rows=[r for r in meta if r["dataset"].strip().lower()==ds
              and r["split"].strip().lower()==split
              and r["demo"].strip().lower() in {"false","0"}
              and r["model"] in CANDIDATES]
        d={}
        for r in rows:
            if r["model"] in d: stop(f"Duplicate metadata {ds}/{r['model']}")
            d[r["model"]]=r
        if set(d)!=set(CANDIDATES):
            stop(f"{ds}/{split} candidate mismatch; missing {sorted(set(CANDIDATES)-set(d))}")
        return d

    def load_ds(tar,members,ds,split,expected_count=None):
        md=select_meta(ds,split); by={}
        for model in CANDIDATES:
            path=md[model]["archive_path"].strip().lstrip("./")
            member=members.get(path)
            if member is None: stop(f"Archive member missing: {path}")
            h=tar.extractfile(member)
            if h is None: stop(f"Cannot read {path}")
            payload=json.load(h)
            if not isinstance(payload,dict) or not isinstance(payload.get("records"),list):
                stop(f"Malformed archive payload {path}")
            seen=set()
            for rec in payload["records"]:
                idx=str(rec.get("index","")).strip()
                if not idx or idx in seen: stop(f"{ds}/{model}: blank/duplicate index {idx!r}")
                seen.add(idx); q=query_of(rec); score=number(rec.get("score"),f"{ds}/{model}/{idx}/score")
                item=by.setdefault(idx,{"queries":{},"records":{},"usages":{}})
                item["queries"][model]=q; item["records"][model]=score
                item["usages"][model]={
                    "completion_tokens":int(rec.get("completion_tokens") or 0),
                    "prompt_tokens":int(rec.get("prompt_tokens") or 0),
                    "cost":number(rec.get("cost") or 0,f"{ds}/{model}/{idx}/cost")}
        for idx,item in by.items():
            if set(item["records"])!=set(CANDIDATES): stop(f"{ds}/{idx}: incomplete model pool")
            if len(set(item["queries"].values()))!=1: stop(f"{ds}/{idx}: prompt mismatch across models")
            item["query"]=next(iter(item["queries"].values())); del item["queries"]
            item["records"]={m:item["records"][m] for m in CANDIDATES}
            item["usages"]={m:item["usages"][m] for m in CANDIDATES}
        if expected_count is not None and len(by)!=expected_count:
            stop(f"{ds}: expected {expected_count} prompts, got {len(by)}")
        return by

    rows=[]; notes=[]
    with tarfile.open(a.archive,"r:gz") as tar:
        members={m.name.strip().lstrip("./"):m for m in tar.getmembers() if m.isfile()}
        for ds in sorted(SOURCE):
            by=load_ds(tar,members,ds,"test")
            expected={idx for d,idx in table_by if d==ds}
            if set(by)!=expected: stop(f"{ds}: archive/table index mismatch")
            for idx,item in by.items():
                tab=table_by[(ds,idx)]
                if any(int(float(tab[f]))!=features(item["query"])[f] for f in FEATURES):
                    stop(f"{ds}/{idx}: archive query feature mismatch")
                for m in CANDIDATES:
                    if not math.isclose(item["records"][m],number(tab[m],f"table {ds}/{idx}/{m}"),rel_tol=0,abs_tol=1e-9):
                        stop(f"Archive/table score mismatch {ds}/{idx}/{m}")
                item.update(dataset=ds,index=int(idx)); rows.append(item)
            notes.append(f"{ds}: {len(by)} prompts; archive/table scores and 11 features agree")
        for ds,(split,n) in TARGETS.items():
            by=load_ds(tar,members,ds,split,n)
            for idx,item in by.items(): item.update(dataset=ds,index=int(idx)); rows.append(item)
            notes.append(f"{ds}: {len(by)} target prompts; 13 model records and prompt strings aligned")

    seen=set()
    for r in rows:
        k=(r["dataset"],r["query"])
        if k in seen: stop(f"Duplicate query in {r['dataset']}: index {r['index']}")
        seen.add(k)

    # Upstream split mechanics: per-dataset prompt shuffle, floor count,
    # one Python RNG stream; OOD datasets are held entirely for test.
    rng=random.Random(a.seed); train=[]; test=[]; split_counts={}
    for ds in sorted(SOURCE):
        group=sorted((r for r in rows if r["dataset"]==ds),key=lambda x:x["index"])
        order=list(range(len(group))); rng.shuffle(order)
        n=int(len(group)*a.train_ratio); train_ids=set(order[:n])
        for i,r in enumerate(group): (train if i in train_ids else test).append(r)
        split_counts[ds]=(n,len(group)-n)
    for ds in sorted(TARGETS): test.extend(r for r in rows if r["dataset"]==ds)
    train.sort(key=lambda x:(x["dataset"],x["index"]))
    test.sort(key=lambda x:(x["dataset"],x["index"]))
    a.output_dir.mkdir(parents=True,exist_ok=True)
    def write(path,data):
        with path.open("w",encoding="utf-8",newline="\n") as f:
            for r in data: f.write(json.dumps(r,ensure_ascii=False,separators=(",",":"))+"\n")
    train_p=a.output_dir/"train.jsonl"; test_p=a.output_dir/"test.jsonl"
    write(train_p,train); write(test_p,test)
    report=a.output_dir/"BUILD_REPORT.txt"
    with report.open("w",encoding="utf-8") as f:
        f.write("AVENGERS-PRO TRANSFER INPUT BUILD\n"+"="*40+"\n")
        f.write(f"seed={a.seed}; train_ratio={a.train_ratio}; candidates={len(CANDIDATES)}\n")
        f.write("query=origin_query when non-empty, otherwise prompt\n")
        f.write("Protocol deviation: upstream AvengersProAdaptor uses BaselineRecord.prompt; this adapter uses origin_query-first text to align with this study's feature extractor.\n")
        f.write("No embeddings, router fitting, or target-informed model selection performed.\n\n")
        f.write("\n".join(notes)+"\n\nSource train/test counts:\n")
        for ds,(tr,te) in split_counts.items(): f.write(f"{ds}: {tr}/{te}\n")
        f.write(f"\ntrain_rows={len(train)}; test_rows={len(test)}\n")
        f.write("OOD test-only: gpqa=198; mmlupro=3000\n")
        f.write("Source archive scores checked against the 13 selected columns in the audited table.\n")
        f.write("Source archive query feature vectors checked against all 11 stored features; exact string identity with original prompt is not asserted.\n")
        f.write(f"\ntrain={train_p}\ntest={test_p}\n")
    print("AVENGERS-PRO INPUT BUILD PASSED")
    print(f"Train: {len(train)}; test: {len(test)}")
    print(f"Source split counts: {split_counts}")
    print("OOD test-only: GPQA 198; MMLU-Pro 3000")
    print(f"Output: {a.output_dir}")
    return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except (OSError,ValueError,KeyError,tarfile.TarError) as e:
        print(f"BUILD BLOCKED: {e}",file=sys.stderr); raise SystemExit(1)
