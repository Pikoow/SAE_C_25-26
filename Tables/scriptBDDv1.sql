DROP SCHEMA IF EXISTS sae CASCADE;
CREATE SCHEMA IF NOT EXISTS sae;
SET SCHEMA 'sae';

/* ##################################################################### */
/*                                TABLES                                 */
/* ##################################################################### */

/* ========================== TABLE USERS  ========================== */

CREATE TABLE users (
    user_id                  SERIAL PRIMARY KEY,
    user_firstName           VARCHAR(65000),
    user_lastName            VARCHAR(65000),
    user_age                 INT,
    user_year_created        DATE,
    user_image               VARCHAR(65000),
    user_location            VARCHAR(65000),
    user_listening_duration  INT,
    user_average_duration    INT,
    user_status              VARCHAR(65000),
    user_average_listenedBPM FLOAT,
    user_favorite_hour       VARCHAR(65000),
    user_favorite_genre      VARCHAR(65000),
    user_favorite_language   VARCHAR(65000),
	user_favorite_platforms  VARCHAR(65000),
    user_gender              VARCHAR(65000),
	user_job                 VARCHAR(65000),
    user_average_valence     FLOAT,
    user_playlist_Id         int,
    user_tags                VARCHAR(65000),
    user_password            VARCHAR(65000),
    user_mail                VARCHAR(65000),
    user_phoneNumber         VARCHAR(10),
    user_id_form             SERIAL UNIQUE
);


/* ========================== TABLE user_fake  ========================== */

CREATE TABLE user_fake (
    user_id INT PRIMARY KEY,
    user_age INT,
    user_listening_duration INT,
    user_average_duration TEXT,
    user_status TEXT,
    user_favorite_hour TEXT,
    user_favorite_genre TEXT,
    user_favorite_languages TEXT,
    user_favorite_platforms TEXT,
    user_gender TEXT,
    user_job TEXT,
    user_tags TEXT,
    listened_tracks TEXT
);

/* ========================== TABLE FAVORITE  ========================== */

CREATE TABLE favorite (
    favorite_id            SERIAL PRIMARY KEY,
    user_favorite_tracks   INT,
    user_favorite_album    INT,
    user_favorite_artist   INT,
    user_favorite_language VARCHAR(65000),
    user_favorite_genre    INT,
    user_id                INT    REFERENCES users(user_id)
);

/* ========================== TABLE ALBUM  ========================== */

CREATE TABLE album (
    album_id            INT PRIMARY KEY,
    album_handle        VARCHAR(65000),
    album_title         VARCHAR(65000),
    album_type          VARCHAR(65000),
    album_tracks        INT DEFAULT 0,
    album_information   VARCHAR(65000),
    album_favorites     INT,
    album_image_file    VARCHAR(65000),
    album_listens       INT,
    album_tags          VARCHAR(65000),
    album_date_released DATE,
    album_date_created  DATE,
    album_engineer      VARCHAR(65000),
    album_producer      VARCHAR(65000),
    album_keynouns      JSONB,
    album_keynames      JSONB
);

/* ========================== TABLE ARTIST  ========================== */

CREATE TABLE artist (
    artist_id                INT PRIMARY KEY,
    artist_password          VARCHAR(65000),
    artist_name              VARCHAR(65000),
    artist_bio               VARCHAR(65000),
    artist_related_project   VARCHAR(65000),
    artist_favorites         INT,
    artist_image_file        VARCHAR(65000),
    artist_active_year_begin DATE,
    artist_active_year_end   DATE,
    artist_tags              VARCHAR(65000),
    artist_location          VARCHAR(65000),
    artist_website           VARCHAR(65000),
    artist_latitude          FLOAT,
    artist_longitude         FLOAT,
    artist_associated_label  VARCHAR(65000),
    id_rank_artist           INT,
    user_id                  INT    REFERENCES users(user_id),
    artist_handle VARCHAR(255),
    artist_members VARCHAR(255),
    artist_date_created DATE
);

/* ========================== TABLE TRACKS  ========================== */


