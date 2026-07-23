from datetime import date, timedelta

from app.forecast import compute_forecast, detect_anomalies


def series(n: int, value_fn=lambda i: 100.0, start: date = date(2026, 1, 1)):
    return [(start + timedelta(days=i), value_fn(i)) for i in range(n)]


def test_empty_history_returns_no_points():
    result = compute_forecast([])
    assert result.points == []
    assert result.confidence == "low"


def test_sparse_history_falls_back_to_moving_average():
    history = series(10)
    result = compute_forecast(history)
    assert result.method == "moving_average"
    assert result.confidence == "low"
    assert len(result.points) == 14


def test_medium_history_uses_regression_medium_confidence():
    history = series(30)
    result = compute_forecast(history)
    assert result.method == "linear_regression"
    assert result.confidence == "medium"


def test_long_history_is_high_confidence():
    history = series(65)
    result = compute_forecast(history)
    assert result.confidence == "high"


def test_forecast_follows_upward_trend():
    # Clear +10/day trend with no seasonality — the fitted trend should continue upward.
    history = series(40, value_fn=lambda i: 100.0 + 10.0 * i)
    result = compute_forecast(history)
    assert result.points[-1].revenue > result.points[0].revenue


def test_forecast_horizon_is_14_days_by_default():
    result = compute_forecast(series(40))
    assert len(result.points) == 14
    assert result.points[0].date == date(2026, 1, 1) + timedelta(days=40)


def test_detect_anomalies_flags_a_spike():
    values = [100.0] * 20
    values[15] = 1000.0
    history = list(zip([date(2026, 1, 1) + timedelta(days=i) for i in range(20)], values))

    anomalies = detect_anomalies(history)

    assert any(a.date == date(2026, 1, 1) + timedelta(days=15) for a in anomalies)


def test_detect_anomalies_flat_series_has_no_anomalies():
    assert detect_anomalies(series(20)) == []


def test_detect_anomalies_needs_minimum_history():
    assert detect_anomalies(series(5)) == []
