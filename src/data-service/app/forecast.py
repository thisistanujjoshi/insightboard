"""Revenue forecasting and anomaly detection.

Pure functions over (date, revenue) series — no FastAPI/DB imports — so they're
testable without a running service. Two behaviors the PRD calls for explicitly:

- **Graceful degradation.** Below 21 days of history a linear-regression trend
  is unreliable, so we fall back to a trailing moving average and label the
  result "low" confidence instead of pretending precision we don't have.
- **Confidence labeling.** 21-59 days -> "medium", 60+ days -> "high" (the PRD's
  own MAPE target is stated for the 60-day-plus cohort).
"""

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
from sklearn.linear_model import LinearRegression

MIN_DAYS_FOR_REGRESSION = 21
HIGH_CONFIDENCE_DAYS = 60
MOVING_AVERAGE_WINDOW = 7
ANOMALY_Z_THRESHOLD = 2.5


@dataclass
class ForecastPoint:
    date: date
    revenue: float


@dataclass
class ForecastResult:
    method: str          # "moving_average" | "linear_regression"
    confidence: str      # "low" | "medium" | "high"
    points: list[ForecastPoint]


@dataclass
class AnomalyPoint:
    date: date
    revenue: float
    expected: float
    z_score: float


def _weekday_features(dates: list[date], day_index_offset: int = 0) -> np.ndarray:
    """Day-index trend column + 6 one-hot weekday columns (Sunday is baseline)."""
    n = len(dates)
    trend = np.arange(day_index_offset, day_index_offset + n, dtype=float).reshape(-1, 1)
    weekday = np.array([d.weekday() for d in dates])
    one_hot = np.zeros((n, 6))
    for i, wd in enumerate(weekday):
        if wd < 6:  # Monday(0)..Saturday(5); Sunday(6) is the baseline
            one_hot[i, wd] = 1.0
    return np.hstack([trend, one_hot])


def compute_forecast(history: list[tuple[date, float]], horizon_days: int = 14) -> ForecastResult:
    if not history:
        return ForecastResult(method="moving_average", confidence="low", points=[])

    history = sorted(history, key=lambda h: h[0])
    dates = [d for d, _ in history]
    revenues = np.array([r for _, r in history], dtype=float)
    last_day = dates[-1]
    future_dates = [last_day + timedelta(days=i) for i in range(1, horizon_days + 1)]

    if len(history) < MIN_DAYS_FOR_REGRESSION:
        window = revenues[-MOVING_AVERAGE_WINDOW:] if len(revenues) >= MOVING_AVERAGE_WINDOW else revenues
        flat_value = float(window.mean())
        points = [ForecastPoint(d, flat_value) for d in future_dates]
        return ForecastResult(method="moving_average", confidence="low", points=points)

    X = _weekday_features(dates)
    model = LinearRegression().fit(X, revenues)

    X_future = _weekday_features(future_dates, day_index_offset=len(dates))
    predicted = np.clip(model.predict(X_future), a_min=0, a_max=None)

    confidence = "high" if len(history) >= HIGH_CONFIDENCE_DAYS else "medium"
    points = [ForecastPoint(d, float(v)) for d, v in zip(future_dates, predicted)]
    return ForecastResult(method="linear_regression", confidence=confidence, points=points)


def detect_anomalies(history: list[tuple[date, float]]) -> list[AnomalyPoint]:
    """Flag days whose revenue deviates from a trailing moving-average baseline
    by more than ANOMALY_Z_THRESHOLD standard deviations of the residuals.
    Needs enough history to establish both a baseline and a residual spread.
    """
    history = sorted(history, key=lambda h: h[0])
    if len(history) < MOVING_AVERAGE_WINDOW + 3:
        return []

    dates = [d for d, _ in history]
    revenues = np.array([r for _, r in history], dtype=float)

    residuals = []
    expecteds = []
    for i in range(MOVING_AVERAGE_WINDOW, len(revenues)):
        baseline = revenues[i - MOVING_AVERAGE_WINDOW:i].mean()
        expecteds.append(baseline)
        residuals.append(revenues[i] - baseline)

    residuals_arr = np.array(residuals)
    std = residuals_arr.std()
    if std == 0:
        return []

    anomalies = []
    for offset, (residual, expected) in enumerate(zip(residuals_arr, expecteds)):
        z = residual / std
        if abs(z) > ANOMALY_Z_THRESHOLD:
            idx = MOVING_AVERAGE_WINDOW + offset
            anomalies.append(AnomalyPoint(
                date=dates[idx], revenue=float(revenues[idx]),
                expected=float(expected), z_score=float(z)))
    return anomalies