CREATE TABLE tracks (
    track_id            INT PRIMARY KEY,
    track_title         VARCHAR(65000),
    track_duration      INT,
    track_genre_top     VARCHAR(65000),
    track_genre         VARCHAR(65000),
    track_listens       INT,
    track_favorite      INT,
    track_interest      FLOAT,
    track_date_recorded DATE,
    track_date_created  DATE,
    track_composer      VARCHAR(65000),
    track_lyricist      VARCHAR(65000),
    track_tags          VARCHAR(65000),
    track_artist_id     INT,
    track_rank_id       INT,
    track_feature_id    INT,
    track_file          VARCHAR(65000),
    track_image_file    VARCHAR(65000),
    track_disk_number   INT,
    track_bit_rate      INT
);


/* ========================== TABLE song_social_score  ========================== */

CREATE TABLE song_social_score (
    sss_id SERIAL PRIMARY KEY,
    track_id INT UNIQUE REFERENCES tracks(track_id),
    social_features_song_currency DOUBLE PRECISION,
    social_features_song_hottness DOUBLE PRECISION
);


/* ========================== TABLE song_rank  ========================== */

CREATE TABLE song_rank (
    sr_id SERIAL PRIMARY KEY,
    track_id INT UNIQUE REFERENCES tracks(track_id),
    ranks_song_currency_rank DOUBLE PRECISION,
    ranks_song_hottness_rank DOUBLE PRECISION
);


/* ========================== TABLE audio  ========================== */

CREATE TABLE audio (
    track_id INT PRIMARY KEY REFERENCES tracks(track_id) ON DELETE CASCADE,
    audio_features_accousticness VARCHAR(20000),
    audio_features_danceability VARCHAR(20000),
    audio_features_energy VARCHAR(20000),
    audio_features_instrumentalness VARCHAR(20000),
    audio_features_liveness VARCHAR(20000),
    audio_features_speechiness VARCHAR(20000),
    audio_features_tempo VARCHAR(20000),
    audio_features_valence VARCHAR(20000)
);



/* ========================== TABLE temp_features  ========================== */

