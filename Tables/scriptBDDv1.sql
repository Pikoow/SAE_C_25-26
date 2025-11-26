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
    user_favortie_genre    INT,
    user_id                INT    REFERENCES users(user_id)
);


/* ========================== TABLE ALBUM  ========================== */

CREATE TABLE album (
    album_id            SERIAL PRIMARY KEY,
    album_title         VARCHAR(50),
    album_type          VARCHAR(30),
    album_tracks        INT,
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
    track_publisher     VARCHAR(50),
    track_tags          VARCHAR(100),
    track_artist_id     INT,
    track_album_id      INT,
    track_rank_id       INT,
    track_feature_id    INT,
    track_file          VARCHAR(255),
    track_disk_number   INT,
    track_bit_rate      INT,
    album_id            INT    NULL REFERENCES album(album_id) ON DELETE SET NULL
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
    playlist_num_tracks INT,
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
    artist_name              VARCHAR(20),
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
    artiste_social_score     INT,
    user_id                  INT    REFERENCES users(user_id)
);


/* ========================== TABLE SCORE ARTIST  ========================== */

CREATE TABLE score_artist (
    id_rank_artist                     SERIAL PRIMARY KEY,
    social_features_artist_discovery   FLOAT,
    social_features_artist_familiarity FLOAT,
    social_features_artist_hotnesss    FLOAT,
    ranks_artist_discovery_rank        INT,
    ranks_artist_familiarity_rank      INT,
    ranks_artist_hotttnesss_rank       INT,
    artist_id                          INT    REFERENCES artist(artist_id)
);


/* ========================== TABLE ALBUM ARTIST  ========================== */

CREATE TABLE album_artist (
    album_id  INT REFERENCES album(album_id)   ON DELETE CASCADE,
    artist_id INT REFERENCES artist(artist_id) ON DELETE CASCADE,
    PRIMARY KEY (album_id, artist_id)
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


/* ##################################################################### */
/*                                 VUES                                  */
/* ##################################################################### */

/* ========================== VUE ALL TRACKS INFORMATIONS  ========================== */

CREATE VIEW all_tracks_informations AS
    SELECT t.track_id,
        t.track_title,
        t.track_duration,
        t.track_genre_top,
        t.track_genre,
        t.track_listens,
        t.track_favorite,
        t.track_interest,
        t.track_tags,
        a.album_title,
        a.album_image_file,
        a.album_date_released,
        art.artist_name,
        s.social_features_song_hotness AS hotness,
        s.social_features_song_currency AS currency
    FROM tracks t
    JOIN album a ON t.album_id = a.album_id
    JOIN artist art ON t.track_artist_id = art.artist_id
    JOIN score_track s ON t.track_id = s.track_id
;


/* ========================== VUE ALL ALBUM INFORMATIONS  ========================== */

CREATE VIEW all_album_informations AS
    SELECT 
        alb.album_id,
        alb.album_title,
        alb.album_type,
        alb.album_tracks,
        alb.album_listens,
        alb.album_favorites,
        alb.album_image_file,
        alb.album_date_released,
        STRING_AGG(art.artist_name, ', ') AS artists
    FROM album alb
    JOIN album_artist aa ON aa.album_id = alb.album_id
    JOIN artist art ON art.artist_id = aa.artist_id
    GROUP BY alb.album_id
;


/* ##################################################################### */
/*                               TRIGGERS                                */
/* ##################################################################### */

CREATE OR REPLACE FUNCTION update_album_track_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE album
        SET album_tracks = album_tracks + 1
        WHERE album_id = NEW.track_album_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE album
        SET album_tracks = album_tracks - 1
        WHERE album_id = OLD.track_album_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER track_album_insert
AFTER INSERT ON tracks
FOR EACH ROW
WHEN (NEW.track_album_id IS NOT NULL)
EXECUTE FUNCTION update_album_track_count();


CREATE TRIGGER track_album_delete
AFTER DELETE ON tracks
FOR EACH ROW
WHEN (OLD.track_album_id IS NOT NULL)
EXECUTE FUNCTION update_album_track_count();


CREATE OR REPLACE FUNCTION update_playlist_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE playlist
        SET playlist_num_tracks = playlist_num_tracks + 1
        WHERE playlist_id = NEW.playlist_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE playlist
        SET playlist_num_tracks = playlist_num_tracks - 1
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