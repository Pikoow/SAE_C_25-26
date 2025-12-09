import csv
import json
import tempfile
import os
import re
import math
from datetime import datetime, date

import psycopg2
import pandas as pd

# ============================================================
# ===================== CONFIG GLOBAL ========================
# ============================================================

# CSV paths (kept exactly as you provided)
ALBUM_CSV_INPUT = "./raw_albums_cleaned.csv"
ARTIST_CSV_INPUT = "./raw_artists_cleaned.csv"
TRACK_CSV_INPUT = "./tracks_clean.csv"
GENRE_CSV_INPUT = "genre_clean.csv"
ECHONEST_CSV_INPUT = "./raw_echonest.csv"
RAW_TRACKS_CSV = "raw_tracks.csv"
USER_CSV_INPUT = "./questionnaire.csv"


# PostgreSQL connection config
HOST = "localhost"
DB = "postgres"
USER = "postgres"
PASSWORD = "6969"
PORT = 5432

# ============================================================
# ===============   FONCTION UTILITAIRE   ====================
# ============================================================

def convert_date(value):
    """
    Convertit une date de type 'MM/DD/YYYY' ou 'MM/DD/YYYY HH:MM:SS AM'
    en 'YYYY-MM-DD'. Renvoie '' si non parsable.
    """
    if value is None:
        return ""
    value = str(value)
    if value.strip() == "":
        return ""

    for fmt in ["%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y"]:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%Y-%m-%d")
        except:
            pass

    return ""

# -----------------------------
# Fonctions utilitaires pour users script
# -----------------------------
def parse_age_from_range(s):
    """Extrait la borne basse d'une tranche '18–25 ans' ou '18-25' ou '18 à 25' ou '18 ans'."""
    if not s:
        return None
    s = str(s).strip()
    m = re.search(r'(\d{1,3})', s)
    if m:
        try:
            return int(m.group(1))
        except:
            return None
    return None

def parse_duration_to_minutes(s):
    """Parse des durées de type '2h', '1h30', '90 min', '45 minutes' en minutes entières."""
    if not s:
        return None
    s = str(s).lower().strip()
    m = re.search(r'(\d+)\s*h(?:[:h\s]*(\d+))?', s)
    if m:
        hours = int(m.group(1))
        mins = int(m.group(2)) if m.group(2) else 0
        return hours * 60 + mins
    m = re.search(r'(\d{1,4})\s*(min|minutes|mn)?', s)
    if m:
        return int(m.group(1))
    return None

def parse_average_duration_pref(s):
    """Tente d'extraire une valeur moyenne en minutes depuis préférences ('3-4 min' -> 3 or 3.5)."""
    if not s:
        return None
    s = str(s).lower()
    m = re.search(r'(\d{1,3})(?:\s*[-–to]\s*(\d{1,3}))?', s)
    if m:
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else None
        return int(a) if b is None else int((a + b) / 2)
    return parse_duration_to_minutes(s)

def parse_platforms(s):
    """Renvoie une liste à partir d'une chaîne 'Spotify, YouTube / Apple Music'."""
    if not s:
        return []
    s2 = re.sub(r'[/\\|]', ',', str(s))
    s2 = re.sub(r'\bet\b', ',', s2, flags=re.I)
    parts = [p.strip() for p in re.split(r'[,\n;]+', s2) if p.strip()]
    return parts

def safe_strip(s):
    return s.strip() if isinstance(s, str) else s

def normalize_job(s):
    if not s:
        return None
    s = str(s).strip().lower()
    if s == "ne se prononce pas":
        return "pas de pref"
    if s is None:
        return "special"
    if s == "autre":
        return "other"
    if s == "secteur tertiaire (commerce, transport, santé, éducation, administration, banque, tourisme, culture, loisirs)":
        return "Tertiaire"
    if s == "secteur secondaire (industrie, construction, agroalimentaire, artisanat de production, énergie...)":
        return "Secondaire"
    if s == "secteur primaire (agriculture, pêche, sylviculture, extraction minière, chasse...)":
        return "Primaire"
    return s

