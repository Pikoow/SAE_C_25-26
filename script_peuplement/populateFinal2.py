import pandas as pd
import psycopg2
import re

# ============================================================
# CONFIG
# ============================================================
CSV_PATH = "./clean_echonest.csv"
PG_CONFIG = {
    "host": "localhost",
    "dbname": "postgres",
    "user": "postgres",
    "password": "6969",
    "port": 5432
}

# ============================================================
# LECTURE UNIQUE DU CSV
# ============================================================
def load_csv():
    df = pd.read_csv(CSV_PATH, low_memory=False)
    df.columns = [c.lower() for c in df.columns]
    print("Colonnes du CSV :", df.columns.tolist())
    return df


# ============================================================
# PEUPLEMENT artist_social_score + artist_rank
# ============================================================
def populate_artist_social_and_rank(df):

    print("\n===== PEUPLEMENT artist_social_score + artist_rank =====")

    social_cols = {
        "social_features_artist_discovery": "echonest_social_features_artist_discovery",
        "social_features_artist_familiarity": "echonest_social_features_artist_familiarity",
        "social_features_artist_hottnesss": "echonest_social_features_artist_hotttnesss"
    }

    rank_cols = {
        "ranks_artist_discovery_rank": "echonest_ranks_artist_discovery_rank",
        "ranks_artist_familiarity_rank": "echonest_ranks_artist_familiarity_rank",
        "ranks_artist_hottnesss_rank": "echonest_ranks_artist_hotttnesss_rank"
    }

    # Vérifications
    for col in list(social_cols.values()) + list(rank_cols.values()):
        if col.lower() not in df.columns:
            raise KeyError(f"Colonne manquante dans CSV : {col}")

    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    cur.execute("SELECT track_id, artist_id FROM sae.tracks;")
    track_to_artist = {t: a for t, a in cur.fetchall()}

    insert_social = """
        INSERT INTO sae.artist_social_score (
            artist_id,
            social_features_artist_discovery,
            social_features_artist_familiarity,
            social_features_artist_hottnesss
        ) VALUES (%s, %s, %s, %s)
        ON CONFLICT (artist_id) DO UPDATE SET
            social_features_artist_discovery = EXCLUDED.social_features_artist_discovery,
            social_features_artist_familiarity = EXCLUDED.social_features_artist_familiarity,
            social_features_artist_hottnesss = EXCLUDED.social_features_artist_hottnesss;
    """

    insert_rank = """
        INSERT INTO sae.artist_rank (
            artist_id,
            ranks_artist_discovery_rank,
            ranks_artist_familiarity_rank,
            ranks_artist_hottnesss_rank
        ) VALUES (%s, %s, %s, %s)
        ON CONFLICT (artist_id) DO UPDATE SET
            ranks_artist_discovery_rank = EXCLUDED.ranks_artist_discovery_rank,
            ranks_artist_familiarity_rank = EXCLUDED.ranks_artist_familiarity_rank,
            ranks_artist_hottnesss_rank = EXCLUDED.ranks_artist_hottnesss_rank;
    """

    inserted = skipped = 0

    for _, row in df.iterrows():
        tid = row["track_id"]
        if tid not in track_to_artist:
            skipped += 1
            continue

        artist_id = track_to_artist[tid]

        cur.execute(insert_social, (
            artist_id,
            row[social_cols["social_features_artist_discovery"]],
            row[social_cols["social_features_artist_familiarity"]],
            row[social_cols["social_features_artist_hottnesss"]],
        ))

        cur.execute(insert_rank, (
            artist_id,
            row[rank_cols["ranks_artist_discovery_rank"]],
            row[rank_cols["ranks_artist_familiarity_rank"]],
            row[rank_cols["ranks_artist_hottnesss_rank"]],
        ))

        inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"FIN : {inserted} insérés, {skipped} ignorés.")


# ============================================================
# PEUPLEMENT song_rank
# ============================================================
def populate_song_rank(df):

    print("\n===== PEUPLEMENT song_rank =====")

    song_cols = {
        "currency": "echonest_ranks_song_currency_rank",
        "hottness": "echonest_ranks_song_hotttnesss_rank"
    }

    for col in song_cols.values():
        if col.lower() not in df.columns:
            raise KeyError(f"Colonne manquante dans CSV : {col}")

    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    cur.execute("SELECT track_id FROM sae.tracks;")
    known_tracks = {t for (t,) in cur.fetchall()}

    insert_song_rank = """
        INSERT INTO sae.song_rank (
            track_id,
            ranks_song_currency_rank,
            ranks_song_hottness_rank
        ) VALUES (%s, %s, %s)
        ON CONFLICT (track_id) DO UPDATE SET
            ranks_song_currency_rank = EXCLUDED.ranks_song_currency_rank,
            ranks_song_hottness_rank = EXCLUDED.ranks_song_hottness_rank;
    """

    inserted = skipped = 0

    for _, row in df.iterrows():
        tid = row["track_id"]
        if tid not in known_tracks:
            skipped += 1
            continue

        cur.execute(insert_song_rank, (
            tid,
            row[song_cols["currency"]],
            row[song_cols["hottness"]],
        ))

        inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"FIN : {inserted} insérés, {skipped} ignorés.")


