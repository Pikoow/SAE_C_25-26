from fastapi import FastAPI, HTTPException, Query
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="API Muse")

#Erreur page web Cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration de la connexion (identique à tes scripts de peuplement)
DB_CONFIG = {
    "host": "localhost",
    "dbname": "postgres",
    "user": "postgres",
    "password": "PASSWORD_HERE",
    "port": 5432
}

def get_db_connection():
    try:
        # On utilise RealDictCursor pour obtenir les résultats sous forme de dictionnaire (JSON)
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Erreur de connexion : {e}")
        return None

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API de Muse!"}

@app.get("/tracks")
def get_all_tracks():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        # On récupère les tracks avec le nom de l'album et de l'artiste associé
        query = """
            SELECT 
                t.track_id, 
                t.track_title, 
                t.track_duration,
                a.album_title,
                art.artist_name
            FROM sae.tracks t
            LEFT JOIN sae.album a ON t.album_id = a.album_id
            LEFT JOIN sae.artist art ON t.artist_id = art.artist_id 
            LIMIT 50;
        """
        cur.execute(query)
        tracks = cur.fetchall()
        cur.close()
        conn.close()
        
        return {
            "count": len(tracks),
            "results": tracks
        }
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tracks/{track_id}")
def get_track_by_id(track_id: int):
    """
    Récupère une musique spécifique par son ID avec toutes ses informations.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        # Requête détaillée pour une musique spécifique
        query = """
            SELECT 
                t.track_id, 
                t.track_title, 
                t.track_duration,
                t.track_genre_top,
                t.track_genre,
                t.track_listens,
                t.track_favorite,
                t.track_interest,
                t.track_date_recorded,
                t.track_date_created,
                t.track_composer,
                t.track_lyricist,
                t.track_tags,
                t.track_bit_rate,
                a.album_id,
                a.album_title,
                a.album_type,
                a.album_tracks,
                a.album_image_file,
                a.album_date_released,
                art.artist_id,
                art.artist_name,
                art.artist_bio,
                art.artist_location,
                art.artist_favorites,
                art.artist_website,
                audio.audio_features_danceability,
                audio.audio_features_energy,
                audio.audio_features_tempo,
                audio.audio_features_valence,
                sss.social_features_song_currency,
                sss.social_features_song_hottness
            FROM sae.tracks t
            LEFT JOIN sae.artist_album_track aat ON t.track_id = aat.track_id
            LEFT JOIN sae.album a ON aat.album_id = a.album_id
            LEFT JOIN sae.artist art ON aat.artist_id = art.artist_id
            LEFT JOIN sae.audio audio ON t.track_id = audio.track_id
            LEFT JOIN sae.song_social_score sss ON t.track_id = sss.track_id
            WHERE t.track_id = %s
        """
        
        cur.execute(query, (track_id,))
        track = cur.fetchone()
        
        if not track:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Musique non trouvée")
        
        # Récupérer les genres associés
        genre_query = """
            SELECT g.genre_title
            FROM sae.track_genre tg
            JOIN sae.genre g ON tg.genre_id = g.genre_id
            WHERE tg.track_id = %s
        """
        cur.execute(genre_query, (track_id,))
        genres = cur.fetchall()
        
        # Formater les genres
        track['genres'] = [genre['genre_title'] for genre in genres]
        
        cur.close()
        conn.close()
        
        return track
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/artists")
def get_artists(
    limit: Optional[int] = Query(50, ge=1, le=500, description="Nombre maximum de résultats"),
    offset: Optional[int] = Query(0, ge=0, description="Décalage pour la pagination"),
    name: Optional[str] = Query(None, description="Filtrer par nom d'artiste")
):
    """
    Récupère la liste des artistes avec leurs statistiques.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        base_query = """
            SELECT 
                artist_id,
                artist_name,
                artist_location,
                artist_favorites,
                artist_active_year_begin,
                artist_active_year_end,
                artist_tags
            FROM sae.artist
            WHERE 1=1
        """
        
        params = []
        if name:
            base_query += " AND artist_name ILIKE %s"
            params.append(f"%{name}%")
        
        base_query += " ORDER BY artist_name LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cur.execute(base_query, params)
        artists = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return {
            "total": len(artists),
            "limit": limit,
            "offset": offset,
            "results": artists
        }
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/artists/{artist_id}/tracks")
def get_artist_tracks(artist_id: int):
    """
    Récupère toutes les musiques d'un artiste spécifique.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        query = """
            SELECT 
                t.track_id,
                t.track_title,
                t.track_duration,
                t.track_genre_top,
                t.track_listens,
                t.track_favorite,
                a.album_title,
                a.album_image_file
            FROM sae.tracks t
            LEFT JOIN sae.artist_album_track aat ON t.track_id = aat.track_id
            LEFT JOIN sae.album a ON aat.album_id = a.album_id
            WHERE aat.artist_id = %s
            ORDER BY t.track_listens DESC
        """
        
        cur.execute(query, (artist_id,))
        tracks = cur.fetchall()
        
        # Récupérer les informations de l'artiste
        artist_query = "SELECT artist_name FROM sae.artist WHERE artist_id = %s"
        cur.execute(artist_query, (artist_id,))
        artist = cur.fetchone()
        
        if not artist:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Artiste non trouvé")
        
        cur.close()
        conn.close()
        
        return {
            "artist": artist['artist_name'],
            "total_tracks": len(tracks),
            "tracks": tracks
        }
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/albums")
def get_albums(
    limit: Optional[int] = Query(50, ge=1, le=500, description="Nombre maximum de résultats"),
    offset: Optional[int] = Query(0, ge=0, description="Décalage pour la pagination"),
    title: Optional[str] = Query(None, description="Filtrer par titre d'album")
):
    """
    Récupère la liste des albums.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        base_query = """
            SELECT 
                album_id,
                album_title,
                album_type,
                album_tracks,
                album_listens,
                album_favorites,
                album_image_file,
                album_date_released
            FROM sae.album
            WHERE 1=1
        """
        
        params = []
        if title:
            base_query += " AND album_title ILIKE %s"
            params.append(f"%{title}%")
        
        base_query += " ORDER BY album_date_released DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cur.execute(base_query, params)
        albums = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return {
            "total": len(albums),
            "limit": limit,
            "offset": offset,
            "results": albums
        }
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/albums/{album_id}/tracks")
def get_album_tracks(album_id: int):
    """
    Récupère toutes les musiques d'un album spécifique.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        # Récupérer les informations de l'album
        album_query = """
            SELECT 
                album_title,
                album_type,
                album_tracks,
                album_image_file,
                album_date_released
            FROM sae.album
            WHERE album_id = %s
        """
        cur.execute(album_query, (album_id,))
        album = cur.fetchone()
        
        if not album:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Album non trouvé")
        
        # Récupérer les musiques de l'album
        tracks_query = """
            SELECT 
                t.track_id,
                t.track_title,
                t.track_duration,
                t.track_genre_top,
                t.track_listens,
                t.track_favorite,
                art.artist_name
            FROM sae.tracks t
            LEFT JOIN sae.artist_album_track aat ON t.track_id = aat.track_id
            LEFT JOIN sae.artist art ON aat.artist_id = art.artist_id
            WHERE aat.album_id = %s
            ORDER BY t.track_disk_number, t.track_title
        """
        
        cur.execute(tracks_query, (album_id,))
        tracks = cur.fetchall()
        
        # Récupérer les artistes de l'album
        artists_query = """
            SELECT DISTINCT art.artist_name
            FROM sae.artist_album_track aat
            JOIN sae.artist art ON aat.artist_id = art.artist_id
            WHERE aat.album_id = %s
        """
        cur.execute(artists_query, (album_id,))
        artists = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return {
            "album": album,
            "artists": [artist['artist_name'] for artist in artists],
            "total_tracks": len(tracks),
            "tracks": tracks
        }
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
def search(
    q: str = Query(..., description="Terme de recherche"),
    search_type: str = Query("all", description="Type de recherche: all, tracks, artists, albums")
):
    """
    Recherche globale dans les musiques, artistes et albums.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        results = {}
        search_term = f"%{q}%"
        
        if search_type in ["all", "tracks"]:
            tracks_query = """
                SELECT 
                    t.track_id,
                    t.track_title,
                    art.artist_name,
                    a.album_title,
                    t.track_duration,
                    t.track_listens
                FROM sae.tracks t
                LEFT JOIN sae.artist_album_track aat ON t.track_id = aat.track_id
                LEFT JOIN sae.artist art ON aat.artist_id = art.artist_id
                LEFT JOIN sae.album a ON aat.album_id = a.album_id
                WHERE t.track_title ILIKE %s
                ORDER BY t.track_listens DESC
                LIMIT 20
            """
            cur.execute(tracks_query, (search_term,))
            results['tracks'] = cur.fetchall()
        
        if search_type in ["all", "artists"]:
            artists_query = """
                SELECT 
                    artist_id,
                    artist_name,
                    artist_location,
                    artist_favorites
                FROM sae.artist
                WHERE artist_name ILIKE %s
                ORDER BY artist_favorites DESC
                LIMIT 20
            """
            cur.execute(artists_query, (search_term,))
            results['artists'] = cur.fetchall()
        
        if search_type in ["all", "albums"]:
            albums_query = """
                SELECT 
                    album_id,
                    album_title,
                    album_type,
                    album_tracks,
                    album_favorites
                FROM sae.album
                WHERE album_title ILIKE %s
                ORDER BY album_favorites DESC
                LIMIT 20
            """
            cur.execute(albums_query, (search_term,))
            results['albums'] = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return results
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Lance le serveur sur le port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)