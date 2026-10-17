"""Offline blinded checklist packet and strict score import. No model calls."""

import argparse
import hashlib
import json
import random
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from callcost.report import score_answer


def digest(answer):
    return hashlib.sha256(answer.encode()).hexdigest()


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def prepare(runs, output):
    groups, prompts = {}, {}
    for run in runs:
        run = run.resolve()
        meta = json.loads((run / 'metadata.json').read_text())
        if meta['status'] != 'completed':
            raise ValueError('All source runs must be complete before review')
        for p in meta['dataset']['prompts']:
            if p['task_type'] == 'summarisation':
                if p['id'] in prompts and prompts[p['id']] != p:
                    raise ValueError('Prompt/rubric differs across source runs')
                prompts[p['id']] = p
        for f in sorted((run / 'checkpoints').glob('*.json')):
            row = json.loads(f.read_text())
            if row['phase'] != 'measured' or row['status'] != 'completed' or row['prompt_id'] not in prompts:
                continue
            key = (row['prompt_id'], row['answer'])
            groups.setdefault(key, []).append(dict(run=str(run), call_id=row['call_id'],
                                                  answer_sha256=digest(row['answer']), prompt_id=row['prompt_id']))
    if not groups:
        raise ValueError('No completed summary answers')
    items, mapping = [], {}
    for (pid, answer), calls in groups.items():
        anon = uuid.uuid4().hex
        mapping[anon] = calls
        p = prompts[pid]
        automatic = score_answer(p, answer)['checks']
        items.append(dict(id=anon, automatic={k: v for k, v in automatic.items() if v is not None}, prompt='\n\n'.join(str(p[k]) for k in ('prompt', 'input') if p.get(k)),
                          answer=answer, checklist=[dict(id=x['id'], description=x['description']) for x in p['scoring']['items']]))
    random.SystemRandom().shuffle(items)
    packet = dict(packet_id=uuid.uuid4().hex, items=items)
    output.mkdir(parents=True, exist_ok=False)
    write(output / 'packet.json', packet)
    write(output / 'key.json', dict(packet_id=packet['packet_id'], mapping=mapping))
    # Escaping '<' prevents model output from terminating the inert JSON script block.
    embedded = json.dumps(packet, ensure_ascii=False).replace('<', '\\u003c')
    (output / 'review.html').write_text(HTML.replace('PACKET_DATA', embedded))
    print(f'Prepared {len(items)} unique prompt/answer pairs from {sum(map(len, mapping.values()))} calls.')


def import_scores(review, scores_path):
    packet = json.loads((review / 'packet.json').read_text())
    key = json.loads((review / 'key.json').read_text())
    scores = json.loads(scores_path.read_text())
    if scores.get('packet_id') != packet['packet_id'] or key['packet_id'] != packet['packet_id']:
        raise ValueError('Packet identity mismatch')
    if not isinstance(scores.get('reviewer'), str) or not scores['reviewer'].strip():
        raise ValueError('Reviewer name required')
    if set(scores.get('scores', {})) != {x['id'] for x in packet['items']}:
        raise ValueError('Every review item must be scored exactly once')
    ids = [x['id'] for x in packet['items']]
    if len(ids) != len(set(ids)) or set(key['mapping']) != set(ids):
        raise ValueError('Review item mapping must be unique and complete')
    by_run = defaultdict(dict)
    for item in packet['items']:
        checks = scores['scores'][item['id']]
        if set(checks) != {x['id'] for x in item['checklist']} or not all(type(v) is bool for v in checks.values()):
            raise ValueError('Each checklist criterion requires a boolean decision')
        if any(checks.get(k) != v for k, v in item['automatic'].items()):
            raise ValueError('Automatic criteria must retain the frozen automatic rule results')
        for identity in key['mapping'][item['id']]:
            run = Path(identity['run'])
            found = [json.loads(p.read_text()) for p in (run / 'checkpoints').glob('*.json')]
            row = next((r for r in found if r['call_id'] == identity['call_id']), None)
            if row is None or row['status'] != 'completed' or row['phase'] != 'measured' or digest(row['answer']) != identity['answer_sha256'] or row['answer'] != item['answer'] or row['prompt_id'] != identity['prompt_id']:
                raise ValueError('Saved answer identity changed')
            meta = json.loads((run / 'metadata.json').read_text())
            prompt = next(p for p in meta['dataset']['prompts'] if p['id'] == row['prompt_id'])
            source = '\n\n'.join(str(prompt[k]) for k in ('prompt', 'input') if prompt.get(k))
            rubric = [dict(id=x['id'], description=x['description']) for x in prompt['scoring']['items']]
            automatic = {k: v for k, v in score_answer(prompt, row['answer'])['checks'].items() if v is not None}
            if item['prompt'] != source or item['checklist'] != rubric or item['automatic'] != automatic:
                raise ValueError('Saved answer identity changed')
            if row['call_id'] in by_run[run]:
                raise ValueError('A call cannot receive multiple blind scores')
            by_run[run][row['call_id']] = dict(checks=checks, answer_sha256=identity['answer_sha256'], prompt_id=identity['prompt_id'])
    # Validate every packet/answer before writing any run's review file.
    for run, calls in by_run.items():
        target = run / 'human_scores.json'
        if target.exists():
            raise ValueError('Human scores already exist; preserve prior review before importing again')
    for run, calls in by_run.items():
        write(run / 'human_scores.json', dict(packet_id=packet['packet_id'], reviewer=scores['reviewer'],
              reviewed_at=datetime.now(timezone.utc).isoformat(), calls=calls))
    print(f'Imported human checks for {sum(map(len, by_run.values()))} calls. Regenerate saved-run reports.')


