SET SCHEMA 'sae';

/* ##################################################################### */
/*                     CRÉATION DES TABLES TEMPORAIRES                   */
/* ##################################################################### */


/* ========================== CRÉATION DE LA TABLE TEMPORAIRE POUR LES ALBUMS ========================== */

CREATE TABLE IF NOT EXISTS stg_albums (
    album_id            TEXT, 
    album_comments      TEXT, 
    album_date_created  TEXT, 
    album_date_released TEXT,
    album_engineer      TEXT, 
    album_favorites     TEXT, 
    album_handle        TEXT, 
    album_image_file    TEXT,
    album_images        TEXT, 
    album_information   TEXT, 
    album_listens       TEXT, 
    album_producer      TEXT,
    album_title         TEXT, 
    album_tracks        TEXT, 
    album_type          TEXT, 
    album_url           TEXT,
    artist_name         TEXT, 
    artist_url          TEXT, 
    tags                TEXT
);


/* ========================== CRÉATION DE LA TABLE TEMPORAIRE POUR LES ARTISTES ========================== */

CREATE TABLE IF NOT EXISTS stg_artists (
    artist_id                TEXT, 
    artist_active_year_begin TEXT, 
    artist_active_year_end   TEXT,
    artist_associated_labels TEXT, 
    artist_bio               TEXT, 
    artist_comments          TEXT,
    artist_contact           TEXT, 
    artist_date_created      TEXT, 
    artist_donation_url      TEXT,
    artist_favorites         TEXT, 
    artist_flattr_name       TEXT, 
    artist_handle            TEXT,
    artist_image_file        TEXT, 
    artist_images            TEXT, 
    artist_latitude          TEXT,
    artist_location          TEXT, 
    artist_longitude         TEXT, 
    artist_members           TEXT,
    artist_name              TEXT, 
    artist_paypal_name       TEXT, 
    artist_related_projects  TEXT,
    artist_url               TEXT, 
    artist_website           TEXT, 
    artist_wikipedia_page    TEXT, 
    tags                     TEXT
);


/* ========================== CRÉATION DE LA TABLE TEMPORAIRE POUR LES TRACKS ========================== */

CREATE TABLE IF NOT EXISTS stg_tracks (
    track_id                 TEXT, 
    album_id                 TEXT, 
    album_title              TEXT, 
    album_url                TEXT,
    artist_id                TEXT, 
    artist_name              TEXT, 
    artist_url               TEXT, 
    artist_website           TEXT,
    license_image_file       TEXT, 
    license_image_file_large TEXT, 
    license_parent_id        TEXT,
    license_title            TEXT, 
    license_url              TEXT, 
    tags                     TEXT, 
    track_bit_rate           TEXT,
    track_comments           TEXT, 
    track_composer           TEXT, 
    track_copyright_c        TEXT,
    track_copyright_p        TEXT, 
    track_date_created       TEXT, 
    track_date_recorded      TEXT,
    track_disc_number        TEXT, 
    track_duration           TEXT, 
    track_explicit           TEXT,
    track_explicit_notes     TEXT, 
    track_favorites          TEXT, 
    track_file               TEXT,
    track_genres             TEXT, 
    track_image_file         TEXT, 
    track_information        TEXT,
    track_instrumental       TEXT, 
    track_interest           TEXT, 
    track_language_code      TEXT,
    track_listens            TEXT, 
    track_lyricist           TEXT, 
    track_number             TEXT,
    track_publisher          TEXT, 
    track_title              TEXT, 
    track_url                TEXT
);


/* ========================== CRÉATION DE LA TABLE TEMPORAIRE POUR LE QUESTIONNAIRE ========================== */

CREATE TABLE IF NOT EXISTS stg_questionnaire (
    horodateur          TEXT,
    consent             TEXT,
    use_streaming       TEXT,
    platforms           TEXT,
    daily_time          TEXT,
    genres              TEXT,
    devices             TEXT,
    context             TEXT,
    frequency           TEXT,
    time_slots          TEXT,
    languages           TEXT,
    follow_releases     TEXT,
    discovery_habits    TEXT,
    change_styles       TEXT,
    track_duration_pref TEXT,
    lyrics_pref         TEXT,
    continue_form       TEXT,
    age_range           TEXT,
    gender              TEXT,
    status              TEXT,
    job_sector          TEXT,
    unused_column       TEXT
);


