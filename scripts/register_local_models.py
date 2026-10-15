"""Register the four prepared models and local thinking-control definitions in LM Studio."""

import os
import shutil
from pathlib import Path


def main():
    plans = []
    for bits in (3, 4, 6, 8):
        source = Path(f'models/converted/Qwen3.5-9B-{bits}bit').resolve(strict=True)
        wrapper = Path(f'configs/lmstudio-models/{bits}bit').resolve(strict=True)
        installed = Path.home() / '.cache/lm-studio/models/And850' / f'callcost-qwen35-9b-{bits}bit-mlx-text'
        control = Path.home() / '.cache/lm-studio/hub/models/local' / f'callcost-qwen35-9b-text-{bits}bit'
        if installed.exists() or control.exists():
            raise SystemExit(f'Existing local registration for {bits} bits; refusing overwrite')
        if not (source / 'config.json').is_file() or not list(source.glob('*.safetensors')):
            raise SystemExit(f'Incomplete converted output: {source}')
        if not (wrapper / 'model.yaml').is_file() or not (wrapper / 'manifest.json').is_file():
            raise SystemExit(f'Incomplete local model definition: {wrapper}')
        plans.append((source, wrapper, installed, control))
    for source, wrapper, installed, control in plans:
        installed.mkdir(parents=True)
        for file in source.iterdir():
            if not file.is_file():
                continue
            if file.suffix == '.safetensors':
                os.link(file, installed / file.name)
            else:
                shutil.copy2(file, installed / file.name)
        control.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(wrapper, control)
        print(f'Registered {installed.name}; allow the model index to refresh before listing')


if __name__ == '__main__':
    main()
