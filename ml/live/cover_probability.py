"""Live P(cover the pregame spread | current state).

Not the same as WP. Needs a live margin distribution (or a spread-aware
WP that is *not* labeled PURE).
"""


def predict(*_args, **_kwargs):  # noqa: ANN002, ANN003
    raise NotImplementedError(
        "Live cover probability comes after WP replication is calibrated."
    )
