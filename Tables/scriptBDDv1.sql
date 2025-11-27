DROP SCHEMA IF EXISTS sae CASCADE;
CREATE SCHEMA IF NOT EXISTS sae;
SET SCHEMA 'sae';

/* ##################################################################### */
/*                                TABLES                                 */
/* ##################################################################### */

/* ========================== TABLE USERS  ========================== */

CREATE TABLE users (
    user_id                  SERIAL PRIMARY KEY,
    user_firstName           VARCHAR(20),
    user_lastName            VARCHAR(20),
    user_age                 INT,
    user_year_created        DATE,
    user_image               VARCHAR(100),
    user_location            VARCHAR(50),
    -- user_latitude         FLOAT,
    -- user_longitude        FLOAT,
    user_listening_duration  INT,
    user_average_duration    INT,
    user_status              VARCHAR(50),
    user_average_listenedBPM FLOAT,
    user_favorite_hour       VARCHAR(50),
    user_favorite_genre      VARCHAR(50),
    user_average_valence     FLOAT,
    user_playlist_Id         int,
    user_tags                VARCHAR(50),
    user_password            VARCHAR(50),
    user_mail                VARCHAR(50),
    user_phoneNumber         VARCHAR(10),
    user_id_form             SERIAL UNIQUE
);

/* ========================== TABLE FAVORITE  ========================== */

CREATE TABLE favorite (
    favorite_id            SERIAL PRIMARY KEY,
    user_favorite_tracks   INT,
    user_favorite_album    INT,
    user_favorite_artist   INT,
    user_favorite_language VARCHAR(50),
    user_favorite_genre    INT,
    user_id                INT    REFERENCES users(user_id)
);

/* ========================== TABLE ALBUM  ========================== */

CREATE TABLE album (
    album_id            SERIAL PRIMARY KEY,
    album_title         VARCHAR(50),
    album_type          VARCHAR(30),
    album_tracks        INT DEFAULT 0,
    album_information   VARCHAR(255),
    album_favorites     INT,
    album_image_file    VARCHAR(255),
    album_listens       INT,
    album_tags          VARCHAR(100),
    album_date_released DATE,
    album_date_created  DATE,
    album_engineer      VARCHAR(50),
    album_producer      VARCHAR(50)
);

/* ========================== TABLE TRACKS  ========================== */

CREATE TABLE tracks (
    track_id            SERIAL PRIMARY KEY,
    track_title         VARCHAR(200),
    track_duration      INT,
    track_genre_top     VARCHAR(30),
    track_genre         VARCHAR(255),
    track_listens       INT,
    track_favorite      INT,
    track_interest      FLOAT,
    track_date_recorded DATE,
    track_date_created  DATE,
    track_composer      VARCHAR(50),
    track_lyricist      VARCHAR(50),
    track_tags          VARCHAR(100),
    track_artist_id     INT,
    track_rank_id       INT,
    track_feature_id    INT,
    track_file          VARCHAR(255),
    track_disk_number   INT,
    track_bit_rate      INT
);

/* ========================== TABLE SCORE TRACK  ========================== */

CREATE TABLE score_track (
    id_rank_track                 SERIAL PRIMARY KEY,
    ranks_song_currency_rank      INT,
    ranks_song_hotness_rank       INT,
    social_features_song_currency FLOAT,
    social_features_song_hotness  FLOAT,
    track_id                      INT REFERENCES tracks(track_id)
);

/* ========================== TABLE USERS TRACK  ========================== */

CREATE TABLE users_track (
    user_id  INT REFERENCES users(user_id),
    track_id INT REFERENCES tracks(track_id),
    PRIMARY KEY (user_id, track_id)
);

/* ========================== TABLE PLAYLIST  ========================== */

CREATE TABLE playlist (
    playlist_id         SERIAL PRIMARY KEY,
    playlist_name       VARCHAR(50),
    playlist_num_tracks INT DEFAULT 0,
    -- list_track          LIST,
    user_id             INT    REFERENCES users(user_id) ON DELETE CASCADE
);

/* ========================== TABLE PLAYLIST TRACK  ========================== */

CREATE TABLE playlist_track (
    playlist_id INT REFERENCES playlist(playlist_id) ON DELETE CASCADE,
    track_id    INT REFERENCES tracks(track_id)      ON DELETE CASCADE,
    PRIMARY KEY (playlist_id, track_id)
);