HTML = '''<!doctype html><meta charset="utf-8"><title>Blind summary review</title>
<style>body{font:17px system-ui;max-width:900px;margin:30px auto;padding:20px}pre{white-space:pre-wrap;background:#f3f4f6;padding:18px}label{display:block;padding:10px;border-bottom:1px solid #ddd}button,select,input{font:inherit;margin:8px;padding:8px}header{position:sticky;top:0;background:white;padding:8px}#notice{color:#444}</style>
<header><b>Blind summary review</b><div id="progress"></div><button id="prev">Previous</button><button id="next">Next</button><button id="export">Export completed scores</button></header>
<p>Read the source and answer. Automatic criteria are prefilled and fixed by the registered rules. Mark each remaining criterion Pass or Fail. Identical answers for the same prompt are reviewed once and mapped back to all repeats. Configuration, timing and identity mapping are hidden. Scores stay in this browser; export a backup when finished. Do not inspect key.json until review is complete.</p>
<label>Reviewer name <input id="reviewer"></label><p id="notice"></p><h2>Source and instruction</h2><pre id="source"></pre><h2>Answer</h2><pre id="answer"></pre><h2>Checklist</h2><div id="checks"></div>
<script type="application/json" id="packet">PACKET_DATA</script>
<script>
const packet=JSON.parse(document.getElementById('packet').textContent), storage='callcost-review-'+packet.packet_id;
let saved={scores:{},reviewer:'',index:0};try{saved=JSON.parse(localStorage.getItem(storage))||saved}catch(e){}
for(const item of packet.items){saved.scores[item.id]??={};Object.assign(saved.scores[item.id],item.automatic)}
let index=Math.max(0,Math.min(saved.index||0,packet.items.length-1)); const el=id=>document.getElementById(id);
el('reviewer').value=saved.reviewer;function persist(){saved.index=index;saved.reviewer=el('reviewer').value;try{localStorage.setItem(storage,JSON.stringify(saved));el('notice').textContent='Progress saved in this browser.'}catch(e){el('notice').textContent='Browser storage unavailable. Keep this tab open until export.'}}
function render(){const item=packet.items[index];el('progress').textContent=(index+1)+' / '+packet.items.length;el('source').textContent=item.prompt;el('answer').textContent=item.answer;el('checks').replaceChildren();for(const check of item.checklist){const label=document.createElement('label');label.textContent=check.description+' ';const select=document.createElement('select');for(const [v,t] of [['','Choose'],['true','Pass'],['false','Fail']]){const option=document.createElement('option');option.value=v;option.textContent=t;select.append(option)}const value=saved.scores[item.id]?.[check.id];select.value=value===undefined?'':String(value);select.disabled=Object.hasOwn(item.automatic,check.id);select.onchange=()=>{saved.scores[item.id]??={};if(select.value==='')delete saved.scores[item.id][check.id];else saved.scores[item.id][check.id]=select.value==='true';persist()};label.append(select);el('checks').append(label)}}
el('reviewer').oninput=persist;el('prev').onclick=()=>{index=Math.max(0,index-1);persist();render()};el('next').onclick=()=>{index=Math.min(packet.items.length-1,index+1);persist();render()};el('export').onclick=()=>{persist();if(!saved.reviewer.trim()||packet.items.some(x=>x.checklist.some(c=>typeof saved.scores[x.id]?.[c.id]!=='boolean'))){alert('Enter your name and score every checklist item before exporting.');return}const blob=new Blob([JSON.stringify({packet_id:packet.packet_id,reviewer:saved.reviewer,scores:saved.scores},null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='summary-scores.json';a.click();URL.revokeObjectURL(a.href)};render();
</script>'''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--runs', nargs='+', type=Path, required=True)
    prep.add_argument('--output', type=Path, required=True)
    imp = sub.add_parser('import')
    imp.add_argument('--review', type=Path, required=True)
    imp.add_argument('--scores', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.runs, args.output)
    else:
        import_scores(args.review, args.scores)
