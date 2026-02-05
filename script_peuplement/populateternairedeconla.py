import csv
import json
import tempfile
import os
import re
import math
from datetime import datetime, date
import io
import psycopg2
import pandas as pd


# ============================================================
# ========= CONFIG GLOBAL (import csv + bdd login) ===========
# ============================================================

track_input = "./aatracks_clean_test.csv"

# PostgreSQL connection config -- to edit
HOST = "localhost"
DB = "postgres"
USER = "postgres"
PASSWORD = "6969"
PORT = 5432

# ============================================================
# ===================== IMPORT ===============================
# ============================================================

ternaire_target_columns = [
    "track_id",
    "album_id",
    "artist_id"
]

ternaire_column_mapping = {
    "track_id": "track_id",
    "album_id": "album_id",
    "artist_id": "artist_id"
}


def populate_ternaire_table():
    print("debut populate_ternaire_table")

    conn = psycopg2.connect(
        host=HOST,
        database=DB,
        user=USER,
        password=PASSWORD,
        port=PORT
    )

    cur = conn.cursor()

    # ===================== FuK test ========================
    cur.execute("SELECT album_id FROM sae.album;")
    valid_album_ids = {str(row[0]) for row in cur.fetchall()}

    cur.execute("SELECT artist_id FROM sae.artist;")
    valid_artist_ids = {str(row[0]) for row in cur.fetchall()}

    print(f"{len(valid_album_ids)} album_id valides charges")
    print(f"{len(valid_artist_ids)} artist_id valides charges")

    print(f"{len(valid_album_ids)} album_id valides charges")
            
    # ===================== BUFFER et main fction ===================

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(ternaire_target_columns)


    skipped_album = skipped_artist = written = 0


    with open(track_input, encoding="utf-8") as infile:
        reader = csv.DictReader(infile)

        for row in reader:
            album_id = row.get("album_id", "").strip()
            artist_id = row.get("artist_id", "").strip()

            if album_id not in valid_album_ids:
                skipped_album += 1
                continue

            if artist_id not in valid_artist_ids:
                skipped_artist += 1
                continue

            writer.writerow([
                row.get("track_id", ""),
                album_id,
                artist_id
            ])
            written += 1
    buffer.seek(0)

    print(f"Lignes ecrites : {written}")
    print(f"Lignes ignorees (album FuK) : {skipped_album}")
    print(f"Lignes ignorees (artist FuK) : {skipped_artist}")


    cur.copy_expert(f"""
        COPY sae.artist_album_track({",".join(ternaire_target_columns)})
        FROM STDIN
        WITH CSV HEADER;
    """, buffer)


    conn.commit()
    cur.close()
    conn.close()

    print("fin populate_ternaire_table")

def main():
    print("\n=== POPULATE TERNAIRE TABLE ===")

    try:
        populate_ternaire_table()
    except Exception as e:
        print(f"Erreur lors du peuplement de la table ternaire : {e}")
    print("\n La table ternaire a ete peuplee avec succes !")

if __name__ == "__main__":
    main()