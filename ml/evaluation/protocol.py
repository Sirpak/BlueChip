"""Frozen evaluation protocol for BCW-v0.1 development.

Holdout 2023–2025 stays sealed. Do not retune from it.
"""

from __future__ import annotations

DEV_SEASON_START = 2009
DEV_SEASON_END = 2022
HOLDOUT_SEASON_START = 2023
HOLDOUT_SEASON_END = 2025
SEASON_TYPE = "REG"

METRICS = ("brier", "log_loss", "ece", "mae", "rmse", "ats", "n")

# Keep searching past λ=100 until MAE flattens or worsens (2009–2022 only).
LAMBDA_GRID = (
    0.0,
    0.01,
    0.1,
    0.5,
    1.0,
    2.0,
    5.0,
    10.0,
    25.0,
    50.0,
    100.0,
    200.0,
    500.0,
    1000.0,
    2000.0,
    5000.0,
)
EWMA_ALPHA_GRID = (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40)

BOOTSTRAP_DRAWS = 400
BOOTSTRAP_SEED = 20260918
BOOTSTRAP_LO = 2.5
BOOTSTRAP_HI = 97.5

PURE_RAW = "PURE-RAW-v0.x"
PURE_ADJ = "PURE-ADJ-v0.x"

MODEL_RIDGE_PURE = "BCW-RIDGE-PURE"
MODEL_RIDGE_RESIDUAL = "BCW-RIDGE-MARKET-RESIDUAL"
MODEL_LOGISTIC = "BCW-LOGISTIC-v0.1"
CANDIDATE_VERSION = "v0.1-candidate"
