"""Exact text variation, with missing repeats kept visible."""

import hashlib
from collections import defaultdict


def answer_hash(answer):
    return hashlib.sha256(answer.encode('utf-8')).hexdigest()


def variation_report(config, dataset, rows):
    groups = []
    summaries = defaultdict(lambda: dict(varying_prompts=0, compared_prompts=0,
                                         incomplete_prompts=0, uncomparable_prompts=0))
    for configuration in config.configurations:
        for prompt in dataset.prompts:
            calls = [r for r in rows if r['phase'] == 'measured'
                     and r['configuration_id'] == configuration.id and r['prompt_id'] == prompt.id
                     and r['status'] == 'completed']
            distinct = {r['answer_sha256'] for r in calls}
            compared = len(calls) >= 2
            varying = compared and len(distinct) > 1
            incomplete = len(calls) != config.run.repeats
            groups.append({'configuration_id': configuration.id, 'prompt_id': prompt.id,
                           'task_type': prompt.task_type, 'completed_calls': len(calls),
                           'distinct_answers': len(distinct), 'compared': compared,
                           'varying': varying, 'incomplete': incomplete,
                           'call_ids': [r['call_id'] for r in calls]})
            summary = summaries[(configuration.id, prompt.task_type)]
            summary['varying_prompts'] += int(varying)
            summary['compared_prompts'] += int(compared)
            summary['incomplete_prompts'] += int(incomplete)
            summary['uncomparable_prompts'] += int(not compared)
    return {'groups': groups, 'summary': [dict(configuration_id=c, task_type=t, **s)
                                        for (c, t), s in summaries.items()]}
