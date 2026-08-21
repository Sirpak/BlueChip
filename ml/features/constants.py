"""Named constants for BCW-SNAP-v0.1. Tune α/λ only on 2009–2022 later."""

FEATURE_VERSION = "BCW-SNAP-v0.1"

EWMA_ALPHA = 0.20
EXPLOSIVE_PASS_YARDS = 16.0
EXPLOSIVE_RUSH_YARDS = 10.0

ELO_MEAN = 1500.0
ELO_K = 20.0
ELO_HFA = 55.0
ELO_SEASON_REGRESS = 0.25

SRS_ITERS = 50
ADJ_RIDGE_LAM = 5.0
HFA_PRIOR_DEFAULT = 2.0
HFA_PRIOR_MIN_N = 80


def era_label(season: int) -> str:
    if season <= 2005:
        return "1999-2005"
    if season <= 2010:
        return "2006-2010"
    if season <= 2015:
        return "2011-2015"
    if season <= 2020:
        return "2016-2020"
    return "2021-2025"
