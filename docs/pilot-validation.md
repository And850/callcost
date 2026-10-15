# Milestone 1 pilot validation

Date: 15 October 2026. Machine: Apple M1 Pro, 10 CPU cores, 16 GPU cores, 16 GiB RAM, macOS 27.0 build 26A428. LM Studio: 0.4.24+1. This is a functional validation, not the first full experiment or evidence for a quality/quantisation knee.

Used the already installed `lmstudio-community/Qwen3.5-9B-MLX-4bit`, with context length 4096, temperature 0, output cap 128 and `reasoning: "off"`. Only a held-out pencil-counting prompt was sent. No GSM8K problem or private summary was sent, and no weights were downloaded.

## Observed and retained

- The final successful pilot returned 38 input tokens, 68 visible output tokens and explicitly `reasoning_output_tokens: 0`. There were no reasoning events or `<think>` tags in the response, and the answer ended with `Answer: 12`.
- The [captured stream fixture](../tests/fixtures/lmstudio-0.4.24-mlx4bit.sse) preserves the response used to exercise the streaming parser. Its regression test checks the observed counts and thinking-off gate.
- Model loading was outside call timing. The load response echoed the requested context length and exposed other effective settings, including `parallel: 4`, which metadata preserves. CallCost still sent only one request at a time.
- Worker discovery identified the app, helpers and the bundled Node runtime executing `llmworker.js`. The final pilot retained 19 memory samples and reported process RSS. An earlier pilot correctly left memory unavailable when the worker was not recognised.
- The model was unloaded after each successful pilot. A follow-up model-list request confirmed no loaded instances remained.
- Two initial load attempts failed before inference because the native load API rejected the listed `@4bit` alias. The adapter now accepts that alias only when it is the selected variant, verifies its quantisation and sends the group key. Failed diagnostic runs remain in local run directories.

The local audit artifacts are `runs/installed-4bit-pilot-001` through `005`. The final successful call ID is `cbd75c084a064001865be44c2cb48111`. Full CSV, metadata, file hashes, raw control/inference responses and process samples remain there. They are ignored by Git; only the held-out, non-private protocol fixture is included in the repository.

## Not established

- Comfortable RAM headroom: the Mac already had substantial swap usage, and process RSS was below the roughly 6 GB installed weight-file size. RSS does not account for all GPU/unified memory. This pilot does not validate the fit of the future 8-bit variant.
- Four-level comparability: the matched conversions have not been produced, loaded or piloted. The installed 4-bit model is a functional fixture only.
- Gemini operation: no `GEMINI_API_KEY` was available to this process and no model/pricing configuration was selected. Its adapter has offline coverage only.
- Energy readings: `sudo -n` reported that a password was required. Installed powermetrics help confirmed the requested samplers and NUL-separated plist format, but actual privileged samples remain unverified.
- Quality or percentiles: pilot rows are excluded. No measured dataset run, blind review, p50/p95 table or knee analysis has been performed.