def normalize_favorite_hour(s):
    if not s:
        return None
    s = str(s).lower()
    if "toute" in s and "journée" in s:
        return json.dumps(["Toute la journée"], ensure_ascii=False)
    parts = re.split(r'[;,/]| et ', s)
    results = set()
    for p in parts:
        p_clean = p.strip()
        if not p_clean:
            continue
        if "le matin" in p_clean or "matin" in p_clean:
            results.add("matin")
        elif "le midi" in p_clean or "midi" in p_clean:
            results.add("midi")
        elif "le soir" in p_clean or "soir" in p_clean:
            results.add("soir")
        elif "la nuit" in p_clean or "nuit" in p_clean:
            results.add("nuit")
    if not results:
        return None
    return json.dumps(sorted(results), ensure_ascii=False)

def normalize_favorite_language(s):
    if not s:
        return None
    s = str(s).lower()
    if "non" in s or "aucune" in s or "toute langue" in s:
        return json.dumps(["Pas de pref"], ensure_ascii=False)
    parts = re.split(r'[;,/]| et ', s)
    results = set()
    for p in parts:
        p_clean = p.strip()
        if not p_clean:
            continue
        if "français" in p_clean:
            results.add("FR")
        elif "anglais" in p_clean:
            results.add("EN")
        elif "géorgienne" in p_clean:
            results.add("GE")
        elif "malgash" in p_clean:
            results.add("MG")
        elif "espagnol" in p_clean:
            results.add("ES")
        elif "allemand" in p_clean:
            results.add("DE")
        elif "italien" in p_clean:
            results.add("IT")
        elif "indien" in p_clean:
            results.add("IN")
        elif "arabe" in p_clean:
            results.add("DZ")
    if not results:
        return None
    return json.dumps(sorted(results), ensure_ascii=False)

# ============================================================
# =====================   IMPORT ALBUM   =====================
# ============================================================

ALBUM_TARGET_COLUMNS = [
    "album_id",
    "album_handle",
    "album_title",
    "album_type",
    "album_tracks",
    "album_information",
    "album_favorites",
    "album_image_file",
    "album_listens",
    "album_tags",
    "album_date_released",
    "album_date_created",
    "album_engineer",
    "album_producer"
]

ALBUM_COLUMN_MAP = {
    "album_id": "album_id",
    "album_handle": "album_handle",
    "album_title": "album_title",
    "album_type": "album_type",
    "album_tracks": "album_tracks",
    "album_information": "album_information",
    "album_favorites": "album_favorites",
    "album_image_file": "album_image_file",
    "album_listens": "album_listens",
    "tags": "album_tags",
    "album_date_released": "album_date_released",
    "album_date_created": "album_date_created",
    "album_engineer": "album_engineer",
    "album_producer": "album_producer"
}

def import_albums():
    print("[ALBUMS] Début import albums")
    temp_fd, temp_path = tempfile.mkstemp(suffix=".csv")
    os.close(temp_fd)

    with open(ALBUM_CSV_INPUT, encoding="utf-8") as infile, \
        open(temp_path, "w", encoding="utf-8", newline="") as outfile:

        reader = csv.DictReader(infile)
        writer = csv.writer(outfile)
        writer.writerow(ALBUM_TARGET_COLUMNS)

        for row in reader:
            new_row = []
            for col in ALBUM_TARGET_COLUMNS:
                csv_column = None
                for k, v in ALBUM_COLUMN_MAP.items():
                    if v == col:
                        csv_column = k
                        break
                value = row.get(csv_column, "")
                if value is None or str(value).strip().upper() == "NULL":
                    value = ""
                if col in ("album_date_created", "album_date_released"):
                    value = convert_date(value)
                new_row.append(value)
            writer.writerow(new_row)

    print("[ALBUMS] CSV temp créé :", temp_path)

    conn = psycopg2.connect(host=HOST, database=DB, user=USER, password=PASSWORD, port=PORT)
    cur = conn.cursor()

    with open(temp_path, "r", encoding="utf-8") as f:
        cur.copy_expert(f"""
            COPY sae.album (
                {",".join(ALBUM_TARGET_COLUMNS)}
            )
            FROM STDIN
            WITH CSV HEADER;
        """, f)

    conn.commit()
    cur.close()
    conn.close()
    
    os.remove(temp_path)
    print("[ALBUMS] Import albums terminé !")