CREATE TABLE temporal_features (
    tf_id SERIAL PRIMARY KEY,
    track_id INT UNIQUE REFERENCES tracks(track_id),
    temporal_features_000 DOUBLE PRECISION,
    temporal_features_001 DOUBLE PRECISION,
    temporal_features_002 DOUBLE PRECISION,
    temporal_features_003 DOUBLE PRECISION,
    temporal_features_004 DOUBLE PRECISION,
    temporal_features_005 DOUBLE PRECISION,
    temporal_features_006 DOUBLE PRECISION,
    temporal_features_007 DOUBLE PRECISION,
    temporal_features_008 DOUBLE PRECISION,
    temporal_features_009 DOUBLE PRECISION,
    temporal_features_010 DOUBLE PRECISION,
    temporal_features_011 DOUBLE PRECISION,
    temporal_features_012 DOUBLE PRECISION,
    temporal_features_013 DOUBLE PRECISION,
    temporal_features_014 DOUBLE PRECISION,
    temporal_features_015 DOUBLE PRECISION,
    temporal_features_016 DOUBLE PRECISION,
    temporal_features_017 DOUBLE PRECISION,
    temporal_features_018 DOUBLE PRECISION,
    temporal_features_019 DOUBLE PRECISION,
    temporal_features_020 DOUBLE PRECISION,
    temporal_features_021 DOUBLE PRECISION,
    temporal_features_022 DOUBLE PRECISION,
    temporal_features_023 DOUBLE PRECISION,
    temporal_features_024 DOUBLE PRECISION,
    temporal_features_025 DOUBLE PRECISION,
    temporal_features_026 DOUBLE PRECISION,
    temporal_features_027 DOUBLE PRECISION,
    temporal_features_028 DOUBLE PRECISION,
    temporal_features_029 DOUBLE PRECISION,
    temporal_features_030 DOUBLE PRECISION,
    temporal_features_031 DOUBLE PRECISION,
    temporal_features_032 DOUBLE PRECISION,
    temporal_features_033 DOUBLE PRECISION,
    temporal_features_034 DOUBLE PRECISION,
    temporal_features_035 DOUBLE PRECISION,
    temporal_features_036 DOUBLE PRECISION,
    temporal_features_037 DOUBLE PRECISION,
    temporal_features_038 DOUBLE PRECISION,
    temporal_features_039 DOUBLE PRECISION,
    temporal_features_040 DOUBLE PRECISION,
    temporal_features_041 DOUBLE PRECISION,
    temporal_features_042 DOUBLE PRECISION,
    temporal_features_043 DOUBLE PRECISION,
    temporal_features_044 DOUBLE PRECISION,
    temporal_features_045 DOUBLE PRECISION,
    temporal_features_046 DOUBLE PRECISION,
    temporal_features_047 DOUBLE PRECISION,
    temporal_features_048 DOUBLE PRECISION,
    temporal_features_049 DOUBLE PRECISION,
    temporal_features_050 DOUBLE PRECISION,
    temporal_features_051 DOUBLE PRECISION,
    temporal_features_052 DOUBLE PRECISION,
    temporal_features_053 DOUBLE PRECISION,
    temporal_features_054 DOUBLE PRECISION,
    temporal_features_055 DOUBLE PRECISION,
    temporal_features_056 DOUBLE PRECISION,
    temporal_features_057 DOUBLE PRECISION,
    temporal_features_058 DOUBLE PRECISION,
    temporal_features_059 DOUBLE PRECISION,
    temporal_features_060 DOUBLE PRECISION,
    temporal_features_061 DOUBLE PRECISION,
    temporal_features_062 DOUBLE PRECISION,
    temporal_features_063 DOUBLE PRECISION,
    temporal_features_064 DOUBLE PRECISION,
    temporal_features_065 DOUBLE PRECISION,
    temporal_features_066 DOUBLE PRECISION,
    temporal_features_067 DOUBLE PRECISION,
    temporal_features_068 DOUBLE PRECISION,
    temporal_features_069 DOUBLE PRECISION,
    temporal_features_070 DOUBLE PRECISION,
    temporal_features_071 DOUBLE PRECISION,
    temporal_features_072 DOUBLE PRECISION,
    temporal_features_073 DOUBLE PRECISION,
    temporal_features_074 DOUBLE PRECISION,
    temporal_features_075 DOUBLE PRECISION,
    temporal_features_076 DOUBLE PRECISION,
    temporal_features_077 DOUBLE PRECISION,
    temporal_features_078 DOUBLE PRECISION,
    temporal_features_079 DOUBLE PRECISION,
    temporal_features_080 DOUBLE PRECISION,
    temporal_features_081 DOUBLE PRECISION,
    temporal_features_082 DOUBLE PRECISION,
    temporal_features_083 DOUBLE PRECISION,
    temporal_features_084 DOUBLE PRECISION,
    temporal_features_085 DOUBLE PRECISION,
    temporal_features_086 DOUBLE PRECISION,
    temporal_features_087 DOUBLE PRECISION,
    temporal_features_088 DOUBLE PRECISION,
    temporal_features_089 DOUBLE PRECISION,
    temporal_features_090 DOUBLE PRECISION,
    temporal_features_091 DOUBLE PRECISION,
    temporal_features_092 DOUBLE PRECISION,
    temporal_features_093 DOUBLE PRECISION,
    temporal_features_094 DOUBLE PRECISION,
    temporal_features_095 DOUBLE PRECISION,
    temporal_features_096 DOUBLE PRECISION,
    temporal_features_097 DOUBLE PRECISION,
    temporal_features_098 DOUBLE PRECISION,
    temporal_features_099 DOUBLE PRECISION,
    temporal_features_100 DOUBLE PRECISION,
    temporal_features_101 DOUBLE PRECISION,
    temporal_features_102 DOUBLE PRECISION,
    temporal_features_103 DOUBLE PRECISION,
    temporal_features_104 DOUBLE PRECISION,
    temporal_features_105 DOUBLE PRECISION,
    temporal_features_106 DOUBLE PRECISION,
    temporal_features_107 DOUBLE PRECISION,
    temporal_features_108 DOUBLE PRECISION,
    temporal_features_109 DOUBLE PRECISION,
    temporal_features_110 DOUBLE PRECISION,
    temporal_features_111 DOUBLE PRECISION,
    temporal_features_112 DOUBLE PRECISION,
    temporal_features_113 DOUBLE PRECISION,
    temporal_features_114 DOUBLE PRECISION,
    temporal_features_115 DOUBLE PRECISION,
    temporal_features_116 DOUBLE PRECISION,
    temporal_features_117 DOUBLE PRECISION,
    temporal_features_118 DOUBLE PRECISION,
    temporal_features_119 DOUBLE PRECISION,
    temporal_features_120 DOUBLE PRECISION,
    temporal_features_121 DOUBLE PRECISION,
    temporal_features_122 DOUBLE PRECISION,
    temporal_features_123 DOUBLE PRECISION,
    temporal_features_124 DOUBLE PRECISION,
    temporal_features_125 DOUBLE PRECISION,
    temporal_features_126 DOUBLE PRECISION,
    temporal_features_127 DOUBLE PRECISION,
    temporal_features_128 DOUBLE PRECISION,
    temporal_features_129 DOUBLE PRECISION,
    temporal_features_130 DOUBLE PRECISION,
    temporal_features_131 DOUBLE PRECISION,
    temporal_features_132 DOUBLE PRECISION,
    temporal_features_133 DOUBLE PRECISION,
    temporal_features_134 DOUBLE PRECISION,
    temporal_features_135 DOUBLE PRECISION,
    temporal_features_136 DOUBLE PRECISION,
    temporal_features_137 DOUBLE PRECISION,
    temporal_features_138 DOUBLE PRECISION,
    temporal_features_139 DOUBLE PRECISION,
    temporal_features_140 DOUBLE PRECISION,
    temporal_features_141 DOUBLE PRECISION,
    temporal_features_142 DOUBLE PRECISION,
    temporal_features_143 DOUBLE PRECISION,
    temporal_features_144 DOUBLE PRECISION,
    temporal_features_145 DOUBLE PRECISION,
    temporal_features_146 DOUBLE PRECISION,
    temporal_features_147 DOUBLE PRECISION,
    temporal_features_148 DOUBLE PRECISION,
    temporal_features_149 DOUBLE PRECISION,
    temporal_features_150 DOUBLE PRECISION,
    temporal_features_151 DOUBLE PRECISION,
    temporal_features_152 DOUBLE PRECISION,
    temporal_features_153 DOUBLE PRECISION,
    temporal_features_154 DOUBLE PRECISION,
    temporal_features_155 DOUBLE PRECISION,
    temporal_features_156 DOUBLE PRECISION,
    temporal_features_157 DOUBLE PRECISION,
    temporal_features_158 DOUBLE PRECISION,
    temporal_features_159 DOUBLE PRECISION,
    temporal_features_160 DOUBLE PRECISION,
    temporal_features_161 DOUBLE PRECISION,
    temporal_features_162 DOUBLE PRECISION,
    temporal_features_163 DOUBLE PRECISION,
    temporal_features_164 DOUBLE PRECISION,
    temporal_features_165 DOUBLE PRECISION,
    temporal_features_166 DOUBLE PRECISION,
    temporal_features_167 DOUBLE PRECISION,
    temporal_features_168 DOUBLE PRECISION,
    temporal_features_169 DOUBLE PRECISION,
    temporal_features_170 DOUBLE PRECISION,
    temporal_features_171 DOUBLE PRECISION,
    temporal_features_172 DOUBLE PRECISION,
    temporal_features_173 DOUBLE PRECISION,
    temporal_features_174 DOUBLE PRECISION,
    temporal_features_175 DOUBLE PRECISION,
    temporal_features_176 DOUBLE PRECISION,
    temporal_features_177 DOUBLE PRECISION,
    temporal_features_178 DOUBLE PRECISION,
    temporal_features_179 DOUBLE PRECISION,
    temporal_features_180 DOUBLE PRECISION,
    temporal_features_181 DOUBLE PRECISION,
    temporal_features_182 DOUBLE PRECISION,
    temporal_features_183 DOUBLE PRECISION,
    temporal_features_184 DOUBLE PRECISION,
    temporal_features_185 DOUBLE PRECISION,
    temporal_features_186 DOUBLE PRECISION,
    temporal_features_187 DOUBLE PRECISION,
    temporal_features_188 DOUBLE PRECISION,
    temporal_features_189 DOUBLE PRECISION,
    temporal_features_190 DOUBLE PRECISION,
    temporal_features_191 DOUBLE PRECISION,
    temporal_features_192 DOUBLE PRECISION,
    temporal_features_193 DOUBLE PRECISION,
    temporal_features_194 DOUBLE PRECISION,
    temporal_features_195 DOUBLE PRECISION,
    temporal_features_196 DOUBLE PRECISION,
    temporal_features_197 DOUBLE PRECISION,
    temporal_features_198 DOUBLE PRECISION,
    temporal_features_199 DOUBLE PRECISION,
    temporal_features_200 DOUBLE PRECISION,
    temporal_features_201 DOUBLE PRECISION,
    temporal_features_202 DOUBLE PRECISION,
    temporal_features_203 DOUBLE PRECISION,
    temporal_features_204 DOUBLE PRECISION,
    temporal_features_205 DOUBLE PRECISION,
    temporal_features_206 DOUBLE PRECISION,
    temporal_features_207 DOUBLE PRECISION,
    temporal_features_208 DOUBLE PRECISION,
    temporal_features_209 DOUBLE PRECISION,
    temporal_features_210 DOUBLE PRECISION,
    temporal_features_211 DOUBLE PRECISION,
    temporal_features_212 DOUBLE PRECISION,
    temporal_features_213 DOUBLE PRECISION,
    temporal_features_214 DOUBLE PRECISION,
    temporal_features_215 DOUBLE PRECISION,
    temporal_features_216 DOUBLE PRECISION,
    temporal_features_217 DOUBLE PRECISION,
    temporal_features_218 DOUBLE PRECISION,
    temporal_features_219 DOUBLE PRECISION,
    temporal_features_220 DOUBLE PRECISION,
    temporal_features_221 DOUBLE PRECISION,
    temporal_features_222 DOUBLE PRECISION,
    temporal_features_223 DOUBLE PRECISION
);




