"""Export aggregate saved results and draw static quality-versus-latency figures. No inference."""

import argparse
import hashlib
import json
import math
from pathlib import Path

SEQUENCE = ['local-q8', 'local-q6', 'local-q4', 'local-q3']
ORDER = SEQUENCE + ['fairy-production', 'cloud']


def load_chart_data(local, cloud):
    tasks = {}
    sources = []
    for directory in (local, cloud):
        report_path = directory / 'report.json'
        report = json.loads(report_path.read_text())
        metadata = json.loads((directory / 'metadata.json').read_text())
        if not report['collection']['complete']:
            raise ValueError('Charts require complete saved collections')
        sources.append(dict(run=directory.name, report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest()))
        config = {c['id']: c for c in metadata['config']['configurations']}
        for task in ('maths', 'summarisation'):
            prompts = sum(p['task_type'] == task for p in metadata['dataset']['prompts'])
            repeats = metadata['config']['run']['repeats']
            dataset = tasks.setdefault(task, dict(unique_prompts=prompts, repeats=repeats,
                                                  calls_per_configuration=prompts * repeats, points=[]))
            if (dataset['unique_prompts'], dataset['repeats']) != (prompts, repeats):
                raise ValueError('Task sizes/repeats differ across passes')
            groups = [g for g in report['groups'] if g['task_type'] == task and g['cache_stratum'] == 'all']
            for g in groups:
                setting = config[g['configuration_id']]
                quality, latency = g['quality'], g['latency_s']
                if quality['score'] is None or g['calls'] != prompts * repeats or latency['n'] != g['calls']:
                    raise ValueError('Primary quality or complete latency samples unavailable')
                if not all(math.isfinite(x) for x in (quality['score'], latency['p50'], latency['p95'])):
                    raise ValueError('Nonfinite chart observation')
                if not (0 <= quality['score'] <= 1 and 0 <= latency['p50'] <= latency['p95']):
                    raise ValueError('Invalid quality/latency bounds')
                dataset['points'].append(dict(configuration_id=g['configuration_id'],
                    comparison_role=setting.get('comparison_role', 'cloud_reference'),
                    quality=quality['score'], quality_fraction=quality.get('score_fraction'),
                    quality_without_max_words=(g.get('quality_without_max_words') or {}).get('score') if task == 'summarisation' else None,
                    latency_p50_s=latency['p50'], latency_p95_s=latency['p95'], calls=g['calls'],
                    swap_free_latency_p50_s=g['swap_free_latency_s']['p50'],
                    swap_free_latency_p95_s=g['swap_free_latency_s']['p95'],
                    swap_free_calls=g['swap_free_latency_s']['n']))
    for task in tasks.values():
        if sorted(p['configuration_id'] for p in task['points']) != sorted(ORDER):
            raise ValueError('Expected exactly four precision levels, Fairy and cloud')
        task['points'].sort(key=lambda p: ORDER.index(p['configuration_id']))
    return dict(schema_version=1, collection_dates='2026-10-16 to 2026-10-17', sources=sources,
                cost_metric='All-completed-call client latency, including swap-active calls; p50 points and p50-to-p95 whiskers',
                quality='Primary registered score: mean repeats within prompt, then equal prompt weights. Summary includes max_words.',
                precision_order=SEQUENCE, tasks=tasks)


