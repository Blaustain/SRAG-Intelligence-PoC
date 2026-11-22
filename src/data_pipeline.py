"""Carga e saneamento da base pública SIVEP-Gripe/SRAG."""
from pathlib import Path
import zipfile
import pandas as pd

COLS = ["NU_NOTIFIC", "DT_SIN_PRI", "DT_INTERNA", "DT_ENTUTI", "DT_SAIDUTI",
        "EVOLUCAO", "DT_EVOLUCA", "UTI", "VACINA", "VACINA_COV",
        "SG_UF", "SG_UF_INTE", "CLASSI_FIN", "HOSPITAL", "CS_SEXO"]
DATE_COLS = ["DT_SIN_PRI", "DT_INTERNA", "DT_ENTUTI", "DT_SAIDUTI", "DT_EVOLUCA"]


def _parse_dates(series: pd.Series) -> pd.Series:
    # Arquivos SIVEP podem trazer datas ISO ou DD/MM/AAAA.
    return pd.to_datetime(series, errors="coerce", format="mixed", dayfirst=True)


def load_srag(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            csvs = [n for n in z.namelist() if n.lower().endswith(".csv")]
            if not csvs:
                raise ValueError("O ZIP não contém CSV.")
            with z.open(csvs[0]) as f:
                df = pd.read_csv(f, sep=";", encoding="latin1", usecols=lambda c: c in COLS,
                                 low_memory=False, dtype={"NU_NOTIFIC": "string"})
    else:
        df = pd.read_csv(path, sep=";", encoding="latin1", usecols=lambda c: c in COLS,
                         low_memory=False, dtype={"NU_NOTIFIC": "string"})
    for col in DATE_COLS:
        if col in df:
            df[col] = _parse_dates(df[col])
    for col in ["UTI", "EVOLUCAO", "VACINA", "VACINA_COV", "HOSPITAL"]:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "DT_SIN_PRI" not in df:
        raise ValueError("A base não contém DT_SIN_PRI, necessária para a série temporal.")
    df = df.dropna(subset=["DT_SIN_PRI"]).copy()
    df = df[df["DT_SIN_PRI"] <= pd.Timestamp.today().normalize()]
    if "NU_NOTIFIC" in df:
        df = df.drop_duplicates(subset=["NU_NOTIFIC"], keep="last")
    return df.reset_index(drop=True)
