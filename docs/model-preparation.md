# Qwen3.5-9B MLX preparation

Decision recorded on 15 October 2026: use Qwen3.5-9B, MLX at 3, 4, 6 and 8 bits, with thinking off. The owner selected reproducible conversion of all four levels from one pinned source after the published 3-bit candidate proved empty. The owner approved the source download and all four conversions on 15 October 2026. The 19,329,392,091-byte source download is complete. Every source shard matches its upstream LFS SHA-256. Converted outputs are pending the owner closing memory-heavy apps.

## Inspected published candidates

| Publisher and repository | Safetensors bytes | Status |
| --- | ---: | --- |
| [mlx-community/Qwen3.5-9B-3bit](https://huggingface.co/mlx-community/Qwen3.5-9B-3bit/tree/d86313135359a5b828cc54059e3e7f7883edeafc) | None | Only `.gitattributes`, not a usable model. |
| [mlx-community/Qwen3.5-9B-4bit](https://huggingface.co/mlx-community/Qwen3.5-9B-4bit/tree/8b2b98c00a6b4d291155e4890773ca8f769aee53) | 5,950,221,072 | Published weights. |
| [mlx-community/Qwen3.5-9B-6bit](https://huggingface.co/mlx-community/Qwen3.5-9B-6bit/tree/76fe4065e622cf34990d3c13ef80ec8531c9a0f7) | 8,188,406,421 | Published weights. |
| [mlx-community/Qwen3.5-9B-8bit](https://huggingface.co/mlx-community/Qwen3.5-9B-8bit/tree/16daa4818c54ce5f5436f929d52542eb65bbed9d) | 10,426,592,423 | Published weights. |

These file sizes are not runtime memory. The full pinned identities are retained in [model-candidates.json](model-candidates.json). Model-tree metadata for the 4/6/8 candidates names Qwen3.5-9B-Base, while their descriptive cards name Qwen3.5-9B. This does not establish which weights were converted and is another reason to retain our own source provenance.

## Approved preparation plan

The owner specified `mlx-lm` for all four conversions. This supersedes the earlier proposed mlx-vlm recipe. The experiment has five local configurations and a separate Gemini reference:

| Configuration | Role | Converter and group size |
| --- | --- | --- |
| Qwen3.5-9B MLX 3-bit, converted | Quantisation sequence | mlx-lm 0.32.0, affine, group size 64 |
| Qwen3.5-9B MLX 4-bit, converted | Quantisation sequence | mlx-lm 0.32.0, affine, group size 64 |
| Qwen3.5-9B MLX 6-bit, converted | Quantisation sequence | mlx-lm 0.32.0, affine, group size 64 |
| Qwen3.5-9B MLX 8-bit, converted | Quantisation sequence | mlx-lm 0.32.0, affine, group size 64 |
| Fairy's production model | Production reference, outside the knee sequence | Existing lmstudio-community MLX 4-bit model, affine, group size 64 |

Fairy's installed model is `lmstudio-community/Qwen3.5-9B-MLX-4bit`. Its card specifies [mlx-vlm conversion](https://huggingface.co/lmstudio-community/Qwen3.5-9B-MLX-4bit), and its config specifies affine quantisation with group size 64. `configs/example.yaml` includes that existing model as the fifth local configuration, labelled **Fairy's production model**, with `comparison_role: production_reference` and the existing weight/configuration/tokenizer paths. Run metadata and CSV retain the label and role. The model files and Fairy's code are read without modification.

The pinned [mlx-lm Qwen3.5 implementation](https://github.com/ml-explore/mlx-lm/blob/a9bd8af5c02118882af735cef60705d2efce9fd0/mlx_lm/models/qwen3_5.py) removes vision tensors. All four experimental variants therefore share a text-only conversion path. Fairy's production model retains vision support, so differences involving that fifth configuration can include converter/runtime and retained-architecture overhead as well as quantisation. It must not replace the converted 4-bit point in the knee calculation.

## Exact pins

- Source: [Qwen/Qwen3.5-9B at c202236235762e1c871ad0ccb60c8ee5ba337b9a](https://huggingface.co/Qwen/Qwen3.5-9B/tree/c202236235762e1c871ad0ccb60c8ee5ba337b9a), the official post-trained checkpoint.
- Source safetensors total: 19,306,310,880 bytes. Full repository payload is about 19.33 GB.
- Converter: **mlx-lm 0.32.0**, release commit [a9bd8af5c02118882af735cef60705d2efce9fd0](https://github.com/ml-explore/mlx-lm/tree/a9bd8af5c02118882af735cef60705d2efce9fd0).
- Resolved conversion environment: Python **3.13.2**, MLX **0.32.4**, mlx-metal **0.32.4**, plus every dependency pinned in [requirements-conversion.lock](../requirements-conversion.lock). This environment is separate from the benchmark environment.
- Common settings: `--q-group-size 64 --q-mode affine --dtype bfloat16`. No mixed-bit recipe, calibration dataset or remote-code trust is requested. Only requested bit count changes.
- Preserve model-specific exclusions and the resulting layer-level quantisation configuration. Some tensors remain unquantised; a nominal bit label does not imply every tensor uses it.

## Commands committed before downloading

Run from the repository root. These commands install the converter environment only:

```sh
python3.13 -m venv .venv-convert
.venv-convert/bin/python -m pip install -r requirements-conversion.lock
.venv-convert/bin/mlx_lm.convert --help
```

The environment and CLI help were verified before the approved weight download. The converter CLI does not expose a revision flag, so download the exact revision to a local directory first, then convert with Hub access disabled. This avoids accidentally resolving `main` during conversion.

The exact source download command is in [download_qwen_source.sh](../scripts/download_qwen_source.sh). It checks at least 45 GB free before downloading and writes a SHA-256 manifest of the local source. **Owner confirmation was received on 15 October 2026**, authorising the download and four conversions.

```sh
bash scripts/download_qwen_source.sh
```

The four explicit conversion commands are in [convert_qwen_mlx.sh](../scripts/convert_qwen_mlx.sh). Each launches a separate process against the same original source, with group size 64. They never requantise a lower-precision variant. The script verifies the exact source file set, sizes and SHA-256 hashes against the download manifest, rejects existing outputs, disables Hub access, records the Python/dependency versions and command copy, preserves logs and licences, and hashes all output files.

```sh
bash scripts/convert_qwen_mlx.sh
```

Conversion has not been executed, so memory feasibility, output sizes, layer settings and LM Studio compatibility remain unverified. The 19.31 GB source weights exceed this Mac's 16 GiB physical RAM; lazy loading is used by the converter, but that does not establish a safe peak working set.

## Disk check

On 15 October 2026, the repository/model target filesystem and existing Hugging Face cache filesystem were the same APFS data volume. After installing the conversion environment, the target had **192.78 GB available**. This exceeds the approximately **45 GB** planning allowance for one source download plus four converted outputs. The download script repeats the check because available space can change. No source directory or converted weights existed at this check.

## Validation before the experiment

Inspect all output layer settings for the requested bit counts and common group size, and compare tokenizer/template hashes across the four conversions. Import all four into LM Studio, record exact variant keys and runtime versions, and verify each requested thinking-off setting in a held-out pilot. A missing reasoning-token count is not zero.

Start with the highest precision to inspect available RAM, swap growth and model/runtime RSS under the intended context length and output budget. The published multimodal 8-bit candidate's 10.43 GB file size does not predict the new text-only output or establish comfortable RAM headroom. Conversion feasibility and runtime headroom are separate checks. Resolve substantial memory pressure before collecting full-run results.

The installed production reference passed functional thinking-off and RSS collection pilots. Those pilot rows are excluded from the experimental dataset. See [pilot validation](pilot-validation.md).

## Conversion memory monitoring

Before download the Mac had about 2.6 GB available RAM, 12.7 GB swap usage and substantial compression. The owner was asked to close memory-heavy apps before conversion. Download and metadata preparation can continue while waiting.

Run the committed conversion commands through the preparation monitor:

```sh
.venv/bin/python scripts/monitor_conversion.py \
  --output models/provenance/conversion-memory-001.jsonl \
  -- bash scripts/convert_qwen_mlx.sh
```

The monitor samples process-tree RSS, available system memory and swap every two seconds, and keeps process IDs and each active converter output path. This is preparation telemetry, not a benchmark result. As a guard against sustained thrashing, it terminates only its own conversion process group if available memory stays below 512 MiB while swap has grown by more than 4 GiB for at least ten seconds. This operational cutoff does not change experiment scoring or knee definitions. Failed partial outputs and logs must be retained under a separate attempt path before any retry.

## Fairy production vision-weight footprint

A header-only inspection of the installed safetensors found **912,020,960 encoded bytes** of `vision_tower.*` tensors, including their scales and biases. Total tensor payload is **5,950,062,560 bytes**; vision therefore accounts for **15.3279%** of that payload. Language tensors account for 5,038,041,600 bytes. Safetensors file size, including headers, is 5,950,221,142 bytes.

The [component report](data/fairy-production-weight-components.json) retains per-file counts and method. Run metadata records the same component breakdown for every local configuration. This measures encoded weight storage, not the resident/allocated memory attributable to vision. Do not subtract 912 MB from process RSS or infer a vision-only load duration. Fairy's RSS and load time include its original vision-capable architecture, runtime and file-cache state; comparisons to the text-only series carry that caveat.


## Source download completed

Downloaded **19,329,392,091 bytes** of non-cache source files at the pinned revision. All four safetensors shards match their published upstream LFS SHA-256 hashes. The [source manifest](data/qwen35-source-manifest.json) preserves file sizes, hashes and verification results. No conversion has started while the apps-closed confirmation is pending.

## Fairy reference memory and load observation

The last successful functional pilot on 15 October 2026 provides one excluded observation, not an experimental percentile:

| Configuration | Load request wall time | Provider load time | Sampled LM Studio RSS peak | Encoded vision weights |
| --- | ---: | ---: | ---: | ---: |
| Fairy's production model, vision retained | 9.1169 s | 9.101 s | 1,777,991,680 bytes | 912,020,960 bytes |

The [pilot record](data/fairy-production-pilot.json) contains the full-precision observations, model-file hashes, conditions and original call/run identity. This pilot ran on battery with substantial pre-existing swap. File-cache state was not controlled. Its RSS excludes some GPU/unified-memory allocations and is smaller than its weight files, so it cannot establish total model memory or a vision-only runtime cost. Its load time and memory must not be attributed solely to quantisation when compared with the new text-only series. The full experiment still requires its own matched-condition observations.