def draw(task, data, output):
    from reportlab.graphics import renderPDF, renderSVG
    from reportlab.graphics.charts.lineplots import LinePlot
    from reportlab.graphics.shapes import (
        Circle,
        Drawing,
        Group,
        Line,
        Polygon,
        Rect,
        String,
    )
    from reportlab.lib.colors import HexColor, white
    from reportlab.pdfbase.pdfmetrics import stringWidth

    is_maths = task == 'maths'
    width, height = 920, 640
    left, bottom, plot_width, plot_height = 90, 190, 740, 320
    maximum = 36 if is_maths else 11
    minimum_quality = 50 if is_maths else 75
    points = {p['configuration_id']: p for p in data['points']}
    color = {'local-q8': '#1D4ED8', 'local-q6': '#0F766E', 'local-q4': '#0891B2',
             'local-q3': '#375A7F', 'fairy-production': '#7B4AB0', 'cloud': '#B45309'}
    drawing = Drawing(width, height)
    drawing.add(Rect(0, 0, width, height, fillColor=white, strokeColor=None))
    title = 'Maths: quality versus latency' if is_maths else 'Summaries: quality versus latency'
    drawing.add(String(55, 598, title, fontName='Helvetica-Bold', fontSize=22, fillColor=HexColor('#172033')))
    drawing.add(String(55, 574, 'Qwen3.5-9B precision series and separate reference configurations', fontName='Helvetica', fontSize=12))
    legend = [(70, '#1D4ED8', '8 -> 6 -> 4 -> 3 bit'), (330, '#7B4AB0', 'Fairy production (4-bit)'), (605, '#B45309', 'Gemini 3.8 Flash reference')]
    for x, c, label in legend:
        if x == 70:
            drawing.add(Line(x, 548, x+24, 548, strokeColor=HexColor(c), strokeWidth=2))
            drawing.add(Circle(x+12, 548, 3.5, fillColor=HexColor(c), strokeColor=white))
        elif x == 330:
            drawing.add(Rect(x+7, 544, 8, 8, fillColor=HexColor(c), strokeColor=white))
        else:
            drawing.add(Polygon([x+11,553,x+16,548,x+11,543,x+6,548], fillColor=HexColor(c), strokeColor=white))
        drawing.add(String(x+32, 544, label, fontName='Helvetica', fontSize=11))
    chart = LinePlot()
    chart.x, chart.y, chart.width, chart.height = left, bottom, plot_width, plot_height
    chart.data = [[(points[c]['latency_p50_s'], 100*points[c]['quality']) for c in SEQUENCE]]
    chart.lines[0].strokeColor = HexColor('#1D4ED8')
    chart.lines[0].strokeWidth = 2.2
    chart.xValueAxis.valueMin, chart.xValueAxis.valueMax = 0, maximum
    chart.xValueAxis.valueSteps = list(range(0, maximum+1, 5 if is_maths else 2))
    chart.yValueAxis.valueMin, chart.yValueAxis.valueMax = minimum_quality, 100
    chart.yValueAxis.valueSteps = list(range(minimum_quality, 101, 10 if is_maths else 5))
    for axis in (chart.xValueAxis, chart.yValueAxis):
        axis.labels.fontName = 'Helvetica'
        axis.labels.fontSize = 11
        axis.strokeColor = HexColor('#64748B')
        axis.gridStrokeColor = HexColor('#E2E8F0')
        axis.visibleGrid = True
    def coords(x, y):
        return left + x/maximum*plot_width, bottom + (y-minimum_quality)/(100-minimum_quality)*plot_height
    # Whiskers are latency percentiles at the task-level quality score, not quality error bars.
    for cid in ORDER:
        p = points[cid]
        x, y = coords(p['latency_p50_s'], 100*p['quality'])
        end, _ = coords(p['latency_p95_s'], 100*p['quality'])
        drawing.add(Line(x, y, end, y, strokeColor=HexColor(color[cid]), strokeWidth=1.2))
        drawing.add(Line(end, y-4, end, y+4, strokeColor=HexColor(color[cid]), strokeWidth=1.2))
    drawing.add(chart)
    offsets = ({'local-q8':(10,-20), 'local-q6':(10,13), 'local-q4':(-48,-22),
                'local-q3':(10,-19), 'fairy-production':(-86,12), 'cloud':(10,14)} if is_maths else
               {'local-q8':(12,15), 'local-q6':(16,-20), 'local-q4':(-65,-24),
                'local-q3':(12,-22), 'fairy-production':(-103,25), 'cloud':(-22,20)})
    for cid in ORDER:
        p = points[cid]
        x, y = coords(p['latency_p50_s'], 100*p['quality'])
        c = HexColor(color[cid])
        if cid == 'fairy-production':
            drawing.add(Rect(x-5, y-5, 10, 10, fillColor=c, strokeColor=white, strokeWidth=1))
            text = 'Fairy ref.'
        elif cid == 'cloud':
            drawing.add(Polygon([x,y+6,x+6,y,x,y-6,x-6,y], fillColor=c, strokeColor=white, strokeWidth=1))
            text = 'Cloud ref.'
        else:
            drawing.add(Circle(x, y, 4.5, fillColor=c, strokeColor=white, strokeWidth=1))
            text = cid.removeprefix('local-q')+'-bit'
        dx, dy = offsets[cid]
        tx, ty = x+dx, y+dy
        edge = tx-3 if dx >= 0 else tx+stringWidth(text,'Helvetica-Bold',11)+3
        drawing.add(Line(x, y, edge, ty+3, strokeColor=HexColor('#94A3B8'), strokeWidth=.6))
        drawing.add(String(tx, ty, text, fontName='Helvetica-Bold', fontSize=11, fillColor=c))
    drawing.add(String(460, 143, 'All-call latency (seconds; median points, p50-to-p95 whiskers)', fontName='Helvetica', fontSize=12, textAnchor='middle'))
    label = 'Maths accuracy (%)' if is_maths else 'Primary human-checklist score (%)'
    axis_label = Group(String(0, 0, label, fontName='Helvetica', fontSize=12, textAnchor='middle'))
    axis_label.transform = (0, 1, -1, 0, 28, 350)
    drawing.add(axis_label)
    sample = f'{data["unique_prompts"]} '+('GSM8K problems' if is_maths else 'invented-text summaries')+f' x {data["repeats"]} repeats = {data["calls_per_configuration"]} measured calls per configuration.'
    captions = [sample,
        'Quality averages repeats within each prompt, then weights prompts equally; repeats are not independent prompts.',
        f'Whiskers show latency spread, not confidence intervals. Quality axis is zoomed to {minimum_quality}-100%.',
        'All completed calls are included, including swapping. References are outside the registered knee sequence.',
        'Local thinking: off. Cloud thinking: low; successful-attempt latency excludes retries and backoff.']
    if not is_maths:
        captions.insert(1, 'One blinded human checklist review; original max_words included. Sensitivity scores are separate.')
    for i, text in enumerate(captions):
        drawing.add(String(55, 111-16*i, text, fontName='Helvetica', fontSize=10, fillColor=HexColor('#475569')))
    output.mkdir(parents=True, exist_ok=True)
    stem = output / f'quality-cost-{task}'
    renderSVG.drawToFile(drawing, str(stem.with_suffix('.svg')))
    renderPDF.drawToFile(drawing, str(stem.with_suffix('.pdf')), title=title, author='CallCost')
    print(stem)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local-run', type=Path)
    parser.add_argument('--cloud-run', type=Path)
    parser.add_argument('--data', type=Path, required=True, help='Aggregate JSON, written with --local-run/--cloud-run; otherwise read')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--export-only', action='store_true')
    args = parser.parse_args()
    if args.local_run or args.cloud_run:
        if not (args.local_run and args.cloud_run):
            parser.error('Both source runs required')
        data = load_chart_data(args.local_run, args.cloud_run)
        args.data.parent.mkdir(parents=True, exist_ok=True)
        args.data.write_text(json.dumps(data, indent=2)+'\n')
    else:
        data = json.loads(args.data.read_text())
    if not args.export_only:
        for task, values in data['tasks'].items():
            draw(task, values, args.output)
