# news-image-20261121 — THE WORLD TODAY, Saturday 21 November 2026

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/cryptocollectorid/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/cryptocollectorid/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

Entry for the make.fun bounty **"Sum up 21 November's world news in one
image"** (pot $100). The program draws a newspaper front page —
**THE WORLD TODAY — Saturday 21 November 2026** — with six stories that
happened or were first reported on Saturday 21 November 2026:

1. **Russia strikes Ukraine** — 400+ drones and 110 missiles hit Kyiv;
   two missiles and a suspected drone come down in Poland.
2. **Myanmar guilty of genocide** — the International Court of Justice
   rules Myanmar committed genocide against the Rohingya people.
3. **Markets tumble on AI sell-off** — the S&P 500 falls into
   correction; the Nasdaq drops 5.3% in a day.
4. **COP31 talks deadlocked** — the climate summit in Antalya runs past
   its deadline over fossil fuels.
5. **Strong quake hits Peru** — a powerful earthquake shakes the
   Peruvian Andes; residents flee outside.
6. **UK and EU sign post-Brexit deal** — three agreements on food,
   carbon and youth mobility in Brussels.

Sources: AP, Reuters, BBC, France 24 (via One Turn, Horizon, Standard
Topic, Medium roundups of 21 November 2026).

## How it works

`main.py` is a single self-contained Python 3 program (standard library
only — no third-party packages, no network, no font files, no downloaded
images). It draws everything in code on a plain RGB canvas: a bitmap
font defined by hand in the file (5×7 glyphs), simple geometric
illustrations per story, and a hand-written PNG encoder. Two runs
produce byte-identical output.

## Run

```sh
mkdir -p out
MAKEFUN_OUTPUT_DIR=$PWD/out python3 main.py
# writes out/entry.png (1024x1024, < 1 MiB)
```

The program validates its own PNG (signature, chunk CRCs, IHDR
dimensions, IEND position) before writing it.

## License

MIT — see `LICENSE`.