# ============================================================
# PEUPLEMENT temporal_features
# ============================================================
def populate_temporal_features(df):

    print("\n===== PEUPLEMENT temporal_features =====")

    temporal_cols = sorted(
        [c for c in df.columns if c.startswith("echonest_temporal_features_")],
        key=lambda x: int(re.findall(r"\d+", x)[0])
    )

    renamed_cols = {
        old: "temporal_features_" + old.split("_")[-1]
        for old in temporal_cols
    }

    df_temp = df[["track_id"] + temporal_cols].copy()
    df_temp.rename(columns=renamed_cols, inplace=True)
    df_temp["track_id"] = pd.to_numeric(df_temp["track_id"], errors="coerce").astype("Int64")
    df_temp = df_temp.where(pd.notnull(df_temp), None)

    feature_cols = list(renamed_cols.values())
    df_temp = df_temp.dropna(subset=feature_cols, how="all")

    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    cur.execute("SELECT track_id FROM sae.tracks;")
    existing_ids = {row[0] for row in cur.fetchall()}

    columns_sql = ", ".join(["track_id"] + feature_cols)
    placeholders = ", ".join(["%s"] * (1 + len(feature_cols)))

    insert_sql = f"""
        INSERT INTO sae.temporal_features (
            {columns_sql}
        ) VALUES ({placeholders})
        ON CONFLICT (track_id) DO NOTHING;
    """

    inserted = skipped = 0

    for _, row in df_temp.iterrows():
        tid = int(row["track_id"]) if row["track_id"] else None

        if tid not in existing_ids:
            skipped += 1
            continue

        values = [tid] + [row[col] for col in feature_cols]
        cur.execute(insert_sql, values)
        inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"FIN : {inserted} insérés, {skipped} ignorés.")


# ============================================================
# PEUPLEMENT song_social_score
# ============================================================
def populate_song_social_score(df):

    print("\n===== PEUPLEMENT song_social_score =====")

    mapping = {
        "track_id": "track_id",
        "social_features_song_currency": "currency",
        "social_features_song_hottness": "hotttnesss"
    }

    col_map = {}
    for target_col, keyword in mapping.items():
        if target_col == "track_id":
            col_map[target_col] = "track_id"
            continue

        match = [c for c in df.columns if "song" in c.lower() and keyword in c.lower()]
        if not match:
            raise KeyError(f"Impossible de trouver colonne '{keyword}' dans CSV.")
        col_map[target_col] = match[0]

    df_social = df[list(col_map.values())].copy()
    df_social.columns = list(mapping.keys())
    df_social["track_id"] = pd.to_numeric(df_social["track_id"], errors="coerce").astype("Int64")
    df_social = df_social.where(pd.notnull(df_social), None)
    df_social = df_social.dropna(subset=["social_features_song_currency", "social_features_song_hottness"], how="all")

    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    cur.execute("SELECT track_id FROM sae.tracks;")
    existing_ids = {row[0] for row in cur.fetchall()}

    insert_sql = """
        INSERT INTO sae.song_social_score (
            track_id,
            social_features_song_currency,
            social_features_song_hottness
        ) VALUES (%s, %s, %s)
        ON CONFLICT (track_id) DO NOTHING;
    """

    inserted = skipped = 0

    for _, row in df_social.iterrows():
        tid = int(row["track_id"]) if row["track_id"] else None
        if tid not in existing_ids:
            skipped += 1
            continue

        cur.execute(insert_sql, (tid, row["social_features_song_currency"], row["social_features_song_hottness"]))
        inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"FIN : {inserted} insérés, {skipped} ignorés.")


# ============================================================
# MAIN SCRIPT
# ============================================================
def main():
    df = load_csv()

    populate_artist_social_and_rank(df)
    populate_song_rank(df)
    populate_temporal_features(df)
    populate_song_social_score(df)

    print("\n=== IMPORT COMPLET TERMINÉ ===")


if __name__ == "__main__":
    main()
