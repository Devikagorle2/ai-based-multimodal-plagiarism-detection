"""
Behavior-based copy-paste likelihood using RandomForest on synthetic data.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

warnings.filterwarnings("ignore", category=UserWarning)

MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODEL_DIR / "behavior_rf.joblib"

FEATURE_NAMES = (
    "typing_speed",
    "pause_time",
    "backspace_count",
    "paste_size",
    "typing_variance",
)

_clf: RandomForestClassifier | None = None


def _synthetic_xy(n_samples: int = 800, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    # Label 0: normal typing — varied pauses, some backspaces, moderate paste
    n0 = n_samples // 2
    ts0 = rng.uniform(0.5, 6.0, n0)
    pause0 = rng.uniform(0.08, 0.55, n0)
    bs0 = rng.integers(0, 40, n0)
    paste0 = rng.integers(0, 120, n0)
    var0 = rng.uniform(0.05, 2.5, n0)

    # Label 1: copy-paste — large paste bursts, short pauses, few backspaces
    n1 = n_samples - n0
    ts1 = rng.uniform(2.0, 25.0, n1)  # burst typing speed
    pause1 = rng.uniform(0.01, 0.12, n1)
    bs1 = rng.integers(0, 8, n1)
    paste1 = rng.integers(80, 5000, n1)
    var1 = rng.uniform(0.0, 0.35, n1)

    X0 = np.column_stack([ts0, pause0, bs0, paste0, var0])
    X1 = np.column_stack([ts1, pause1, bs1, paste1, var1])
    X = np.vstack([X0, X1])
    y = np.array([0] * n0 + [1] * n1)
    perm = rng.permutation(len(y))
    return X[perm], y[perm]


def _train_and_save() -> RandomForestClassifier:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    X, y = _synthetic_xy()
    clf = RandomForestClassifier(
        n_estimators=120,
        max_depth=12,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X, y)
    joblib.dump(clf, MODEL_PATH)
    return clf


def get_classifier() -> RandomForestClassifier:
    global _clf
    if _clf is not None:
        return _clf
    if MODEL_PATH.is_file():
        try:
            _clf = joblib.load(MODEL_PATH)
            return _clf
        except Exception:
            _clf = None
    _clf = _train_and_save()
    return _clf


def predict_behavior_score(
    typing_speed: float,
    pause_time: float,
    backspace_count: int,
    paste_size: int,
    typing_variance: float,
) -> float:
    """
    Return probability in [0, 1] that behavior matches copy-paste (class 1).
    """
    try:
        clf = get_classifier()
        X = np.array(
            [
                [
                    float(typing_speed),
                    float(pause_time),
                    int(backspace_count),
                    int(paste_size),
                    float(typing_variance),
                ]
            ],
            dtype=np.float64,
        )
        if hasattr(clf, "predict_proba"):
            proba = clf.predict_proba(X)[0]
            # class 1 = suspicious copy-paste
            if proba.shape[0] > 1:
                return float(max(0.0, min(1.0, proba[1])))
            return float(max(0.0, min(1.0, proba[0])))
        p = float(clf.predict(X)[0])
        return float(max(0.0, min(1.0, p)))
    except Exception:
        return 0.0
