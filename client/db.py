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

# only needs to be ran once
#load_csv_to_db()