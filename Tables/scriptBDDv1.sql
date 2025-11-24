DROP SCHEMA IF EXISTS sae CASCADE;
CREATE SCHEMA IF NOT EXISTS sae;
SET SCHEMA 'sae';

CREATE TABLE Users (
    user_id       SERIAL Primary key,
    user_firstName VARCHAR(20),
    user_lastName VARCHAR(20),
    user_age int,
    user_year_created date,
    user_image VARCHAR(100),
    user_location            VARCHAR(50),
    user_latitude            FLOAT,
    user_longitude           FLOAT,
    user_duree_ecoute        INT,
    user_average_duration    INT,
    user_status              VARCHAR(50),
    user_average_listenedBPM FLOAT,
    user_average_valence     FLOAT,
    user_playlist_Id         int,
    user_tags                VARCHAR(50),
    user_password            VARCHAR(50),
    user_mail                VARCHAR(50),
    user_phoneNumber         VARCHAR(10),
    user_id_form             SERIAL UNIQUE
);

create table favorite(
  favorite_id serial Primary key,
  user_id INT REFERENCES users(user_id),
  user_favorite_tracks integer,
  user_favorite_album integer,
  user_favorite_artist integer,
  user_favorite_language VARCHAR(50),
  user_favortie_genre integer,
  user_favorite_hour VARCHAR(50)
);

create table Album(
  album_id serial primary key,
  album_title VARCHAR(200),
  album_type VARCHAR(200),
  album_tracks int,
  album_information VARCHAR(200),
  album_favorites int,
  album_image_file VARCHAR(200),
  album_listens int,
  album_tags VARCHAR(200),
  album_date_released date,
  album_date_created date,
  album_engineer VARCHAR(200),
  album_producer VARCHAR(200)
);

create table tracks(
  track_id serial primary key,
  track_title varchar(200),
  track_duration int,
  track_genre_top varchar(50),
  track_genre varchar(50),
  track_listens int,
  track_favorite int,
  track_interest float,
  track_date_recorded date,
  track_date_created date,
  track_composer varchar(50),
  track_lyricist varchar(50),
  track_publisher varchar(50),
  track_tags varchar(200),
  track_artist_id int,
  track_album_id int,
  track_rank_id int,
  track_feature_id int,
  track_file varchar(200),
  track_disk_number int,
  track_bit_rate int,
  album_id INT NULL REFERENCES Album(album_id) ON DELETE SET NULL
);

create table score_track(
  id_rank_track serial primary key,
  ranks_song_currency_rank int,
  ranks_song_hotttnesss_rank int ,
  social_features_song_currency float,
  social_features_song_hotttnesss float,
  track_id int references tracks(track_id)
);

create table users_track(
  user_id int references users(user_id),
  track_id int references tracks(track_id),
  PRIMARY KEY (user_id, track_id)
);

CREATE TABLE playlist (
  playlist_id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
  playlist_name VARCHAR(50),
  playlist_num_tracks int
);

CREATE TABLE playlist_track (
  playlist_id INT REFERENCES playlist(playlist_id) ON DELETE CASCADE,
  track_id INT REFERENCES tracks(track_id) ON DELETE CASCADE,
  PRIMARY KEY (playlist_id, track_id)
);

create table artist (
  artist_id serial primary key,
  artist_name VARCHAR(200),
  artist_bio VARCHAR(200),
  artist_related_project VARCHAR(200),
  artistes_favoris int,
  artist_image_file VARCHAR(200),
  artist_active_year_begin date,
  artist_active_year_end date,
  artist_tags VARCHAR(200),
  artist_location VARCHAR(200),
  artist_website VARCHAR(200),
  artist_latitude float,
  artist_longitude float,
  artist_associated_label VARCHAR(200),
  id_rank_artist int,
  artiste_social_score int,
  user_id int references users(user_id)
);

create table score_artist(
  id_rank_artist serial primary key,
  social_features_artist_discovery float,
  social_features_artist_familiarity float,
  social_features_artist_hotttnesss float,
  ranks_artist_discovery_rank int,
  ranks_artist_familiarity_rank int,
  ranks_artist_hotttnesss_rank int,
  artist_id int references artist(artist_id)
);



CREATE TABLE album_artist (
  album_id INT REFERENCES album(album_id) ON DELETE CASCADE,
  artist_id INT REFERENCES artist(artist_id) ON DELETE CASCADE,
  PRIMARY KEY (album_id, artist_id)
);

create table genre(
  genre_id serial unique primary key,
  genre_parent_id int,
  genre_title VARCHAR(200),
  genre_handle VARCHAR(200),
  genre_color VARCHAR(200),
  low_level bool,
  tracks int,
  track_id references tracks(track_id)
);
