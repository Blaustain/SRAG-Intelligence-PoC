"""Persistência local SQLite para a PoC e consultas parametrizadas."""
import sqlite3
from pathlib import Path
import pandas as pd


def build_database(df: pd.DataFrame, db_path: str | Path) -> str:
    path = Path(db_path); path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        df.to_sql("srag_cases", conn, if_exists="replace", index=False, chunksize=5000)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_srag_symptom_date ON srag_cases(DT_SIN_PRI)")
        if "SG_UF" in df:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_srag_state ON srag_cases(SG_UF)")
    return str(path)


def query_cases(db_path: str | Path, state: str | None = None) -> pd.DataFrame:
    sql = "SELECT DT_SIN_PRI, DT_INTERNA, DT_ENTUTI, DT_SAIDUTI, EVOLUCAO, UTI, VACINA, HOSPITAL, SG_UF, SG_UF_INTE, CLASSI_FIN FROM srag_cases"
    params = []
    if state:
        sql += " WHERE SG_UF = ?"; params.append(state)
    with sqlite3.connect(db_path) as conn:
        result = pd.read_sql_query(sql, conn, params=params, parse_dates=["DT_SIN_PRI", "DT_INTERNA", "DT_ENTUTI", "DT_SAIDUTI"])
    return result


def database_summary(db_path: str | Path) -> dict:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT COUNT(*), MIN(DT_SIN_PRI), MAX(DT_SIN_PRI) FROM srag_cases").fetchone()
    return {"rows": row[0], "min_symptom_date": row[1], "max_symptom_date": row[2]}