/* ========================== TABLE ARTIST  ========================== */

CREATE TABLE artist (
    artist_id                SERIAL PRIMARY KEY,
    artist_password          VARCHAR(30),
    artist_name              VARCHAR(200),
    artist_bio               VARCHAR(200),
    artist_related_project   VARCHAR(255),
    artist_favorites         INT,
    artist_image_file        VARCHAR(200),
    artist_active_year_begin DATE,
    artist_active_year_end   DATE,
    artist_tags              VARCHAR(200),
    artist_location          VARCHAR(200),
    artist_website           VARCHAR(200),
    artist_latitude          FLOAT,
    artist_longitude         FLOAT,
    artist_associated_label  VARCHAR(200),
    id_rank_artist           INT,
    artist_social_score      INT,
    user_id                  INT    REFERENCES users(user_id)
);

/* ========================== TABLE SCORE ARTIST  ========================== */

CREATE TABLE score_artist (
    id_rank_artist                     SERIAL PRIMARY KEY,
    social_features_artist_discovery   FLOAT,
    social_features_artist_familiarity FLOAT,
    social_features_artist_hotness     FLOAT,
    ranks_artist_discovery_rank        INT,
    ranks_artist_familiarity_rank      INT,
    ranks_artist_hotness_rank          INT,
    artist_id                          INT    REFERENCES artist(artist_id)
);

/* ========================== TABLE GENRE  ========================== */

CREATE TABLE genre (
    genre_id        SERIAL UNIQUE PRIMARY KEY,
    genre_parent_id INT,
    genre_title     VARCHAR(200),
    genre_handle    VARCHAR(200),
    genre_color     VARCHAR(200),
    low_level       BOOLEAN,
    tracks          INT,
    track_id        INT    REFERENCES tracks(track_id)
);

/* ========================== TABLE PUBLISHER  ========================== */

CREATE TABLE publisher (
    publisher_id   SERIAL PRIMARY KEY,
    publisher_name VARCHAR(200)
);

/* ========================== TERNARY LINK TABLES ========================== */

CREATE TABLE album_artist_track (
    album_id  INT    REFERENCES album(album_id)   ON DELETE CASCADE,
    artist_id INT    REFERENCES artist(artist_id) ON DELETE CASCADE,
    track_id  INT    REFERENCES tracks(track_id)  ON DELETE CASCADE,
    contribution_role VARCHAR(100), -- optional: e.g. 'main', 'feat', 'producer'
    PRIMARY KEY (album_id, artist_id, track_id)
);

CREATE TABLE artist_publisher_track (
    artist_id    INT    REFERENCES artist(artist_id) ON DELETE CASCADE,
    publisher_id INT    REFERENCES publisher(publisher_id) ON DELETE CASCADE,
    track_id     INT    REFERENCES tracks(track_id)    ON DELETE CASCADE,
    publisher_role VARCHAR(100), -- optional: e.g. 'label', 'distributor'
    PRIMARY KEY (artist_id, publisher_id, track_id)
);

/* ##################################################################### */
/*                                 VUES                                  */
/* ##################################################################### */


CREATE OR REPLACE VIEW tracks_features AS
    SELECT
        t.track_id,
        t.track_title,
        t.track_duration,
        t.track_genre_top,
        t.track_genre,
        t.track_tags,
        t.track_listens,
        t.track_favorite,
        t.track_interest,
        t.track_date_recorded,
        t.track_date_created,
        t.track_composer,
        t.track_lyricist,
        t.track_bit_rate,
        t.track_disk_number,
        STRING_AGG(DISTINCT a.album_id::text, ',') AS album_ids,
        STRING_AGG(DISTINCT a.album_title, ', ') AS album_titles,
        STRING_AGG(DISTINCT ar.artist_name, ', ') AS artist_names,
        STRING_AGG(DISTINCT ar.artist_id::text, ',') AS artist_ids,
        AVG(sa.social_features_artist_hotness) AS avg_artist_hotness,
        AVG(sa.social_features_artist_familiarity) AS avg_artist_familiarity
    FROM tracks t
    LEFT JOIN album_artist_track aat ON aat.track_id = t.track_id
    LEFT JOIN album a ON a.album_id = aat.album_id
    LEFT JOIN artist ar ON ar.artist_id = aat.artist_id
    LEFT JOIN score_artist sa ON sa.artist_id = ar.artist_id
    GROUP BY t.track_id
