# news-image-20261118

[![news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/luthfiseptian1303-cmyk/news-image-20261118/rank.svg)](https://make.fun/bounty/news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/luthfiseptian1303-cmyk/news-image-20261118/reward.svg)](https://make.fun/bounty/news-image-20261118)

A program that draws one newspaper front page summing up the world's news of Wednesday 18 November 2026 as a 1024x1024 PNG. It is written in Python 3.13 with the standard library only: a small bitmap font, a flat RGB canvas, and a hand-rolled PNG writer, so it runs with no network and produces byte-identical output on every run.

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

This writes `out/entry.png` (1024x1024, under 1 MiB).
