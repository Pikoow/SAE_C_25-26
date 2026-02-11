from fastapi import FastAPI, HTTPException, Query
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Annotated, Union
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Recommendation'))

from item_based_pierre import recommend_similar_tracks
from item_based_stanislas import recommend_artists, initialize_artist_system

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_artist_system()
    yield

app = FastAPI(title="API Muse", lifespan=lifespan)

# Erreur page web Cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration de la connexion
DB_CONFIG = {
    "host": "localhost",
    "dbname": os.getenv("POSTGRES_DBNAME"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "port": int(os.getenv("POSTGRES_PORT", 5432))
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Erreur de connexion : {e}")
        return None

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API de Muse!"}

@app.get("/tracks")
def get_all_tracks(
    limit: Optional[int] = Query(50, ge=1, le=100000, description="Nombre maximum de résultats"),
    offset: Optional[int] = Query(0, ge=0, description="Décalage pour la pagination")
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        # On utilise la vue tracks_features pour simplifier
        query = """
            SELECT 
                track_id, 
                track_title, 
                track_duration,
                track_genre_top,
                track_listens,
                track_file,
                album_titles,
                artist_names
            FROM sae.tracks_features
            ORDER BY track_listens DESC
            LIMIT %s OFFSET %s
        """
        cur.execute(query, (limit, offset))
        tracks = cur.fetchall()
        
        # Compter le total
        count_query = "SELECT COUNT(*) as total FROM sae.tracks"
        cur.execute(count_query)
        total = cur.fetchone()['total']
        
        cur.close()
        conn.close()
        
        return {
            "total": total,
            "count": len(tracks),
            "limit": limit,
            "offset": offset,
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
        
        # Utilisation de la vue tracks_features pour une requête plus simple
        query = """
            SELECT 
                track_id, 
                track_title, 
                track_duration,
                track_genre_top,
                track_genre,
                track_listens,
                track_favorite,
                track_interest,
                track_date_recorded,
                track_date_created,
                track_composer,
                track_lyricist,
                track_tags,
                track_file,
                track_image_file,
                track_bit_rate,
                album_ids,
                album_titles,
                artist_ids,
                artist_names,
                audio_features_accousticness,
                audio_features_danceability,
                audio_features_energy,
                audio_features_instrumentalness,
                audio_features_liveness,
                audio_features_speechiness,
                audio_features_tempo,
                audio_features_valence,
                avg_song_currency,
                avg_song_hottness,
                avg_song_currency_rank,
                avg_song_hottness_rank
            FROM sae.tracks_features
            WHERE track_id = %s
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
        
        # Récupérer les détails de l'album (premier album)
        if track['album_ids']:
            album_id = track['album_ids'].split(',')[0]
            album_query = """
                SELECT 
                    album_id,
                    album_title,
                    album_type,
                    album_tracks,
                    album_image_file,
                    album_date_released
                FROM sae.album
                WHERE album_id = %s
            """
            cur.execute(album_query, (int(album_id),))
            album_info = cur.fetchone()
            track['album_info'] = album_info
        
        # Récupérer les détails de l'artiste (premier artiste)
        if track['artist_ids']:
            artist_id = track['artist_ids'].split(',')[0]
            artist_query = """
                SELECT 
                    artist_id,
                    artist_name,
                    artist_bio,
                    artist_location,
                    artist_favorites,
                    artist_website
                FROM sae.artist
                WHERE artist_id = %s
            """
            cur.execute(artist_query, (int(artist_id),))
            artist_info = cur.fetchone()
            track['artist_info'] = artist_info
        
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
    limit: Optional[int] = Query(50, ge=1, le=100000, description="Nombre maximum de résultats"),
    offset: Optional[int] = Query(0, ge=0, description="Décalage pour la pagination")
):
    """
    Récupère la liste des artistes avec leurs statistiques.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        query = """
            SELECT 
                artist_id,
                artist_name,
                artist_location,
                artist_favorites,
                artist_active_year_begin,
                artist_active_year_end,
                artist_tags,
                artist_image_file
            FROM sae.artist
            ORDER BY artist_favorites DESC
            LIMIT %s OFFSET %s
        """
        
        cur.execute(query, (limit, offset))
        artists = cur.fetchall()
        
        # Compter le total
        count_query = "SELECT COUNT(*) as total FROM sae.artist"
        cur.execute(count_query)
        total = cur.fetchone()['total']
        
        cur.close()
        conn.close()
        
        return {
            "total": total,
            "count": len(artists),
            "limit": limit,
            "offset": offset,
            "results": artists
        }
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/artists/{artist_id}")
def get_artist_by_id(artist_id: int):
    """
    Récupère un artiste spécifique par son ID.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        query = """
            SELECT 
                artist_id,
                artist_name,
                artist_bio,
                artist_location,
                artist_favorites,
                artist_active_year_begin,
                artist_active_year_end,
                artist_tags,
                artist_image_file,
                artist_website,
                artist_associated_label
            FROM sae.artist
            WHERE artist_id = %s
        """
        
        cur.execute(query, (artist_id,))
        artist = cur.fetchone()
        
        if not artist:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Artiste non trouvé")
        
        cur.close()
        conn.close()
        
        return artist
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/artists/{artist_id}/tracks")
def get_artist_tracks(
    artist_id: int,
    limit: Optional[int] = Query(50, ge=1, le=500, description="Nombre maximum de résultats"),
    offset: Optional[int] = Query(0, ge=0, description="Décalage pour la pagination")
):
    """
    Récupère toutes les musiques d'un artiste spécifique.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        # Vérifier si l'artiste existe
        artist_query = "SELECT artist_name FROM sae.artist WHERE artist_id = %s"
        cur.execute(artist_query, (artist_id,))
        artist = cur.fetchone()
        
        if not artist:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Artiste non trouvé")
        
        # Récupérer les tracks de l'artiste
        query = """
            SELECT DISTINCT
                t.track_id,
                t.track_title,
                t.track_duration,
                t.track_genre_top,
                t.track_listens,
                t.track_favorite,
                t.track_file,
                a.album_title,
                a.album_image_file
            FROM sae.tracks t
            JOIN sae.artist_album_track aat ON t.track_id = aat.track_id
            LEFT JOIN sae.album a ON aat.album_id = a.album_id
            WHERE aat.artist_id = %s
            ORDER BY t.track_listens DESC
            LIMIT %s OFFSET %s
        """
        
        cur.execute(query, (artist_id, limit, offset))
        tracks = cur.fetchall()
        
        # Compter le total
        count_query = """
            SELECT COUNT(DISTINCT t.track_id) as total
            FROM sae.tracks t
            JOIN sae.artist_album_track aat ON t.track_id = aat.track_id
            WHERE aat.artist_id = %s
        """
        cur.execute(count_query, (artist_id,))
        total = cur.fetchone()['total']
        
        cur.close()
        conn.close()
        
        return {
            "artist": artist['artist_name'],
            "total": total,
            "count": len(tracks),
            "limit": limit,
            "offset": offset,
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
                album_date_released,
                album_tags,
                artists
            FROM sae.album_features
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
        
        # Compter le total
        count_query = "SELECT COUNT(*) as total FROM sae.album"
        if title:
            count_query += " WHERE album_title ILIKE %s"
            cur.execute(count_query, (f"%{title}%",))
        else:
            cur.execute(count_query)
        total = cur.fetchone()['total']
        
        cur.close()
        conn.close()
        
        return {
            "total": total,
            "count": len(albums),
            "limit": limit,
            "offset": offset,
            "results": albums
        }
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/albums/{album_id}")
def get_album_by_id(album_id: int):
    """
    Récupère un album spécifique par son ID.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        # Utilisation de la vue album_features pour simplifier
        query = """
            SELECT 
                album_id,
                album_title,
                album_type,
                album_tracks,
                album_listens,
                album_favorites,
                album_image_file,
                album_date_released,
                album_tags,
                artists
            FROM sae.album_features
            WHERE album_id = %s
        """
        
        cur.execute(query, (album_id,))
        album = cur.fetchone()
        
        if not album:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Album non trouvé")
        
        cur.close()
        conn.close()
        
        return album
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/albums/{album_id}/tracks")
def get_album_tracks(
    album_id: int,
    limit: Optional[int] = Query(50, ge=1, le=500, description="Nombre maximum de résultats"),
    offset: Optional[int] = Query(0, ge=0, description="Décalage pour la pagination")
):
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
                t.track_file,
                t.track_favorite,
                art.artist_name
            FROM sae.tracks t
            JOIN sae.artist_album_track aat ON t.track_id = aat.track_id
            JOIN sae.artist art ON aat.artist_id = art.artist_id
            WHERE aat.album_id = %s
            ORDER BY t.track_disk_number, t.track_title
            LIMIT %s OFFSET %s
        """
        
        cur.execute(tracks_query, (album_id, limit, offset))
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
        
        # Compter le total
        count_query = """
            SELECT COUNT(*) as total
            FROM sae.artist_album_track
            WHERE album_id = %s
        """
        cur.execute(count_query, (album_id,))
        total = cur.fetchone()['total']
        
        cur.close()
        conn.close()
        
        return {
            "album": album,
            "artists": [artist['artist_name'] for artist in artists],
            "total": total,
            "count": len(tracks),
            "limit": limit,
            "offset": offset,
            "tracks": tracks
        }
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reco/tracks")
def recommend_tracks(
    track_ids: List[int] = Query(..., description="One or more track IDs to base recommendations on"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Exemple: /reco/tracks?track_ids=69170&track_ids=95976
    """
    try:
        recommendations = recommend_similar_tracks(track_ids, top_n=limit)
        
        if not recommendations:
            raise HTTPException(status_code=404, detail="No recommendations found for the given IDs")
            
        return {
            "input_ids": track_ids,
            "count": len(recommendations),
            "results": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reco/artists")
def get_artist_recommendations(
    artist_ids: List[int] = Query(..., description="One or more artist IDs to base recommendations on"),
    limit: int = Query(5, ge=1, le=50)
):
    """
    Exemple: /reco/artists?artist_ids=123&artist_ids=456
    """
    try:
        recommendations = recommend_artists(artist_ids=artist_ids, top_k=limit)
        
        if not recommendations:
            # Logic to check if the input IDs exist at all if no recommendations are found
            return {
                "input_artist_ids": artist_ids,
                "count": 0,
                "results": [],
                "message": "No embeddings found for the provided artist IDs."
            }
        
        return {
            "input_artist_ids": artist_ids,
            "count": len(recommendations),
            "results": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur reco: {str(e)}")

@app.get("/genres")
def get_all_genres(
    limit: Optional[int] = Query(500, ge=1, le=500, description="Nombre maximum de résultats"),
    offset: Optional[int] = Query(0, ge=0, description="Décalage pour la pagination")
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        # On récupère tous les genres
        query = """
            SELECT 
                genre_id, 
                genre_title,
                genre_color,
                tracks
            FROM sae.genre
            ORDER BY tracks DESC
            LIMIT %s OFFSET %s
        """
        cur.execute(query, (limit, offset))
        genres = cur.fetchall()
        
        # Compter le total
        count_query = "SELECT COUNT(*) as total FROM sae.genre"
        cur.execute(count_query)
        total = cur.fetchone()['total']
        
        cur.close()
        conn.close()
        
        return {
            "total": total,
            "count": len(genres),
            "limit": limit,
            "offset": offset,
            "results": genres
        }
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/genres/{genre_id}/tracks")
def get_genre_tracks(
    genre_id: int,
    limit: Optional[int] = Query(50, ge=1, le=500, description="Nombre maximum de résultats"),
    offset: Optional[int] = Query(0, ge=0, description="Décalage pour la pagination")
):
    """
    Récupère toutes les musiques d'un genre spécifique.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        # Vérifier si le genre existe
        genre_query = "SELECT genre_title FROM sae.genre WHERE genre_id = %s"
        cur.execute(genre_query, (genre_id,))
        genre = cur.fetchone()
        
        if not genre:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Genre non trouvé")
        
        # Récupérer les tracks du genre
        query = """
            SELECT 
                t.track_id,
                t.track_title,
                t.track_duration,
                t.track_listens,
                t.track_file,
                t.track_favorite,
                art.artist_name,
                alb.album_title
            FROM sae.tracks t
            JOIN sae.track_genre tg ON t.track_id = tg.track_id
            JOIN sae.artist_album_track aat ON t.track_id = aat.track_id
            JOIN sae.artist art ON aat.artist_id = art.artist_id
            LEFT JOIN sae.album alb ON aat.album_id = alb.album_id
            WHERE tg.genre_id = %s
            ORDER BY t.track_listens DESC
            LIMIT %s OFFSET %s
        """
        
        cur.execute(query, (genre_id, limit, offset))
        tracks = cur.fetchall()
        
        # Compter le total
        count_query = """
            SELECT COUNT(*) as total
            FROM sae.track_genre
            WHERE genre_id = %s
        """
        cur.execute(count_query, (genre_id,))
        total = cur.fetchone()['total']
        
        cur.close()
        conn.close()
        
        return {
            "genre": genre['genre_title'],
            "total": total,
            "count": len(tracks),
            "limit": limit,
            "offset": offset,
            "tracks": tracks
        }
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ternaire/{genre}/{genre_secondaire}")
def get_all_id_ternaire(
    genre: str,
    genre_secondaire : str,
    limit: Optional[int] = Query(500, ge=1, le=500, description="Nombre maximum de résultats"),
    offset: Optional[int] = Query(0, ge=0, description="Décalage pour la pagination")
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        query = """
            SELECT DISTINCT
                e.artist_id,
                a.artist_name
            FROM sae.artist_album_track e
            INNER JOIN sae.tracks t ON e.track_id = t.track_id
            INNER JOIN sae.artist a ON e.artist_id = a.artist_id
            INNER JOIN sae.genre g ON g.genre_id = ANY(string_to_array(t.track_genre, ',')::int[])
            WHERE (t.track_genre_top = %s OR g.genre_title = %s)
            AND t.track_genre_top IS NOT NULL 
            AND t.track_genre_top != 'NaN'
            LIMIT %s OFFSET %s
        """
        cur.execute(query, (genre,genre_secondaire,limit, offset))
        id = cur.fetchall()
        
        count_query = "SELECT COUNT(*) as total FROM sae.artist_album_track"
        cur.execute(count_query)
        total = cur.fetchone()['total']
        
        cur.close()
        conn.close()
        
        return {
            "total": total,
            "count": len(id),
            "limit": limit,
            "offset": offset,
            "results": id
        }
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Lance le serveur sur le port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)