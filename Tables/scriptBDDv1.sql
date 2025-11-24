DROP SCHEMA IF EXISTS sae CASCADE;
CREATE SCHEMA IF NOT EXISTS sae;
SET SCHEMA 'sae';

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

CREATE TABLE favorite (
    favorite_id            SERIAL PRIMARY KEY,
    user_favorite_tracks   INT,
    user_favorite_album    INT,
    user_favorite_artist   INT,
    user_favorite_language VARCHAR(50),
    user_favortie_genre    INT,
    user_id                INT    REFERENCES users(user_id)
);

CREATE TABLE album (
    album_id            SERIAL PRIMARY KEY,
    album_title         VARCHAR(50)
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

CREATE TABLE score_track (
    id_rank_track                 SERIAL PRIMARY KEY,
    ranks_song_currency_rank      INT,
    ranks_song_hotness_rank       INT,
    social_features_song_currency FLOAT,
    social_features_song_hotness  FLOAT,
    track_id                      INT REFERENCES tracks(track_id)
);

CREATE TABLE users_track (
    user_id  INT REFERENCES users(user_id),
    track_id INT REFERENCES tracks(track_id),
    PRIMARY KEY (user_id, track_id)
);

CREATE TABLE playlist (
    playlist_id         SERIAL PRIMARY KEY,
    playlist_name       VARCHAR(50),
    playlist_num_tracks INT,
    -- list_track          LIST,
    user_id             INT    REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE playlist_track (
    playlist_id INT REFERENCES playlist(playlist_id) ON DELETE CASCADE,
    track_id    INT REFERENCES tracks(track_id)      ON DELETE CASCADE,
    PRIMARY KEY (playlist_id, track_id)
);

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
    -- artist_latitude       FLOAT,
    -- artist_longitude      FLOAT,
    artist_associated_label  VARCHAR(200),
    id_rank_artist           INT,
    artiste_social_score     INT,
    user_id                  INT    REFERENCES users(user_id)
);

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

CREATE TABLE album_artist (
    album_id  INT REFERENCES album(album_id)   ON DELETE CASCADE,
    artist_id INT REFERENCES artist(artist_id) ON DELETE CASCADE,
    PRIMARY KEY (album_id, artist_id)
);

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