# ============================================================
# =====================   IMPORT ARTIST   ====================
# ============================================================

ARTIST_TARGET_COLUMNS = [
    "artist_id",
    "artist_password",
    "artist_name",
    "artist_bio",
    "artist_related_project",
    "artist_favorites",
    "artist_image_file",
    "artist_active_year_begin",
    "artist_active_year_end",
    "artist_tags",
    "artist_location",
    "artist_website",
    "artist_latitude",
    "artist_longitude",
    "artist_associated_label",
    "id_rank_artist",
    "user_id"
]

ARTIST_COLUMN_MAP = {
    "artist_id": "artist_id",
    "artist_name": "artist_name",
    "artist_bio": "artist_bio",
    "artist_related_projects": "artist_related_project",
    "artist_favorites": "artist_favorites",
    "artist_image_file": "artist_image_file",
    "artist_active_year_begin": "artist_active_year_begin",
    "artist_active_year_end": "artist_active_year_end",
    "tags": "artist_tags",
    "artist_location": "artist_location",
    "artist_website": "artist_website",
    "artist_latitude": "artist_latitude",
    "artist_longitude": "artist_longitude",
    "artist_associated_labels": "artist_associated_label"
}

def import_artists():
    print("[ARTISTS] Début import artists")
    temp_fd, temp_path = tempfile.mkstemp(suffix=".csv")
    os.close(temp_fd)

    with open(ARTIST_CSV_INPUT, encoding="utf-8") as infile, \
        open(temp_path, "w", encoding="utf-8", newline="") as outfile:

        reader = csv.DictReader(infile)
        writer = csv.writer(outfile)
        writer.writerow(ARTIST_TARGET_COLUMNS)

        for row in reader:
            new_row = []
            for col in ARTIST_TARGET_COLUMNS:
                if col in ("artist_password", "id_rank_artist", "user_id"):
                    new_row.append("")
                    continue
                csv_column = None
                for k, v in ARTIST_COLUMN_MAP.items():
                    if v == col:
                        csv_column = k
                        break
                value = row.get(csv_column, "")
                if value is None or str(value).strip().upper() == "NULL":
                    value = ""
                if col in ("artist_active_year_begin", "artist_active_year_end"):
                    value = convert_date(value)
                new_row.append(value)
            writer.writerow(new_row)

    print("[ARTISTS] CSV temp créé :", temp_path)

    conn = psycopg2.connect(host=HOST, database=DB, user=USER, password=PASSWORD, port=PORT)
    cur = conn.cursor()

    with open(temp_path, "r", encoding="utf-8") as f:
        cur.copy_expert(f"""
            COPY sae.artist (
                {",".join(ARTIST_TARGET_COLUMNS)}
            )
            FROM STDIN
            WITH CSV HEADER;
        """, f)

    conn.commit()
    cur.close()
    conn.close()

    os.remove(temp_path)
    print("[ARTISTS] Import artists terminé !")

# ============================================================
# =====================   IMPORT TRACKS  =====================
# ============================================================

def parse_date_track(value):
    if pd.isna(value) or value == "":
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").date()
    except:
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except:
            return None

def import_tracks():
    print("[TRACKS] Début import tracks")
    df = pd.read_csv(TRACK_CSV_INPUT)

    df_sql = pd.DataFrame({
        "track_id": df["track_id"],
        "track_title": df["track_title"],
        "track_duration": df["track_duration"],
        "track_genre_top": df["track_genre_top"],
        "track_genre": df["track_genres"],
        "track_listens": df["track_listens"],
        "track_favorite": df["track_favorites"],
        "track_interest": df["track_interest"],
        "track_date_recorded": df["track_date_recorded"].apply(parse_date_track),
        "track_date_created": df["track_date_created"].apply(parse_date_track),
        "track_composer": df["track_composer"],
        "track_lyricist": df["track_lyricist"],
        "track_tags": df["track_tags"],
        "track_artist_id": None,
        "track_rank_id": None,
        "track_feature_id": None,
        "track_file": None,
        "track_disk_number": df["track_number"],
        "track_bit_rate": df["track_bit_rate"]
    })

    df_sql = df_sql.where(pd.notnull(df_sql), None)

    conn = psycopg2.connect(
        dbname=DB,
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT
    )
    cur = conn.cursor()

    columns = ",".join(df_sql.columns)
    placeholders = ",".join(["%s"] * len(df_sql.columns))

    sql = f"""
    INSERT INTO sae.tracks ({columns})
    VALUES ({placeholders})
    ON CONFLICT (track_id) DO NOTHING;
    """

    data = [tuple(row) for row in df_sql.to_numpy()]

    cur.executemany(sql, data)
    conn.commit()

    print("[TRACKS] Import tracks terminé :", len(data), "lignes insérées.")

    cur.close()
    conn.close()

