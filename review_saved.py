"""Review selected saved development outputs without replacing their benchmark results."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import quality
from models import Brief

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--cases',required=True,help='Comma-separated development case IDs')
    args=parser.parse_args()
    chosen=set(args.cases.split(','))
    cases={c['id']:c for c in json.loads((args.run/'cases.json').read_text())}
    if not chosen <= cases.keys() or any(cases[i]['split']!='development' for i in chosen):
        parser.error('Select only development cases available in the saved run')
    rows=[json.loads(s) for s in (args.run/'results.jsonl').read_text().splitlines()]
    dest=Path(__file__).resolve().parent/'evaluation/reviews'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    dest.mkdir(parents=True)
    (dest/'metadata.json').write_text(json.dumps(dict(source_run=str(args.run),case_ids=sorted(chosen),
        review_version=quality.REVIEW_VERSION,quality_sha256=hashlib.sha256(Path(quality.__file__).read_bytes()).hexdigest()),indent=2))
    for row in rows:
        if row['case_id'] not in chosen or row['status']!='valid':continue
        start=time.perf_counter()
        result=dict(case_id=row['case_id'],review=quality.review_assessment(Brief.model_validate(cases[row['case_id']]['brief']),row['assessment']))
        result['elapsed_seconds']=round(time.perf_counter()-start,4)
        with (dest/'results.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(result)+'\n')
        print(result['case_id'],result['review']['status'],flush=True)
    print('Review results:',dest,flush=True)

if __name__=='__main__':main()