/* ========================== TABLE license  ========================== */

CREATE TABLE license (
    license_id serial unique PRIMARY KEY,
    license_parent_id INT, 
    license_title VARCHAR(255),
    license_short_title VARCHAR(50),
    license_url VARCHAR(255),
    track_license VARCHAR(255),
    track_id INT REFERENCES tracks(track_id) 
);



/* ========================== TABLE associative USERS TRACK  ========================== */

CREATE TABLE users_track (
    user_id  INT REFERENCES users(user_id),
    track_id INT REFERENCES tracks(track_id),
    PRIMARY KEY (user_id, track_id)
);

/* ========================== TABLE PLAYLIST  ========================== */

CREATE TABLE playlist (
    playlist_id SERIAL PRIMARY KEY,
    playlist_name VARCHAR(255) NOT NULL,
    playlist_description TEXT,
    /* list_tracks           ****************************************a voir si table lie pour la liste track**********************/
    created_at TIMESTAMP DEFAULT NOW()
);
ALTER TABLE sae.playlist ADD COLUMN playlist_num_tracks INT DEFAULT 0;

/* ========================== TABLE PLAYLIST TRACK / playlist user ========================== */

CREATE TABLE playlist_track (
    playlist_id INT REFERENCES playlist(playlist_id),
    track_id INT REFERENCES tracks(track_id),
    PRIMARY KEY (playlist_id, track_id)
);

