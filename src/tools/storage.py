import sqlite3, json
import pandas as pd
from pathlib import Path
from typing import Iterable, Dict, Any, List
from ..settings import settings

def _conn():
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(settings.db_path)

def _sanitize_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    df = df.copy()
    df.columns = [str(c).replace(".", "_").replace("$", "S_") for c in df.columns]
    for col in df.columns:
        df[col] = df[col].map(lambda v: json.dumps(v) if isinstance(v, (list, dict)) else v)
    return df

def _sqlite_type_of_series(s: pd.Series) -> str:
    kind = s.dtype.kind
    if kind in ("i", "u"): return "INTEGER"
    if kind in ("f"):       return "REAL"
    return "TEXT"

def _ensure_columns(name: str, df: pd.DataFrame, con: sqlite3.Connection):
    cur = con.execute(f"PRAGMA table_info({name})")
    existing = {row[1] for row in cur.fetchall()}  # 2. stĺpec je name
    missing = [c for c in df.columns if c not in existing]
    for col in missing:
        coltype = _sqlite_type_of_series(df[col])
        con.execute(f'ALTER TABLE {name} ADD COLUMN "{col}" {coltype}')
    con.commit()

def _to_sql(name: str, df: pd.DataFrame, mode="replace") -> int:
    df = _sanitize_df(df)
    if df is None or df.empty:
        return 0
    with _conn() as c:
        try:
            df.to_sql(name, c, if_exists=mode, index=False)
        except sqlite3.OperationalError as e:
            # keď append a chýbajú stĺpce → doplň a skús znova
            if mode == "append" and "no column named" in str(e).lower():
                _ensure_columns(name, df, c)
                df.to_sql(name, c, if_exists="append", index=False)
            else:
                raise
    return len(df)

def save_networks(networks: List[Dict[str, Any]]) -> int:
    return _to_sql("networks", pd.DataFrame(networks), "replace")

def save_devices(devices: List[Dict[str, Any]]) -> int:
    return _to_sql("devices", pd.DataFrame(devices), "replace")

def save_wan_usage(rows: Iterable[Dict[str, Any]]) -> int:
    flat = []
    for r in rows:
        base = {k: v for k, v in r.items() if k != "byUplink"}
        uplinks = r.get("byUplink", [])
        if not uplinks:
            flat.append(base)
        else:
            for u in uplinks:
                rec = base.copy()
                rec.update({
                    "uplink_interface": u.get("interface"),
                    "uplink_sent": u.get("sent"),
                    "uplink_received": u.get("received"),
                    "uplink_serial": u.get("serial"),
                })
                extra = {k: u[k] for k in u.keys() - {"interface","sent","received","serial"}}
                if extra:
                    rec["uplink_extra"] = extra
                flat.append(rec)
    return _to_sql("wan_usage", pd.DataFrame(flat), "append")

def save_switch_ports(serial: str, rows: List[Dict[str, Any]]) -> int:
    df = pd.DataFrame(rows)
    if df.empty: return 0
    df.insert(0, "serial", serial)
    return _to_sql("switch_ports_usage", df, "append")