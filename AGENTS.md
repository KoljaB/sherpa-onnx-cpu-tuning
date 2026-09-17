# Repository workflow

This repository publishes an experimental sherpa-ONNX dependency build. It does
not publish RealtimeSTT distributions. Never upload under the upstream PyPI name.
Preserve upstream and bundled dependency licenses and corresponding build sources.
Use exact per-command Git trust for D:/Projekte/sherpa-onnx-cpu-tuning. The workspace
helper cannot initialize a brand-new repository; after verifying the new directory
has no Git metadata, use scoped `git init` for its initial creation.

Before releases: review changed filenames, keep user audio/transcripts and machine
credentials out of the repository, validate source/patch consistency, record native
platform requirements, match the wheel to the tested runtime, and verify the public
asset hashes after upload. Tag experimental releases and never replace an asset
under an existing version. Put compiled artifacts in GitHub Releases, not Git.