# ============================================================
# =====================   IMPORT GENRE   =====================
# ============================================================

def import_genre():
    print("[GENRE] Début import genre")
    CSV_PATH = GENRE_CSV_INPUT

    PG_CONFIG = {
        "host": HOST,
        "dbname": DB,
        "user": USER,
        "password": PASSWORD,
        "port": PORT
    }

    def to_int_or_none(x):
        if x is None or pd.isna(x):
            return None
        return int(x)

    print("[GENRE] Chargement CSV…")
    df = pd.read_csv(CSV_PATH)

    df = df.rename(columns={"#tracks": "tracks"})

    # conversions -> numpy → python
    df["genre_id"] = pd.to_numeric(df["genre_id"], errors="coerce")
    df["genre_parent_id"] = pd.to_numeric(df["genre_parent_id"], errors="coerce")
    df["tracks"] = pd.to_numeric(df["tracks"], errors="coerce")

    df["genre_title"] = df["title"].astype(str)
    df["top_level"] = df["top_level"].apply(lambda x: str(x).strip() != "0")

    print(df[["genre_id","genre_parent_id","genre_title","genre_handle","genre_color","top_level","tracks"]].head())

    insert_sql = """
    INSERT INTO sae.genre (
        genre_id,
        genre_parent_id,
        genre_title,
        genre_handle,
        genre_color,
        top_level,
        tracks
    ) VALUES (%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (genre_id) DO NOTHING;
    """

    print("[GENRE] Connexion PostgreSQL…")
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    count = 0

    for _, row in df.iterrows():
        cur.execute(insert_sql, (
            to_int_or_none(row["genre_id"]),
            to_int_or_none(row["genre_parent_id"]),
            row["genre_title"],
            row["genre_handle"],
            row["genre_color"],
            bool(row["top_level"]),
            to_int_or_none(row["tracks"])
        ))
        count += 1

    conn.commit()
    cur.close()
    conn.close()

    print("===================================")
    print("[GENRE] IMPORT GENRE TERMINÉ")
    print("Lignes insérées :", count)
    print("===================================")

# ============================================================
# =====================   IMPORT ECHONEST AUDIO   ============
# ============================================================

