import pandas as pd
from src.metrics import calculate_metrics, daily_series, monthly_series


def sample():
    return pd.DataFrame({
        "DT_SIN_PRI": pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-05", "2024-12-10"]),
        "EVOLUCAO": [1, 2, 3, None], "HOSPITAL": [1, 1, 1, 1],
        "UTI": [1, 2, 1, None], "VACINA": [1, 2, 1, None]
    })


def test_metrics():
    m = calculate_metrics(sample(), as_of="2025-01-05")
    assert m["cases"] == 4
    assert abs(m["mortality_pct"] - 66.6666667) < 0.01  # EVOLUCAO 2 e 3 são óbitos
    assert m["uti_share_pct"] == 2/3*100
    assert abs(m["vaccinated_cases_pct"] - 66.6666667) < 0.01


def test_series_lengths():
    d = daily_series(sample(), end="2025-01-05")
    m = monthly_series(sample(), end="2025-01-05")
    assert len(d) == 30 and len(m) == 12
