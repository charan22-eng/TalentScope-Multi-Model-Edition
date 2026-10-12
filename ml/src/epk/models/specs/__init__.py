"""Model specifications package."""

from .linreg import SPEC as LINREG_SPEC
from .logreg import SPEC as LOGREG_SPEC
from .knn import SPEC as KNN_SPEC
from .svm import SPEC as SVM_SPEC
from .dt import SPEC as DT_SPEC
from .rf import SPEC as RF_SPEC
from .boost import SPEC as BOOST_SPEC

ALL_SPECS = [
    LINREG_SPEC,
    LOGREG_SPEC,
    KNN_SPEC,
    SVM_SPEC,
    DT_SPEC,
    RF_SPEC,
    BOOST_SPEC,
]

__all__ = [
    "LINREG_SPEC",
    "LOGREG_SPEC",
    "KNN_SPEC",
    "SVM_SPEC",
    "DT_SPEC",
    "RF_SPEC",
    "BOOST_SPEC",
    "ALL_SPECS",
]