def import_echonest_audio():
    print("[ECHONEST] Début import Echonest audio")
    CSV_PATH = ECHONEST_CSV_INPUT
    PG_CONFIG = {
        "host": HOST,
        "dbname": DB,
        "user": USER,
        "password": PASSWORD,
        "port": PORT
    }

    print("[ECHONEST] Lecture du CSV brut…")
    raw = pd.read_csv(CSV_PATH, header=None, low_memory=False)

    # find line with 'track_id'
    track_id_row = None
    for i in range(0, 10):
        if raw.iloc[i].astype(str).str.contains("track_id", case=False, na=False).any():
            track_id_row = i
            break

    if track_id_row is None:
        raise ValueError("[ECHONEST] Impossible de trouver la ligne contenant 'track_id'.")

    print(f"[ECHONEST] Ligne track_id trouvée : {track_id_row}")
    data_start = track_id_row + 1

    header_rows = raw.iloc[:track_id_row+1].fillna("").astype(str)

    def make_colname(col_idx):
        parts = []
        for r in range(header_rows.shape[0]):
            v = header_rows.iat[r, col_idx].strip()
            if v and v.lower() != "nan":
                parts.append(v)
        name = "_".join(parts)
        name = name.replace("__", "_").strip("_")
        return name

    colnames = [make_colname(c) for c in range(raw.shape[1])]

    data = raw.iloc[data_start:].copy().reset_index(drop=True)
    data.columns = colnames

    print(data.columns.tolist()[:20], "...")

    mapping = {
        "track_id": "track_id",
        "audio_features_accousticness": "echonest_audio_features_acousticness",
        "audio_features_danceability": "echonest_audio_features_danceability",
        "audio_features_energy": "echonest_audio_features_energy",
        "audio_features_instrumentalness": "echonest_audio_features_instrumentalness",
        "audio_features_liveness": "echonest_audio_features_liveness",
        "audio_features_speechiness": "echonest_audio_features_speechiness",
        "audio_features_tempo": "echonest_audio_features_tempo",
        "audio_features_valence": "echonest_audio_features_valence"
    }

    missing = [v for v in mapping.values() if v not in data.columns]
    if missing:
        raise KeyError(f"[ECHONEST] Colonnes manquantes dans le CSV : {missing}")

    df_audio = data[list(mapping.values())].copy()

    df_audio.columns = [
        "track_id",
        "audio_features_accousticness",
        "audio_features_danceability",
        "audio_features_energy",
        "audio_features_instrumentalness",
        "audio_features_liveness",
        "audio_features_speechiness",
        "audio_features_tempo",
        "audio_features_valence"
    ]

    df_audio["track_id"] = pd.to_numeric(df_audio["track_id"], errors="coerce").astype("Int64")
    df_audio = df_audio.where(pd.notnull(df_audio), None)

    print("[ECHONEST] Préparation du DataFrame audio terminée.")
    print(df_audio.head())

    print("[ECHONEST] Connexion à PostgreSQL…")
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    # Charger les track_id existants
    cur.execute("SELECT track_id FROM sae.tracks;")
    existing_ids = {row[0] for row in cur.fetchall()}
    print(f"[ECHONEST] {len(existing_ids)} track_id trouvés dans tracks.")

    insert_sql = """
    INSERT INTO sae.audio (
        track_id,
        audio_features_accousticness,
        audio_features_danceability,
        audio_features_energy,
        audio_features_instrumentalness,
        audio_features_liveness,
        audio_features_speechiness,
        audio_features_tempo,
        audio_features_valence
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (track_id) DO NOTHING;
    """

    rows_inserted = 0
    rows_skipped = 0

    for _, row in df_audio.iterrows():
        tid = int(row["track_id"]) if row["track_id"] is not None else None

        if tid not in existing_ids:
            rows_skipped += 1
            continue

        cur.execute(insert_sql, (
            tid,
            row["audio_features_accousticness"],
            row["audio_features_danceability"],
            row["audio_features_energy"],
            row["audio_features_instrumentalness"],
            row["audio_features_liveness"],
            row["audio_features_speechiness"],
            row["audio_features_tempo"],
            row["audio_features_valence"]
        ))

        rows_inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print("=======================================")
    print("[ECHONEST] IMPORT TERMINÉ")
    print(f"[ECHONEST] Lignes insérées : {rows_inserted}")
    print(f"[ECHONEST] Lignes ignorées (track_id non présent dans tracks) : {rows_skipped}")
    print("=======================================")

# ============================================================
# =====================   IMPORT LICENSE   ====================
# ============================================================

