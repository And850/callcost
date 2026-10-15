# Local thinking-control definitions

These four local `model.yaml` definitions connect the converted files to LM Studio's documented `enableThinking` custom field, which sets the official Qwen template's `enable_thinking` variable. The default is false; every CallCost request also sends `reasoning: "off"`. The pilot gate independently requires zero reasoning tokens and no emitted reasoning content or think tags.

The Hugging Face-style source names are local directory mappings under `~/.cache/lm-studio/models/And850/`. No corresponding remote repositories were published, and this setup does not download those names. Use the prepared local files; do not run `lms get` on these definitions. Nothing is uploaded to the LM Studio Hub.

Run `python3 scripts/register_local_models.py` from the repository root after conversion. It creates new local entries, hard-links weights to avoid duplicating their storage, copies the small metadata files, and installs these definitions under `~/.cache/lm-studio/hub/models/local/`. It refuses existing targets. The cache layout is specific to the tested LM Studio 0.4.24 installation; a future version may require another installation method. `lms dev --install` accepts plugins and is not the installer for these model definitions.

Allow the local index to refresh, then inspect `callcost models`. Each entry should expose `reasoning.allowed_options: [off, on]` and `reasoning.default: off`. This declaration is not sufficient evidence by itself: run the excluded pilot and inspect the observed tokens and text.

Fairy's original catalog definition and weight files are unchanged. The four local definitions contain the same control settings; only their identifiers and backing precision differ. Fairy's reference retains its original catalog defaults in addition to vision support.

References: [model.yaml](https://lmstudio.ai/docs/app/modelyaml), [native reasoning control](https://lmstudio.ai/docs/developer/rest/chat).
