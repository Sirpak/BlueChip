# 007 — Data leakage and the research clock

## Citation

Standard ML: leakage, target leakage, look-ahead. Sports-specific: using closing information at open; using **observed** weather; using post-game injury lists; `vegas_wp` in a “fundamental” model; shuffling games. Holdout harvesting.

## Question

How do we guarantee a prediction at `prediction_at` uses only facts with `known_at < prediction_at`?

## Dataset

Any snapshot table: injuries, odds, weather, depth charts, news events.

## Model

n/a — process. Tests in CI.

## Features

Four classes must be named on the snapshot (`PURE` … `ALL`). Market accidentally in PURE is a test failure.

## Train/test methodology

Walk-forward is necessary, not sufficient. **Develop 2009–2022. Sacred holdout 2023–2025 opens once** after freeze ([04-bcw-v0.1.md](../roadmap/04-bcw-v0.1.md)). Repeat inspection of 2023–25 to “tweak the model” **is** fitting the test set. Current-game EPA and `vegas_wp` are banned from PURE.

Time clocks: T−24h vs T−60m vs pregame as different experiments.

## Result

(To be measured.) Goal: a leakage test suite that fails the build.

## Limitations

`known_at` is only as honest as the source timestamp. ESPN “retrieved Saturday” ≠ “fan knew Friday.” Document source lag.

## What BlueChip will test

```
assert known_at < prediction_at
assert vegas_wp not in PURE feature list
assert weather.kind != observation for pregame snapshots
assert nflverse vs espn score conflicts surface, not overwrite
```

Feature snapshots persist `feature_version` + `prediction_at` so a 2027 audit can replay Sunday 11am.

## Implemented?

No. Contract specified in [data-dictionary/v0.1-data-contract.md](../data-dictionary/v0.1-data-contract.md).

## Experiment ID

—