CREATE TABLE playlist_user (
    playlist_id INT REFERENCES playlist(playlist_id),
    user_id INT REFERENCES users(user_id),
    PRIMARY KEY (playlist_id, user_id)
);



/* ========================== TABLE artistsocialscore et artist rank  ========================== */

CREATE TABLE artist_social_score (
    ass_id SERIAL PRIMARY KEY,
    artist_id INT UNIQUE REFERENCES artist(artist_id),
    social_features_artist_discovery DOUBLE PRECISION,
    social_features_artist_familiarity DOUBLE PRECISION,
    social_features_artist_hottnesss DOUBLE PRECISION
);

CREATE TABLE artist_rank (
    ar_id SERIAL PRIMARY KEY,
    artist_id INT UNIQUE REFERENCES artist(artist_id),
    ranks_artist_discovery_rank DOUBLE PRECISION,
    ranks_artist_familiarity_rank DOUBLE PRECISION,
    ranks_artist_hottnesss_rank DOUBLE PRECISION

);



/* ========================== TABLE GENRE  ========================== */

CREATE TABLE genre (
    genre_id        INT UNIQUE PRIMARY KEY,
    genre_parent_id INT,
    genre_title     VARCHAR(65000),
    genre_handle    VARCHAR(65000),
    genre_color     VARCHAR(65000),
    top_level       BOOLEAN,
    tracks          INT
);



