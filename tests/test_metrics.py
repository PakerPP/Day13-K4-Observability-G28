from collections import Counter

from app import metrics


def test_percentile_basic() -> None:
    assert metrics.percentile([100, 200, 300, 400], 50) >= 100


def test_error_rate_is_zero_without_requests(monkeypatch) -> None:
    monkeypatch.setattr(metrics, "TRAFFIC", 0)
    monkeypatch.setattr(metrics, "ERRORS", Counter())

    assert metrics.calculate_error_rate_pct() == 0.0


def test_error_rate_is_zero_without_errors(monkeypatch) -> None:
    monkeypatch.setattr(metrics, "TRAFFIC", 10)
    monkeypatch.setattr(metrics, "ERRORS", Counter())

    assert metrics.calculate_error_rate_pct() == 0.0


def test_error_rate_with_failures(monkeypatch) -> None:
    monkeypatch.setattr(metrics, "TRAFFIC", 8)
    monkeypatch.setattr(
        metrics,
        "ERRORS",
        Counter({"RuntimeError": 1, "TimeoutError": 1}),
    )

    result = metrics.snapshot()

    assert result["error_rate_pct"] == 20.0
    assert result["error_breakdown"] == {
        "RuntimeError": 1,
        "TimeoutError": 1,
    }