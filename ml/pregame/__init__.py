"""Pregame betting models — HFA, Elo, SRS, opp-adj EPA, logistic, ridge.

HFA/Elo/SRS/opp-adj EPA live on ``feature_snapshots`` (``python -m ml.features.build``).
Logistic and Ridge train via ``python -m ml.pregame.walk_forward``. Market 0 is the close, not a PURE input.
Lab order: docs/research/011-model-lab-reproductions.md.
"""
