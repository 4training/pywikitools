from .base import CorrectorBase
from .universal import UniversalCorrector, RTLCorrector

class ArabicCorrector(CorrectorBase, UniversalCorrector, RTLCorrector):
    pass