;


CREATE OR REPLACE VIEW album_features AS
    SELECT 
        alb.album_id,
        alb.album_title,
        alb.album_type,
        alb.album_tracks,
        alb.album_listens,
        alb.album_favorites,
        alb.album_image_file,
        alb.album_date_released,
        alb.album_tags,
        STRING_AGG(DISTINCT art.artist_name, ', ') AS artists
    FROM album alb
    LEFT JOIN album_artist_track aat ON aat.album_id = alb.album_id
    LEFT JOIN artist art ON art.artist_id = aat.artist_id
    GROUP BY alb.album_id
;


CREATE OR REPLACE VIEW artist_features AS
    SELECT
        ar.artist_id,
        ar.artist_name,
        ar.artist_tags,
        ar.artist_location,
        ar.artist_associated_label,
        ar.artist_active_year_begin,
        ar.artist_active_year_end,
        ar.artist_favorites,
        AVG(sa.social_features_artist_hotness) AS hotness,
        AVG(sa.social_features_artist_familiarity) AS familiarity,
        AVG(sa.social_features_artist_discovery) AS discovery,
        COUNT(DISTINCT aat.track_id) AS num_tracks_associated,
        COUNT(DISTINCT apt.publisher_id) AS num_publishers
    FROM artist ar
    LEFT JOIN score_artist sa ON sa.artist_id = ar.artist_id
    LEFT JOIN album_artist_track aat ON aat.artist_id = ar.artist_id
    LEFT JOIN artist_publisher_track apt ON apt.artist_id = ar.artist_id
    GROUP BY ar.artist_id
;

/* ========================== VIEW USER FEATURES  ========================== */

CREATE OR REPLACE VIEW user_features AS
    SELECT
        u.user_id,
        u.user_firstName,
        u.user_lastName,
        u.user_age,
        u.user_location,
        u.user_favorite_genre,
        u.user_average_listenedBPM,
        u.user_average_duration,
        u.user_average_valence,
        u.user_favorite_hour,
        f.user_favorite_tracks,
        f.user_favorite_album,
        f.user_favorite_artist,
        f.user_favorite_language
    FROM users u
    LEFT JOIN favorite f ON f.user_id = u.user_id
;

/* ##################################################################### */
/*                               TRIGGERS                                */
/* ##################################################################### */

CREATE OR REPLACE FUNCTION update_album_track_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE album
        SET album_tracks = COALESCE(album_tracks, 0) + 1
        WHERE album_id = NEW.album_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE album
        SET album_tracks = GREATEST(COALESCE(album_tracks, 0) - 1, 0)
        WHERE album_id = OLD.album_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER album_artist_track_insert
AFTER INSERT ON album_artist_track
FOR EACH ROW
EXECUTE FUNCTION update_album_track_count();

CREATE TRIGGER album_artist_track_delete
AFTER DELETE ON album_artist_track
FOR EACH ROW
EXECUTE FUNCTION update_album_track_count();


CREATE OR REPLACE FUNCTION update_playlist_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE playlist
        SET playlist_num_tracks = COALESCE(playlist_num_tracks, 0) + 1
        WHERE playlist_id = NEW.playlist_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE playlist
        SET playlist_num_tracks = GREATEST(COALESCE(playlist_num_tracks, 0) - 1, 0)
        WHERE playlist_id = OLD.playlist_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER playlist_track_insert
AFTER INSERT ON playlist_track
FOR EACH ROW EXECUTE FUNCTION update_playlist_count();

CREATE TRIGGER playlist_track_delete
AFTER DELETE ON playlist_track
FOR EACH ROW EXECUTE FUNCTION update_playlist_count();


CREATE OR REPLACE FUNCTION set_album_created_date()
RETURNS TRIGGER AS $$
BEGIN
    NEW.album_date_created := CURRENT_DATE;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER album_set_date
BEFORE INSERT ON album
FOR EACH ROW EXECUTE FUNCTION set_album_created_date();


CREATE OR REPLACE FUNCTION set_track_created_date()
RETURNS TRIGGER AS $$
BEGIN
    NEW.track_date_created := CURRENT_DATE;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER track_set_date
BEFORE INSERT ON tracks
FOR EACH ROW EXECUTE FUNCTION set_track_created_date();