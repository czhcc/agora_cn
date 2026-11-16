### Added

- Optional `AGORA_TWHIN_BERT_MODEL_DIR` loads the Twitter recommender's model and tokenizer directly from a local directory, offline, without Hub snapshot completeness checks. Empty/unset preserves the existing Hub cache/warmup flow. Invalid configured directories fail explicitly.
