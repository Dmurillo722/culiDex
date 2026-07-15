import sqlite3
import pandas as pd


CSV_PATH_JAPAN = './data/japan_foods.csv'
CSV_PATH_STARTING = './data/starting_database.csv'
DB_PATH = './data/data.db'


""" Python functions for database access. Uses pandas for now"""

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