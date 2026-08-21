"""BlueChipWager model lab.

Two problems, two tracks. Do not mix them.

PREGAME (the product)
    Before kickoff, estimate the distribution of final scoring margin M
    and compare P(M > x) to the market.

LIVE (in-game, nflfastR-shaped)
    Given current game state, P(possession team wins) and expected points
    of the next scoring event.

nflverse is a data provider. We do not wrap their R models. Replication
lives under ``ml.reference.nflfastr`` and is named
``BCW-nflfastR-replication-v1`` — a benchmark, not the betting model.
"""
