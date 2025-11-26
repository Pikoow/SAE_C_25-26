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