/* ========================== TABLE associative trackGENRE  ========================== */

CREATE TABLE track_genre (
    track_id INT REFERENCES tracks(track_id),
    genre_id INT REFERENCES genre(genre_id),
    PRIMARY KEY (track_id, genre_id)
);


/* ========================== TABLE PUBLISHER  ========================== */

CREATE TABLE publisher (
    publisher_id int PRIMARY KEY,
    publisher_name VARCHAR(255)
);


/* ========================== ternaire LINK TABLES ========================== */


CREATE TABLE artist_album_track (
    artist_id INT,
    album_id INT,
    track_id INT,

    PRIMARY KEY (artist_id, album_id, track_id),

    FOREIGN KEY (track_id) REFERENCES tracks(track_id) ON DELETE CASCADE,
    FOREIGN KEY (album_id) REFERENCES album(album_id) ON DELETE CASCADE,
    FOREIGN KEY (artist_id) REFERENCES artist(artist_id) ON DELETE CASCADE
);


CREATE TABLE artist_track_publisher (
    artist_id INT REFERENCES artist(artist_id),
    track_id INT REFERENCES tracks(track_id),
    publisher_id INT REFERENCES publisher(publisher_id),
    PRIMARY KEY (artist_id, track_id, publisher_id)
);


/* ##################################################################### */
/*                                 VUES                                  */
/* ##################################################################### */

CREATE OR REPLACE VIEW tracks_features AS
    SELECT
        t.track_id,
        MAX(t.track_title)              AS track_title,
        MAX(t.track_duration)           AS track_duration,
        MAX(t.track_genre_top)          AS track_genre_top,
        MAX(t.track_genre)              AS track_genre,
        MAX(t.track_tags)               AS track_tags,
        MAX(t.track_listens)            AS track_listens,
        MAX(t.track_favorite)           AS track_favorite,
        MAX(t.track_interest)           AS track_interest,
        MAX(t.track_date_recorded)      AS track_date_recorded,
        MAX(t.track_date_created)       AS track_date_created,
        MAX(t.track_composer)           AS track_composer,
        MAX(t.track_lyricist)           AS track_lyricist,
        MAX(t.track_file)               AS track_file,
        MAX(t.track_image_file)         AS track_image_file,
        MAX(t.track_bit_rate)           AS track_bit_rate,
        MAX(t.track_disk_number)        AS track_disk_number,
        STRING_AGG(DISTINCT alb.album_id::text, ',') AS album_ids,
        STRING_AGG(DISTINCT alb.album_title, ', ')   AS album_titles,
        STRING_AGG(DISTINCT ar.artist_name, ', ')    AS artist_names,
        STRING_AGG(DISTINCT ar.artist_id::text, ',') AS artist_ids,
        MAX(au.audio_features_accousticness)    AS audio_features_accousticness,
        MAX(au.audio_features_danceability)     AS audio_features_danceability,
        MAX(au.audio_features_energy)           AS audio_features_energy,
        MAX(au.audio_features_instrumentalness) AS audio_features_instrumentalness,
        MAX(au.audio_features_liveness)         AS audio_features_liveness,
        MAX(au.audio_features_speechiness)      AS audio_features_speechiness,
        MAX(au.audio_features_tempo)            AS audio_features_tempo,
        MAX(au.audio_features_valence)          AS audio_features_valence,
        AVG(sss.social_features_song_currency)  AS avg_song_currency,
        AVG(sss.social_features_song_hottness)  AS avg_song_hottness,
        AVG(sr.ranks_song_currency_rank)        AS avg_song_currency_rank,
        AVG(sr.ranks_song_hottness_rank)        AS avg_song_hottness_rank
    FROM tracks t
    LEFT JOIN artist_album_track aat ON aat.track_id = t.track_id
    LEFT JOIN album alb              ON alb.album_id = aat.album_id
    LEFT JOIN artist ar              ON ar.artist_id = aat.artist_id
    LEFT JOIN audio au               ON au.track_id = t.track_id
    LEFT JOIN song_social_score sss  ON sss.track_id = t.track_id
    LEFT JOIN song_rank sr           ON sr.track_id = t.track_id
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
    LEFT JOIN artist_album_track aat ON aat.album_id = alb.album_id
    LEFT JOIN artist art             ON art.artist_id = aat.artist_id
    GROUP BY alb.album_id
