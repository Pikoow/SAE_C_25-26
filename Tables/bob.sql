SET SCHEMA 'sae';

-- 1. Staging Table for Albums
CREATE TABLE IF NOT EXISTS stg_albums (
    album_id text, album_comments text, album_date_created text, album_date_released text,
    album_engineer text, album_favorites text, album_handle text, album_image_file text,
    album_images text, album_information text, album_listens text, album_producer text,
    album_title text, album_tracks text, album_type text, album_url text,
    artist_name text, artist_url text, tags text
);

-- 2. Staging Table for Artists
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

-- 3. Staging Table for Tracks
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

SET SCHEMA 'sae';

-- Disable triggers temporarily to prevent double-counting tracks during bulk insert
ALTER TABLE album DISABLE TRIGGER ALL;

/* ========================== 1. POPULATE ALBUM ========================== */
INSERT INTO album (
    album_id, album_title, album_type, album_tracks, album_information,
    album_favorites, album_image_file, album_listens, album_tags,
    album_date_released, album_date_created, album_engineer, album_producer
)
SELECT
    album_id::INT,
    album_title,
    album_type,
    0, -- We set this to 0 initially. We will calculate it correctly later using the link table.
    album_information,
    NULLIF(album_favorites, '')::INT,
    album_image_file,
    NULLIF(album_listens, '')::INT,
    tags,
    -- Handle Date Formats (MM/DD/YYYY)
    TO_DATE(LEFT(album_date_released, 10), 'MM/DD/YYYY'),
    TO_DATE(LEFT(album_date_created, 10), 'MM/DD/YYYY'),
    album_engineer,
    album_producer
FROM stg_albums
ON CONFLICT (album_id) DO NOTHING;

/* ========================== 2. POPULATE ARTIST ========================== */
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
    -- Handle "2006.0" format for years
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

/* ========================== 3. POPULATE TRACKS ========================== */
INSERT INTO tracks (
    track_id, track_title, track_duration, track_genre, track_listens,
    track_favorite, track_interest, track_date_recorded, track_date_created,
    track_composer, track_lyricist, track_tags, track_artist_id,
    track_file, track_disk_number, track_bit_rate
)
SELECT
    track_id::INT,
    track_title,
    -- Convert "MM:SS" string to Integer (Seconds)
    (SPLIT_PART(track_duration, ':', 1)::INT * 60) + SPLIT_PART(track_duration, ':', 2)::INT,
    track_genres, -- Storing the raw JSON/String provided in CSV
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

/* ========================== 4. POPULATE LINK TABLE (Album-Artist-Track) ========================== */
-- This logic creates the relationships that are implicit in the raw_tracks CSV
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

-- Re-enable triggers
ALTER TABLE album ENABLE TRIGGER ALL;

/* ========================== 5. FIX SEQUENCES AND COUNTS ========================== */

-- Update the album track counts based on what we just inserted into the link table
UPDATE album a
SET album_tracks = (
    SELECT COUNT(*) 
    FROM album_artist_track aat 
    WHERE aat.album_id = a.album_id
);

-- Reset the SERIAL sequences so new inserts don't crash
SELECT setval('sae.users_user_id_seq', COALESCE((SELECT MAX(user_id)+1 FROM users), 1), false);
SELECT setval('sae.album_album_id_seq', COALESCE((SELECT MAX(album_id)+1 FROM album), 1), false);
SELECT setval('sae.artist_artist_id_seq', COALESCE((SELECT MAX(artist_id)+1 FROM artist), 1), false);
SELECT setval('sae.tracks_track_id_seq', COALESCE((SELECT MAX(track_id)+1 FROM tracks), 1), false);

-- Clean up staging tables
DROP TABLE IF EXISTS stg_albums;
DROP TABLE IF EXISTS stg_artists;
DROP TABLE IF EXISTS stg_tracks;