/* ##################################################################### */
/*                    PEUPLEMENT DES TABLES TEMPORAIRES                  */
/* ##################################################################### */


/* ========================== PEUPLEMENT DE LA TABLE TEMPORAIRE ALBUMS ========================== */

COPY stg_albums
FROM '/imports/raw_albums_cleaned.csv'
DELIMITER ','
CSV HEADER
QUOTE '"'
ESCAPE '"';


/* ========================== PEUPLEMENT DE LA TABLE TEMPORAIRE ARTISTS ========================== */

COPY stg_artists
FROM '/imports/raw_artists_cleaned.csv'
DELIMITER ','
CSV HEADER
QUOTE '"'
ESCAPE '"';


/* ========================== PEUPLEMENT DE LA TABLE TEMPORAIRE TRACKS ========================== */

COPY stg_tracks
FROM '/imports/raw_tracks_cleaned.csv'
DELIMITER ','
CSV HEADER
QUOTE '"'
ESCAPE '"';


/* ========================== PEUPLEMENT DE LA TABLE TEMPORAIRE QUESTIONNAIRE ========================== */

COPY stg_questionnaire
FROM '/imports/questionnaire.csv'
DELIMITER ','
CSV HEADER
QUOTE '"'
ESCAPE '"';


/* ##################################################################### */
/*                    PEUPLEMENT DES TABLES DÉFINITIVES                  */
/* ##################################################################### */


ALTER TABLE album DISABLE TRIGGER ALL;


/* ========================== PEUPLEMENT DE LA TABLE ALBUM ========================== */

INSERT INTO album (
    album_id, album_title, 
    album_type, album_tracks, 
    album_information,
    album_favorites, 
    album_image_file, 
    album_listens, 
    album_tags,
    album_date_released, 
    album_date_created, 
    album_engineer, 
    album_producer
)
SELECT
    album_id::INT,
    album_title,
    album_type,
    0,
    album_information,
    NULLIF(album_favorites, '')::INT,
    album_image_file,
    NULLIF(album_listens, '')::INT,
    tags,
    TO_DATE(LEFT(album_date_released, 10), 'MM/DD/YYYY'),
    TO_DATE(LEFT(album_date_created, 10), 'MM/DD/YYYY'),
    album_engineer,
    album_producer
FROM stg_albums
ON CONFLICT (album_id) DO NOTHING;


/* ========================== PEUPLEMENT DE LA TABLE ARTIST ========================== */

INSERT INTO artist (
    artist_id, artist_name, 
    artist_bio, 
    artist_related_project,
    artist_favorites, 
    artist_image_file, 
    artist_active_year_begin,
    artist_active_year_end, 
    artist_tags, 
    artist_location,
    artist_website, 
    artist_latitude, 
    artist_longitude, 
    artist_associated_label
)
SELECT
    artist_id::INT,
    artist_name,
    artist_bio,
    artist_related_projects,
    NULLIF(artist_favorites, '')::INT,
    artist_image_file,
    TO_DATE(SPLIT_PART(NULLIF(artist_active_year_begin, 'NULL'), '.', 1), 'YYYY'),
    TO_DATE(SPLIT_PART(NULLIF(artist_active_year_end, 'NULL'), '.', 1), 'YYYY'),
    tags,
    artist_location,
    artist_website,
    NULLIF(artist_latitude, '')::FLOAT,
    NULLIF(artist_longitude, '')::FLOAT,
    artist_associated_labels
FROM stg_artists
ON CONFLICT (artist_id) DO NOTHING;


/* ========================== PEUPLEMENT DE LA TABLE TRACKS ========================== */

INSERT INTO tracks (
    track_id, 
    track_title, 
    track_duration, 
    track_genre,
    track_listens,
    track_favorite, 
    track_interest, 
    track_date_recorded, 
    track_date_created,
    track_composer, 
    track_lyricist, 
    track_tags, 
    track_artist_id,
    track_file, 
    track_disk_number, 
    track_bit_rate
)
SELECT
    track_id::INT,
    track_title,
    (SPLIT_PART(track_duration, ':', 1)::INT * 60) + SPLIT_PART(track_duration, ':', 2)::INT,
    track_genres,
    NULLIF(track_listens, '')::INT,
    NULLIF(track_favorites, '')::INT,
    NULLIF(track_interest, '')::FLOAT,
    TO_DATE(LEFT(track_date_recorded, 10), 'MM/DD/YYYY'),
    TO_DATE(LEFT(track_date_created, 10), 'MM/DD/YYYY'),
    track_composer,
    track_lyricist,
    tags,
    NULLIF(artist_id, '')::INT,
    track_file,
    NULLIF(track_disc_number, '')::INT,
    NULLIF(track_bit_rate, '')::FLOAT::INT