;


CREATE OR REPLACE VIEW artist_features AS
    SELECT
        art.artist_id,
        art.artist_name,
        art.artist_tags,
        art.artist_location,
        art.artist_associated_label,
        art.artist_active_year_begin,
        art.artist_active_year_end,
        art.artist_favorites,
        AVG(sa.social_features_artist_discovery)   AS avg_artist_discovery,
        AVG(sa.social_features_artist_familiarity) AS avg_artist_familiarity,
        AVG(sa.social_features_artist_hottnesss)   AS avg_sa_artist_hottness,
        AVG(ar.ranks_artist_discovery_rank)        AS avg_artist_discovery_rank,
        AVG(ar.ranks_artist_familiarity_rank)      AS avg_artist_familiarity_rank,
        AVG(ar.ranks_artist_hottnesss_rank)        AS avg_ar_artist_hottness,
        COUNT(DISTINCT aat.track_id)               AS num_tracks_associated
    FROM artist art
    LEFT JOIN artist_social_score sa     ON sa.artist_id = art.artist_id
    LEFT JOIN artist_rank ar             ON ar.artist_id = art.artist_id
    LEFT JOIN artist_album_track aat     ON aat.artist_id = art.artist_id
    GROUP BY art.artist_id
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

CREATE OR REPLACE FUNCTION sae.update_album_track_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE sae.album
        SET album_tracks = COALESCE(album_tracks, 0) + 1
        WHERE album_id = NEW.album_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE sae.album
        SET album_tracks = GREATEST(COALESCE(album_tracks, 0) - 1, 0)
        WHERE album_id = OLD.album_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_album_track_count
AFTER INSERT OR DELETE ON sae.artist_album_track
FOR EACH ROW
EXECUTE FUNCTION sae.update_album_track_count();

CREATE TRIGGER artist_album_track_insert
AFTER INSERT ON artist_album_track
FOR EACH ROW
EXECUTE FUNCTION update_album_track_count();

CREATE TRIGGER artist_album_track_delete
AFTER DELETE ON artist_album_track
FOR EACH ROW
EXECUTE FUNCTION update_album_track_count();


CREATE OR REPLACE FUNCTION update_playlist_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE sae.playlist
        SET playlist_num_tracks = COALESCE(playlist_num_tracks, 0) + 1
        WHERE playlist_id = NEW.playlist_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE sae.playlist
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



/* ##################################################################### */
/*                               INDEX                                   */
/* ##################################################################### */


CREATE INDEX IF NOT EXISTS idx_album_keynouns
ON sae.album USING GIN (album_keynouns);
