SET SCHEMA 'sae';

 -- 1. Table temporaire pour les albums
CREATE TABLE IF NOT EXISTS stg_albums (
    album_id text, album_comments text, album_date_created text, album_date_released text,
    album_engineer text, album_favorites text, album_handle text, album_image_file text,
    album_images text, album_information text, album_listens text, album_producer text,
    album_title text, album_tracks text, album_type text, album_url text,
    artist_name text, artist_url text, tags text
);

-- 2. Table temporaire pour les artistes
CREATE TABLE IF NOT EXISTS stg_artists (
    artist_id text, artist_active_year_begin text, artist_active_year_end text,
    artist_associated_labels text, artist_bio text, artist_comments text,
    artist_contact text, artist_date_created text, artist_donation_url text,
    artist_favorites text, artist_flattr_name text, artist_handle text,
    artist_image_file text, artist_images text, artist_latitude text,
    artist_location text, artist_longitude text, artist_members text,
    artist_name text, artist_paypal_name text, artist_related_projects text,
    artist_url text, artist_website text, artist_wikipedia_page text, tags text
);

-- 3. Table temporaire pour les tracks
CREATE TABLE IF NOT EXISTS stg_tracks (
    track_id text, album_id text, album_title text, album_url text,
    artist_id text, artist_name text, artist_url text, artist_website text,
    license_image_file text, license_image_file_large text, license_parent_id text,
    license_title text, license_url text, tags text, track_bit_rate text,
    track_comments text, track_composer text, track_copyright_c text,
    track_copyright_p text, track_date_created text, track_date_recorded text,
    track_disc_number text, track_duration text, track_explicit text,
    track_explicit_notes text, track_favorites text, track_file text,
    track_genres text, track_image_file text, track_information text,
    track_instrumental text, track_interest text, track_language_code text,
    track_listens text, track_lyricist text, track_number text,
    track_publisher text, track_title text, track_url text
);

-- 4. Table temporaire pour les questionnaires
CREATE TABLE IF NOT EXISTS stg_questionnaire (
    horodateur text,
    consent text,
    use_streaming text,
    platforms text,
    daily_time text,
    genres text,
    devices text,
    context text,
    frequency text,
    time_slots text,
    languages text,
    follow_releases text,
    discovery_habits text,
    change_styles text,
    track_duration_pref text,
    lyrics_pref text,
    continue_form text,
    age_range text,
    gender text,
    status text,
    job_sector text
);

/* Importation des csv dans pgAdmin */

-- Désactiver temporairement les triggers
ALTER TABLE album DISABLE TRIGGER ALL;

/* ========================== 1. Population d'albums  ========================== */
INSERT INTO album (
    album_id, album_title, album_type, album_tracks, album_information,
    album_favorites, album_image_file, album_listens, album_tags,
    album_date_released, album_date_created, album_engineer, album_producer
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

/* ========================== 2. Population des artistes ========================== */
INSERT INTO artist (
    artist_id, artist_name, artist_bio, artist_related_project,
    artist_favorites, artist_image_file, artist_active_year_begin,
    artist_active_year_end, artist_tags, artist_location,
    artist_website, artist_latitude, artist_longitude, artist_associated_label
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

/* ========================== 3. Population des tracks ========================== */
INSERT INTO tracks (
    track_id, track_title, track_duration, track_genre, track_listens,
    track_favorite, track_interest, track_date_recorded, track_date_created,
    track_composer, track_lyricist, track_tags, track_artist_id,
    track_file, track_disk_number, track_bit_rate
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

/* ========================== 4. Population d'albums_artists ========================== */
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

/* ========================== 5. Population des utilisateurs ========================== */
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

/* ========================== 5. Fixer les sequences ========================== */

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