FROM stg_tracks
ON CONFLICT (track_id) DO NOTHING;


/* ========================== PEUPLEMENT DE LA TABLE ALBUM_ARTIST_TRACK ========================== */

INSERT INTO album_artist_track (album_id, artist_id, track_id)
SELECT DISTINCT
    t.album_id::INT,
    t.artist_id::INT,
    t.track_id::INT
FROM stg_tracks t
JOIN album a ON a.album_id = t.album_id::INT
JOIN artist ar ON ar.artist_id = t.artist_id::INT
WHERE t.album_id IS NOT NULL 
    AND t.artist_id IS NOT NULL 
    AND t.track_id IS NOT NULL
ON CONFLICT DO NOTHING;


/* ========================== PEUPLEMENT DE LA TABLE USERS ========================== */

INSERT INTO users (
	user_firstName,
    user_lastName,
    user_age,
    user_year_created,
    user_listening_duration,
    user_average_duration,
    user_status,
    user_favorite_hour,
    user_favorite_genre,
	user_favorite_language,
	user_favorite_platforms,
	user_gender,
	user_job
)
SELECT
	'Anonymous',
	'Anonymous',
    -- Convertir la tranche d'âge en un entier
    CASE 
        WHEN age_range LIKE '%17 ans%' THEN 16
        WHEN age_range LIKE '%18 - 25%' THEN 22
        WHEN age_range LIKE '%26- 35%' THEN 30
        WHEN age_range LIKE '%36 - 45%' THEN 40
        WHEN age_range LIKE '%46 - 55%' THEN 50
        WHEN age_range LIKE '%55 ans%' THEN 60
        ELSE 25
    END,

    -- Timestamp en date
    TO_DATE(LEFT(horodateur, 10), 'YYYY/MM/DD'),

    -- Convertir le temps d'écoute quotidien en entier
    CASE 
        WHEN daily_time LIKE '%30 minutes%' THEN 30
        WHEN daily_time LIKE '%1 heure%' THEN 60
        WHEN daily_time LIKE '%2 heures%' THEN 120
        WHEN daily_time LIKE '%4 heures%' THEN 240
        WHEN daily_time LIKE '%6 heures%' THEN 360
        ELSE 60
    END,

    -- Convertir la durée moyenne des morceaux préférés en entier
    CASE 
        WHEN track_duration_pref LIKE '%Moins de 1 minute%' THEN 60
        WHEN track_duration_pref LIKE '%1 minute 30 à 3 minutes%' THEN 135
        WHEN track_duration_pref LIKE '%3 minutes à 5 minutes%' THEN 240
        WHEN track_duration_pref LIKE '%Plus de 5 minutes%' THEN 350
        ELSE 180
    END,
    status,
    time_slots,
    genres,
    languages,
	platforms,
	gender,
	job_sector
FROM stg_questionnaire;

-- Activer les triggers
ALTER TABLE album ENABLE TRIGGER ALL;


/* ========================== FIX DES SÉQUENCES ========================== */

-- Réinitialiser les séquences SERIAL pour que les nouvelles insertions ne provoquent pas d'erreurs
SELECT setval('sae.users_user_id_seq', COALESCE((SELECT MAX(user_id)+1 FROM users), 1), false);
SELECT setval('sae.album_album_id_seq', COALESCE((SELECT MAX(album_id)+1 FROM album), 1), false);
SELECT setval('sae.artist_artist_id_seq', COALESCE((SELECT MAX(artist_id)+1 FROM artist), 1), false);
SELECT setval('sae.tracks_track_id_seq', COALESCE((SELECT MAX(track_id)+1 FROM tracks), 1), false);
SELECT setval('sae.users_user_id_seq', COALESCE((SELECT MAX(user_id)+1 FROM users), 1), false);
SELECT setval('sae.users_user_id_form_seq', COALESCE((SELECT MAX(user_id_form)+1 FROM users), 1), false);

-- Supprimer les tables temporaires
DROP TABLE IF EXISTS stg_albums;
DROP TABLE IF EXISTS stg_artists;
DROP TABLE IF EXISTS stg_tracks;
DROP TABLE IF EXISTS stg_questionnaire;