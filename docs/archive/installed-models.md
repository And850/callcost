# Installed model inventory

Observed on 15 October 2026 by reading model files from the default LM Studio model directory. The REST server at localhost port 1234 was unavailable, and `lms ls --llm --variants --json` timed out while attempting to contact its service. These are filesystem observations, not confirmed REST model identifiers.

| Model directory | Variant observed | Weight-file size |
| --- | --- | --- |
| lmstudio-community/Qwen2.5-Coder-7B-Instruct-GGUF | Q4_K_M | 4.361 GiB |
| lmstudio-community/Qwen2.5-VL-7B-Instruct-GGUF | Q4_K_M | 4.361 GiB plus a 1.261 GiB vision projector |
| lmstudio-community/Qwen3.5-9B-MLX-4bit | MLX affine 4-bit, group size 64 | 5.541 GiB across two shards |
| mlx-community/gpt-oss-20b-MXFP4-Q8 | Mixed MXFP4 and 8-bit overrides | 11.247 GiB across three shards |

No installed family currently supplies three or four comparable quantisations. File size is not loaded-process memory and does not prove comfortable operation alongside macOS and collectors.

The model family remains unselected. The first experiment should use one base checkpoint and one engine, likely a 7B to 9B model, with the highest tested precision verified to leave memory headroom on the 16 GB Mac. No model was downloaded or loaded for this inventory.

The previously detected machine is an Apple M1 Pro with ten CPU cores, sixteen GPU cores and 16 GB RAM, running macOS 27.0. The installed LM Studio application reported version 0.4.24+1. Every benchmark run must detect these conditions again rather than reuse this note.
