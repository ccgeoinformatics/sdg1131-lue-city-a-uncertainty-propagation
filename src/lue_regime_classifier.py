"""
LUE regime classifier for the SDG 11.3.1 City A experiment.
"""

from __future__ import annotations

EPS = 1e-10


def classify_regime(lcr: float, pgr: float, lcrpgr: float | None = None) -> str:
    """
    Classify into LUE regimes R1..R17 using LCR, PGR, and LCRPGR.

    Sign conditions are based on LCR and PGR. LCRPGR is treated as undefined
    when PGR is effectively zero. The returned value uses the regime label
    format used in the thesis, e.g., "R16".
    """

    def is_zero(x: float) -> bool:
        return abs(x) <= EPS

    def is_equal(x: float, target: float) -> bool:
        return abs(x - target) <= EPS

    lcr0 = is_zero(lcr)
    pgr0 = is_zero(pgr)

    # PGR = 0
    if pgr0:
        if lcr0:
            return "R17"
        if lcr > 0:
            return "R15"
        return "R7"

    # LCR = 0 and PGR != 0
    if lcr0:
        if pgr > 0:
            return "R3"
        return "R11"

    # LCRPGR is required from here onward.
    if lcrpgr is None:
        return "R17"

    # LCR > 0, PGR > 0
    if lcr > 0 and pgr > 0:
        if is_equal(lcrpgr, 1.0):
            return "R1"
        if (lcrpgr > EPS) and (lcrpgr < 1.0 - EPS):
            return "R2"
        if lcrpgr > 1.0 + EPS:
            return "R16"
        return "R17"

    # LCR < 0, PGR > 0
    if lcr < 0 and pgr > 0:
        if (lcrpgr > -1.0 + EPS) and (lcrpgr < -EPS):
            return "R4"
        if is_equal(lcrpgr, -1.0):
            return "R5"
        if lcrpgr < -1.0 - EPS:
            return "R6"
        return "R17"

    # LCR < 0, PGR < 0
    if lcr < 0 and pgr < 0:
        if lcrpgr > 1.0 + EPS:
            return "R8"
        if is_equal(lcrpgr, 1.0):
            return "R9"
        if (lcrpgr > EPS) and (lcrpgr < 1.0 - EPS):
            return "R10"
        return "R17"

    # LCR > 0, PGR < 0
    if lcr > 0 and pgr < 0:
        if (lcrpgr > -1.0 + EPS) and (lcrpgr < -EPS):
            return "R12"
        if is_equal(lcrpgr, -1.0):
            return "R13"
        if lcrpgr < -1.0 - EPS:
            return "R14"
        return "R17"

    return "R17"
