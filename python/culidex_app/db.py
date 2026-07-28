import shutil
import sqlite3
from importlib import resources
from pathlib import Path

import pandas as pd
from platformdirs import user_data_dir

""" Python functions for database access. Uses pandas for now"""

# Dev-only paths, used by load_csv_to_db() to rebuild the seed database from
# the source CSVs. Only valid when run from the repository root (not once
# installed as a package) — this is a maintainer utility, not a runtime path.
CSV_PATH_JAPAN = './data/japan_foods.csv'
CSV_PATH_STARTING = './data/starting_database.csv'

# Runtime DB path: a per-user, writable copy of the pre-built database that
# ships inside the installed package. Copied into place on first run so the
# read-only installed package files are never written to.
_DATA_DIR = Path(user_data_dir("culidex", appauthor=False))
_DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = str(_DATA_DIR / "data.db")

if not (_DATA_DIR / "data.db").exists():
    _seed = resources.files(__package__) / "data" / "data.db"
    with resources.as_file(_seed) as _seed_path:
        shutil.copy(_seed_path, DB_PATH)

# turns csv file into db file
def load_csv_to_db():
    df_japan = pd.read_csv(CSV_PATH_JAPAN)
    df_starting = pd.read_csv(CSV_PATH_STARTING)

    df = pd.concat([df_japan, df_starting], ignore_index=True)
    df = df.drop_duplicates()

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("foods", conn, if_exists="replace", index=False)
    conn.close()
    print(f"Loaded {len(df)} records into DB")


# gets the entire table as dataframe
def fetch_all() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM foods", conn)
    conn.close()
    return df


def search(query: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    q = f"%{query}%"

    df = pd.read_sql("""
                     SELECT * FROM FOODS
                     WHERE name LIKE ?
                     OR category LIKE ?
                     OR country LIKE ?
                     """, conn, params=(q,q,q))
    conn.close()
    return df

_SAVED_DDL = """CREATE TABLE IF NOT EXISTS saved_foods (
                name TEXT PRIMARY KEY,
                saved_at TEXT DEFAULT CURRENT_TIMESTAMP)"""


_RECENT_DDL = """CREATE TABLE IF NOT EXISTS recent_searches (
                name TEXT PRIMARY KEY,
                searched_at TEXT DEFAULT CURRENT_TIMESTAMP)"""

def add_recent_search(name: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_RECENT_DDL)
    conn.execute("""INSERT INTO recent_searches (name, searched_at)
                     VALUES (?, CURRENT_TIMESTAMP)
                     ON CONFLICT(name) DO UPDATE SET searched_at = CURRENT_TIMESTAMP""", (name,))

    # 5 most recent searches only
    conn.execute("""DELETE FROM recent_searches
                     WHERE name NOT IN (
                         SELECT name FROM recent_searches
                         ORDER BY searched_at DESC, rowid DESC
                         LIMIT 5
                     )""")
    conn.commit()
    conn.close()


def delete_recent_search(name: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_RECENT_DDL)
    conn.execute("DELETE FROM recent_searches WHERE name = ?", (name,))
    conn.commit()
    conn.close()


def fetch_recent() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_RECENT_DDL)
    df = pd.read_sql("SELECT name FROM recent_searches ORDER BY searched_at DESC, rowid DESC LIMIT 5", conn)
    conn.close()
    return df


def save_food(name: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_SAVED_DDL)
    conn.execute("INSERT OR IGNORE INTO saved_foods (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()


def unsave_food(name: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_SAVED_DDL)
    conn.execute("DELETE FROM saved_foods WHERE name = ?", (name,))
    conn.commit()
    conn.close()


def fetch_saved() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_SAVED_DDL)
    df = pd.read_sql("SELECT name FROM saved_foods ORDER BY saved_at DESC, rowid DESC", conn)
    conn.close()
    return df


def is_saved(name: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_SAVED_DDL)
    row = conn.execute("SELECT 1 FROM saved_foods WHERE name = ?", (name,)).fetchone()
    conn.close()
    return row is not None


# only needs to be ran once, when building the database
if __name__ == "__main__":
    print("Building database..")
    load_csv_to_db()
