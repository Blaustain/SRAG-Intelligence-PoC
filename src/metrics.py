"""Indicadores epidemiológicos. Fórmulas e limitações documentadas."""
import pandas as pd


def calculate_metrics(df: pd.DataFrame, as_of=None) -> dict:
    if df.empty:
        return {"cases": 0, "growth_pct": None, "mortality_pct": None,
                "uti_share_pct": None, "vaccinated_cases_pct": None,
                "period_start": None, "period_end": None}
    end = pd.Timestamp(as_of).normalize() if as_of is not None else df.DT_SIN_PRI.max().normalize()
    start = end - pd.Timedelta(days=29)
    prev_start, prev_end = start - pd.Timedelta(days=30), start - pd.Timedelta(days=1)
    recent = df[df.DT_SIN_PRI.between(start, end)]
    previous = df[df.DT_SIN_PRI.between(prev_start, prev_end)]
    current_n, previous_n = len(recent), len(previous)
    growth = ((current_n - previous_n) / previous_n * 100) if previous_n else None

    # Dicionário SIVEP: 1=Cura, 2=Óbito, 3=Óbito por outras causas, 9=Ignorado.
    # Denominador exclui evolução ausente/desconhecida; mortalidade considera códigos 2 e 3.
    known = df[df.EVOLUCAO.isin([1, 2, 3])] if "EVOLUCAO" in df else pd.DataFrame()
    mortality = (known.EVOLUCAO.isin([2, 3]).mean() * 100) if len(known) else None

    hospitalized = df[df.HOSPITAL.eq(1)] if "HOSPITAL" in df else df
    uti_yes = hospitalized.UTI.eq(1).sum() if "UTI" in hospitalized else 0
    uti_den = hospitalized.UTI.isin([1, 2]).sum() if "UTI" in hospitalized else 0
    uti_share = uti_yes / uti_den * 100 if uti_den else None

    # Este dado é vacinação entre notificações de SRAG, NÃO cobertura vacinal populacional.
    vac_known = df[df.VACINA.isin([1, 2])] if "VACINA" in df else pd.DataFrame()
    vaccinated = (vac_known.VACINA.eq(1).mean() * 100) if len(vac_known) else None
    return {"cases": current_n, "growth_pct": growth, "mortality_pct": mortality,
            "uti_share_pct": uti_share, "vaccinated_cases_pct": vaccinated,
            "period_start": start.date().isoformat(), "period_end": end.date().isoformat(),
            "previous_cases": previous_n, "known_evolution_n": len(known),
            "uti_denominator": int(uti_den), "vaccine_known_n": len(vac_known)}


def daily_series(df: pd.DataFrame, end=None) -> pd.DataFrame:
    if df.empty: return pd.DataFrame(columns=["date", "cases"])
    end = pd.Timestamp(end).normalize() if end is not None else df.DT_SIN_PRI.max().normalize()
    dates = pd.date_range(end=end, periods=30, freq="D")
    s = df.DT_SIN_PRI.dt.normalize().value_counts().reindex(dates, fill_value=0).sort_index()
    return pd.DataFrame({"date": s.index, "cases": s.values})


def monthly_series(df: pd.DataFrame, end=None) -> pd.DataFrame:
    if df.empty: return pd.DataFrame(columns=["month", "cases"])
    end = pd.Timestamp(end) if end is not None else df.DT_SIN_PRI.max()
    periods = pd.period_range(end=end.to_period("M"), periods=12, freq="M")
    s = df.DT_SIN_PRI.dt.to_period("M").value_counts().reindex(periods, fill_value=0).sort_index()
    return pd.DataFrame({"month": s.index.astype(str), "cases": s.values})