def import_license():
    print("[LICENSE] Début import license")
    conn = psycopg2.connect(
        dbname=DB,
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT
    )
    cur = conn.cursor()

    def clean_int(value):
        """Convertit '' ou ' ' ou None en None (NULL en SQL)"""
        if value is None:
            return None
        v = str(value).strip()
        if v == "":
            return None
        try:
            return int(v)
        except:
            return None

    with open(RAW_TRACKS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        inserted = 0
        for row in reader:
            if not row or not row.get("track_id"):
                continue

            track_id = clean_int(row["track_id"])

            # Vérifier que le track existe
            cur.execute("SELECT 1 FROM sae.tracks WHERE track_id = %s;", (track_id,))
            if not cur.fetchone():
                continue

            license_parent_id = clean_int(row.get("license_parent_id"))

            cur.execute("""
                INSERT INTO sae.license (
                    license_parent_id,
                    license_title,
                    license_short_title,
                    license_url,
                    track_license,
                    track_id
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                license_parent_id,
                row.get("license_title"),
                None,
                row.get("license_url"),
                None,
                track_id
            ))
            inserted += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"[LICENSE] Import terminé. Lignes insérées: {inserted}")

# ============================================================
# =====================   IMPORT PUBLISHER  ====================
# ============================================================

def import_publisher():
    print("[PUBLISHER] Début import publisher")
    conn = psycopg2.connect(
        dbname=DB,
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT
    )
    cur = conn.cursor()

    def clean_int(value):
        if value is None:
            return None
        v = str(value).strip()
        if v == "":
            return None
        try:
            return int(v)
        except:
            return None

    def clean_str(value):
        if value is None:
            return None
        v = str(value).strip()
        if v == "":
            return None
        return v

    with open(RAW_TRACKS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            if not row.get("track_id"):
                continue

            publisher_id = clean_int(row["track_id"])
            publisher_name = clean_str(row.get("track_publisher"))

            if publisher_name is None:
                continue

            try:
                cur.execute("""
                    INSERT INTO sae.publisher (publisher_id, publisher_name)
                    VALUES (%s, %s)
                    ON CONFLICT (publisher_id) DO NOTHING;
                """, (publisher_id, publisher_name))
            except Exception as e:
                print(f"[PUBLISHER] Erreur sur track_id {publisher_id} :", e)
                conn.rollback()
            else:
                conn.commit()
                count += 1

    cur.close()
    conn.close()

    print("===================================")
    print("[PUBLISHER] Terminé — valeurs NULL ignorées.")
    print("Lignes insérées :", count)
    print("===================================")

# ============================================================
# =====================   IMPORT USERS (QUESTIONNAIRE) =======
# ============================================================

# TARGET_COLUMNS used for COPY
USERS_TARGET_COLUMNS = [
    "user_firstName",
    "user_lastName",
    "user_age",
    "user_year_created",
    "user_image",
    "user_location",
    "user_listening_duration",
    "user_average_duration",
    "user_status",
    "user_average_listenedBPM",
    "user_favorite_hour",
    "user_favorite_genre",
    "user_favorite_language",
    "user_favorite_platforms",
    "user_gender",
    "user_job",
    "user_average_valence",
    "user_playlist_Id",
    "user_tags",
    "user_password",
    "user_mail",
    "user_phoneNumber"
]

def transform_user_row(csv_row):
    out = {col: None for col in USERS_TARGET_COLUMNS}

    age_src = csv_row.get("🎉 Dans quelle tranche d’âge vous situez-vous ?", "") or csv_row.get("🎉 Dans quelle tranche d’âge vous situez-vous ? ", "")
    out["user_age"] = parse_age_from_range(age_src)
    out["user_year_created"] = date.today().isoformat()
    out["user_location"] = safe_strip(csv_row.get("📍 D'où écoutez-vous ?", ""))
    out["user_listening_duration"] = parse_duration_to_minutes(csv_row.get("🎧 Combien de temps écoutez-vous de la musique par jour ?", ""))
    out["user_average_duration"] = parse_average_duration_pref(csv_row.get("🕰️ Quelle durée de musique préférez-vous ?", ""))
    out["user_status"] = safe_strip(csv_row.get("💼 Quelle est votre situation ?", ""))
    out["user_favorite_genre"] = safe_strip(csv_row.get("🎶 Quels genres de musique écoutez-vous ?", ""))
    out["user_favorite_language"] = normalize_favorite_language(csv_row.get("🗣️🎵 Avez-vous des préférences pour la langue de la musique ?", ""))
    
    platforms_raw = csv_row.get("💬 Si oui, lesquelles utilisez-vous ? (vous pouvez en sélectionner plusieurs)", "")
    platforms_list = parse_platforms(platforms_raw)
    uses_streaming = (csv_row.get("👉 Utilisez-vous des plateformes de streaming ?", "") or "").strip().lower()
    if uses_streaming and uses_streaming in ("non", "non " , "no", "non merci"):
        platforms_list = []
    out["user_favorite_platforms"] = json.dumps(platforms_list, ensure_ascii=False) if platforms_list else None

    out["user_favorite_hour"] = normalize_favorite_hour(csv_row.get("🕙 Sur quels créneaux horaires écoutez-vous de la musique ?", ""))
    out["user_gender"] = safe_strip(csv_row.get("♀️♂️⚧️ À quel genre vous identifiez-vous ?", ""))
    out["user_job"] = normalize_job(csv_row.get("🔍 Dans quelle domaine travaillez-vous ?", ""))

    tags_parts = []
    t1 = csv_row.get("🔂 Avez-vous tendance à toujours écouter les mêmes artistes/playlists ou à en découvrir de nouveaux ?", "")
    if t1: tags_parts.append(safe_strip(t1))
    t2 = csv_row.get("🔄 Changez vous régulièrement de style / genre de musique ?", "")
    if t2: tags_parts.append(safe_strip(t2))
    out["user_tags"] = ", ".join(tags_parts) if tags_parts else None

    # Fields not present in form
    out["user_average_listenedBPM"] = None
    out["user_average_valence"] = None
    out["user_playlist_Id"] = None
    out["user_image"] = None
    out["user_mail"] = None
    out["user_phoneNumber"] = None
    out["user_password"] = None
    out["user_firstName"] = None
    out["user_lastName"] = None

    return out

def import_users():
    print("[USERS] Début import users (questionnaire)")
    CSV_INPUT = USER_CSV_INPUT
    TARGET_TABLE = "sae.users"

    with open(CSV_INPUT, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("[USERS] Aucune ligne trouvée dans le CSV.")
        return

    temp_fd, temp_path = tempfile.mkstemp(suffix=".csv")
    os.close(temp_fd)

    with open(temp_path, "w", encoding="utf-8", newline='') as outf:
        writer = csv.writer(outf)
        writer.writerow(USERS_TARGET_COLUMNS)

        for r in rows:
            transformed = transform_user_row(r)
            row_for_csv = []
            for col in USERS_TARGET_COLUMNS:
                val = transformed.get(col)
                if val is None:
                    row_for_csv.append(r'\N')
                else:
                    row_for_csv.append(str(val))
            writer.writerow(row_for_csv)

    print("[USERS] CSV temporaire créé :", temp_path, " — lignes :", len(rows))

    conn = psycopg2.connect(host=HOST, database=DB, user=USER, password=PASSWORD, port=PORT)
    cur = conn.cursor()

    copy_sql = f"""
        COPY {TARGET_TABLE} (
            {", ".join(USERS_TARGET_COLUMNS)}
        )
        FROM STDIN
        WITH CSV HEADER
        NULL AS '\\N';
    """

    with open(temp_path, "r", encoding="utf-8") as f:
        cur.copy_expert(copy_sql, f)

    conn.commit()
    cur.close()
    conn.close()
    os.remove(temp_path)

    print("[USERS] Import termine vers", TARGET_TABLE)

# ============================================================
# =====================   MAIN / RUN ALL ======================
# ============================================================

def main():
    print("========================================")
    print("DEBUT DU PROCESSUS D'IMPORT — populateFinale.py")
    print("========================================\n")

    try:
        import_albums()
    except Exception as e:
        print("[MAIN] Erreur lors de l'import albums :", e)

    try:
        import_artists()
    except Exception as e:
        print("[MAIN] Erreur lors de l'import artists :", e)

    try:
        import_tracks()
    except Exception as e:
        print("[MAIN] Erreur lors de l'import tracks :", e)

    try:
        import_genre()
    except Exception as e:
        print("[MAIN] Erreur lors de l'import genre :", e)

    try:
        import_echonest_audio()
    except Exception as e:
        print("[MAIN] Erreur lors de l'import echonest audio :", e)

    try:
        import_license()
    except Exception as e:
        print("[MAIN] Erreur lors de l'import license :", e)

    try:
        import_publisher()
    except Exception as e:
        print("[MAIN] Erreur lors de l'import publisher :", e)

    try:
        import_users()
    except Exception as e:
        print("[MAIN] Erreur lors de l'import users :", e)

    print("\n========================================")
    print("TOUS LES IMPORTS TERMINÉS")
    print("========================================")

if __name__ == "__main__":
    main()
