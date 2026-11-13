# Python Artwork Generator

A deterministic, offline procedural-art generator producing a fantasy cosmic scene: golden spiral galaxy, nebula clouds, starfield, luminous stars, and a shadowed planet.

## Runtime
- Python 3.13; standard library only.
- No network, model calls, external assets, or third-party packages.

## Run
```bash
python3 main.py
```
Writes a 1024 × 1024 RGB PNG to `/output/entry.png`.

## Verify
```bash
python3 verify.py
```
Runs twice, compares output bytes, validates PNG chunks/CRC and decoded pixel stream, and enforces the 1 MiB size limit.

The make.fun bounty additionally requires a genuine coding-agent session transcript bundle. Export the actual session with the official make.fun kit; do not fabricate or alter transcripts.

## Continuous integration

GitHub Actions runs the generator twice on Python 3.13, compares the PNG bytes, and runs `verify.py` to check PNG integrity and size. See `.github/workflows/verify.yml`.

The runtime writes to the absolute path `/output/entry.png`. The repository's generated-artwork copy is a separate deliverable and must be added as a binary PNG before submission.
