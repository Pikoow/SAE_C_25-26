import pandas as pd
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

# =========================
# CONFIG
# =========================
CSV_PATH = "synthetic_users_1000_real_tracks.csv"

DB_CONFIG = {
    "host": "localhost",
    "dbname": os.getenv("POSTGRES_DBNAME"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "port": int(os.getenv("POSTGRES_PORT", 5432))
}

# =========================
# LOAD CSV
# =========================
df = pd.read_csv(
    CSV_PATH,
    sep=",",
    encoding="utf-8"
)

# =========================
# CONNECT DB
# =========================
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# =========================
# CREATE TABLE IF NEEDED
# =========================
cur.execute("""
CREATE TABLE IF NOT EXISTS sae.user_fake (
    user_id INT PRIMARY KEY,
    user_age INT,
    user_listening_duration INT,
    user_average_duration TEXT,
    user_status TEXT,
    user_favorite_hour TEXT,
    user_favorite_genre TEXT,
    user_favorite_languages TEXT,
    user_favorite_platforms TEXT,
    user_gender TEXT,
    user_job TEXT,
    user_tags TEXT,
    listened_tracks TEXT
);
""")
conn.commit()

# =========================
# OPTIONAL CLEAN
# =========================
cur.execute("TRUNCATE TABLE sae.user_fake;")
conn.commit()

# =========================
# INSERT QUERY
# =========================
insert_query = """
INSERT INTO sae.user_fake (
    user_id,
    user_age,
    user_listening_duration,
    user_average_duration,
    user_status,
    user_favorite_hour,
    user_favorite_genre,
    user_favorite_languages,
    user_favorite_platforms,
    user_gender,
    user_job,
    user_tags,
    listened_tracks
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (user_id) DO NOTHING;
"""

# =========================
# INSERT DATA
# =========================
for _, row in df.iterrows():
    cur.execute(insert_query, (
        int(row["user_id"]),
        int(row["user_age"]),
        int(row["user_listening_duration"]),
        str(row["user_average_duration"]),
        row["user_status"],
        row["user_favorite_hour"],
        row["user_favorite_genre"],
        row["user_favorite_languages"],
        row["user_favorite_platforms"],
        row["user_gender"],
        row["user_job"],
        row["user_tags"],
        row["listened_tracks"]
    ))

conn.commit()

cur.close()
conn.close()

print("Table user_fake alimentée avec succès")
