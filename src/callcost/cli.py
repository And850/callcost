"""Small CLI: validate inputs, inspect installed models, run experiments."""

import argparse
import json
import os
import sys
from pathlib import Path

import httpx

from callcost.experiment import file_identity, run_experiment
from callcost.schemas import Config, Dataset, LMStudioSettings, load_document


def main(argv=None):
    parser = argparse.ArgumentParser(prog='callcost')
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('validate', 'run'):
        sub = commands.add_parser(name)
        sub.add_argument('--prompts', type=Path, required=True)
        sub.add_argument('--config', type=Path, required=True)
        if name == 'run':
            sub.add_argument('--output', type=Path, required=True, help='New directory; never overwritten')
            sub.add_argument('--pilot-only', action='store_true', help='One excluded thinking-off pilot per configuration')
    models = commands.add_parser('models', help='Read installed models without loading them')
    models.add_argument('--base-url', default='http://127.0.0.1:1234')
    models.add_argument('--api-key-env')
    args = parser.parse_args(argv)
    try:
        if args.command == 'models':
            settings = LMStudioSettings(base_url=args.base_url, api_key_env=args.api_key_env)
            key = os.environ.get(settings.api_key_env) if settings.api_key_env else None
            if settings.api_key_env and not key:
                raise ValueError('Missing LM Studio credential environment variable')
            with httpx.Client(trust_env=False) as client:
                response = client.get(settings.base_url + '/api/v1/models', timeout=10,
                                      headers={'Authorization': f'Bearer {key}'} if key else {})
                response.raise_for_status()
                print(json.dumps(response.json(), indent=2))
            return 0
        config = Config.model_validate(load_document(args.config))
        dataset = Dataset.model_validate(load_document(args.prompts))
        # Relative model files are relative to config, independent of invocation directory.
        for setting in config.configurations:
            if setting.provider == 'lmstudio':
                setting.model_files = [(args.config.resolve().parent / p.expanduser()).resolve()
                                       for p in setting.model_files]
        if args.command == 'validate':
            print(f'Valid: {len(config.configurations)} configurations, {len(dataset.prompts)} prompts, '
                  f'{config.run.repeats} measured repeats. Files and provider access are checked at run time.')
            return 0
        meta = run_experiment(config, dataset, args.output, pilot_only=args.pilot_only,
                              input_files=[file_identity(args.config), file_identity(args.prompts)])
        print(f'Run {meta["status"]}: {meta["completed_measured_calls"]} completed measured calls; {args.output.resolve()}')
        if not args.pilot_only:
            for row in meta['variation']['summary']:
                print(f'{row["configuration_id"]} / {row["task_type"]}: '
                      f'{row["varying_prompts"]}/{row["compared_prompts"]} compared prompts varied; '
                      f'{row["incomplete_prompts"]} incomplete; {row["uncomparable_prompts"]} uncomparable')
        for error in meta['errors']:
            print(error, file=sys.stderr)
        return 0 if meta['status'] == 'completed' else 1
    except (ValueError, OSError, httpx.HTTPError) as error:
        print(f'callcost: {error if isinstance(error, (ValueError, OSError)) else type(error).__name__}', file=sys.stderr)
        return 1
