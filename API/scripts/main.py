from fastapi import FastAPI, HTTPException, Query
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from pydantic import BaseModel
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

@app.get("/users")
def get_all_users(
    limit: Optional[int] = Query(500, ge=1, le=500, description="Nombre maximum de résultats"),
    offset: Optional[int] = Query(0, ge=0, description="Décalage pour la pagination")
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        query = """
            SELECT *
            FROM sae.users
            LIMIT %s OFFSET %s
        """
        cur.execute(query, (limit, offset))
        users = cur.fetchall()
        
        count_query = "SELECT COUNT(*) as total FROM sae.users"
        cur.execute(count_query)
        total = cur.fetchone()['total']
        
        cur.close()
        conn.close()
        
        return {
            "total": total,
            "count": len(users),
            "limit": limit,
            "offset": offset,
            "users": users
        }
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))
class PlaylistCreate(BaseModel):
    name: str
    description: Optional[str] = None
    user_id: int
    track_ids: List[int] = []

class PlaylistUpdateTracks(BaseModel):
    track_ids: List[int]

@app.get("/users/{user_id}/playlists")
def get_user_playlists(user_id: int):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        query = """
            SELECT p.playlist_id, p.playlist_name, p.playlist_description, p.created_at
            FROM sae.playlist p
            JOIN sae.playlist_user pu ON p.playlist_id = pu.playlist_id
            WHERE pu.user_id = %s
        """
        cur.execute(query, (user_id,))
        return cur.fetchall()
    finally:
        conn.close()

@app.post("/playlists")
def create_playlist(data: PlaylistCreate):
    """
    Crée une nouvelle playlist avec ses informations et les musiques sélectionnées
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        # 1. Vérifier que l'utilisateur existe
        cur.execute("SELECT user_id FROM sae.users WHERE user_id = %s", (data.user_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        # 2. Créer la playlist - NOTE: created_at aura automatiquement NOW() grâce à DEFAULT
        cur.execute(
            """
            INSERT INTO sae.playlist (playlist_name, playlist_description) 
            VALUES (%s, %s) 
            RETURNING playlist_id
            """,
            (data.name, data.description)
        )
        result = cur.fetchone()
        playlist_id = result['playlist_id']
        
        # 3. Lier la playlist à l'utilisateur
        cur.execute(
            "INSERT INTO sae.playlist_user (playlist_id, user_id) VALUES (%s, %s)",
            (playlist_id, data.user_id)
        )
        
        # 4. Ajouter les musiques sélectionnées à la playlist
        tracks_added = 0
        if data.track_ids and len(data.track_ids) > 0:
            for track_id in data.track_ids:
                try:
                    cur.execute(
                        "INSERT INTO sae.playlist_track (playlist_id, track_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        (playlist_id, track_id)
                    )
                    tracks_added += 1
                except Exception as e:
                    print(f"Erreur ajout track {track_id}: {e}")
                    continue
        
        conn.commit()
        
        return {
            "message": "Playlist créée avec succès",
            "playlist_id": playlist_id,
            "playlist_name": data.name,
            "tracks_added": tracks_added
        }
        
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"Erreur détaillée: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()

@app.delete("/playlists/{playlist_id}")
def delete_playlist(playlist_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        # Désactiver temporairement les triggers si nécessaire
        cur.execute("SET session_replication_role = 'replica';")
        
        # Supprimer dans le bon ordre
        cur.execute("DELETE FROM sae.playlist_track WHERE playlist_id = %s", (playlist_id,))
        cur.execute("DELETE FROM sae.playlist_user WHERE playlist_id = %s", (playlist_id,))
        cur.execute("DELETE FROM sae.playlist WHERE playlist_id = %s", (playlist_id,))
        
        # Réactiver les triggers
        cur.execute("SET session_replication_role = 'origin';")
        
        conn.commit()
        return {"message": "Playlist supprimée"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/playlists/{playlist_id}/tracks")
def update_tracks_in_playlist(playlist_id: int, data: PlaylistUpdateTracks):
    """Remplace ou ajoute des musiques (Logique de mise à jour complète)"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # On vide la playlist actuelle pour simplifier la mise à jour
        cur.execute("DELETE FROM sae.playlist_track WHERE playlist_id = %s", (playlist_id,))
        for t_id in data.track_ids:
            cur.execute("INSERT INTO sae.playlist_track (playlist_id, track_id) VALUES (%s, %s)", (playlist_id, t_id))
        conn.commit()
        return {"message": "Liste de lecture mise à jour"}
    finally:
        conn.close()

@app.get("/users/{user_id}/playlists/detailed")
def get_user_playlists_detailed(user_id: int):
    """
    Récupère les playlists d'un utilisateur avec leurs détails (nombre de tracks, etc.)
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        query = """
            SELECT 
                p.playlist_id, 
                p.playlist_name, 
                p.playlist_description, 
                p.created_at,
                COUNT(DISTINCT pt.track_id) as tracks_count
            FROM sae.playlist p
            JOIN sae.playlist_user pu ON p.playlist_id = pu.playlist_id
            LEFT JOIN sae.playlist_track pt ON p.playlist_id = pt.playlist_id
            WHERE pu.user_id = %s
            GROUP BY p.playlist_id, p.playlist_name, p.playlist_description, p.created_at
            ORDER BY p.created_at DESC
        """
        
        cur.execute(query, (user_id,))
        playlists = cur.fetchall()
        
        # Pour chaque playlist, récupérer les premières tracks (pour afficher un aperçu)
        for playlist in playlists:
            tracks_query = """
                SELECT 
                    t.track_id,
                    t.track_title,
                    t.track_image_file,
                    ar.artist_name
                FROM sae.playlist_track pt
                JOIN sae.tracks t ON pt.track_id = t.track_id
                LEFT JOIN sae.artist_album_track aat ON t.track_id = aat.track_id
                LEFT JOIN sae.artist ar ON aat.artist_id = ar.artist_id
                WHERE pt.playlist_id = %s
                LIMIT 4
            """
            cur.execute(tracks_query, (playlist['playlist_id'],))
            playlist['preview_tracks'] = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return {
            "user_id": user_id,
            "count": len(playlists),
            "playlists": playlists
        }
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/playlists/{playlist_id}")
def get_playlist_by_id(playlist_id: int):
    """
    Récupère une playlist spécifique avec toutes ses tracks
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        # Récupérer les infos de la playlist
        playlist_query = """
            SELECT 
                p.playlist_id,
                p.playlist_name,
                p.playlist_description,
                p.created_at,
                pu.user_id
            FROM sae.playlist p
            JOIN sae.playlist_user pu ON p.playlist_id = pu.playlist_id
            WHERE p.playlist_id = %s
        """
        cur.execute(playlist_query, (playlist_id,))
        playlist = cur.fetchone()
        
        if not playlist:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Playlist non trouvée")
        
        # Récupérer toutes les tracks de la playlist
        tracks_query = """
            SELECT 
                t.track_id,
                t.track_title,
                t.track_duration,
                t.track_genre_top,
                t.track_listens,
                t.track_file,
                t.track_image_file,
                STRING_AGG(DISTINCT ar.artist_name, ', ') as artist_names,
                STRING_AGG(DISTINCT alb.album_title, ', ') as album_titles
            FROM sae.playlist_track pt
            JOIN sae.tracks t ON pt.track_id = t.track_id
            LEFT JOIN sae.artist_album_track aat ON t.track_id = aat.track_id
            LEFT JOIN sae.artist ar ON aat.artist_id = ar.artist_id
            LEFT JOIN sae.album alb ON aat.album_id = alb.album_id
            WHERE pt.playlist_id = %s
            GROUP BY t.track_id, t.track_title, t.track_duration, t.track_genre_top, 
                     t.track_listens, t.track_file, t.track_image_file
            ORDER BY pt.track_id
        """
        cur.execute(tracks_query, (playlist_id,))
        tracks = cur.fetchall()
        
        playlist['tracks'] = tracks
        playlist['tracks_count'] = len(tracks)
        
        cur.close()
        conn.close()
        
        return playlist
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/playlists/{playlist_id}/tracks/{track_id}")
def remove_track_from_playlist(playlist_id: int, track_id: int):
    """
    Supprime une track spécifique d'une playlist
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        # Vérifier si la track existe dans la playlist
        check_query = """
            SELECT * FROM sae.playlist_track 
            WHERE playlist_id = %s AND track_id = %s
        """
        cur.execute(check_query, (playlist_id, track_id))
        if not cur.fetchone():
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Cette track n'est pas dans la playlist")
        
        # Supprimer la track
        cur.execute(
            "DELETE FROM sae.playlist_track WHERE playlist_id = %s AND track_id = %s",
            (playlist_id, track_id)
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"message": "Track supprimée de la playlist"}
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/tracks")
def search_tracks(
    query: str = Query(..., description="Terme de recherche"),
    limit: Optional[int] = Query(10, ge=1, le=50, description="Nombre maximum de résultats")
):
    """
    Recherche des musiques par titre ou artiste
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        search_query = """
            SELECT DISTINCT
                t.track_id,
                t.track_title,
                t.track_duration,
                t.track_genre_top,
                t.track_image_file,
                STRING_AGG(DISTINCT ar.artist_name, ', ') as artist_names,
                STRING_AGG(DISTINCT alb.album_title, ', ') as album_titles
            FROM sae.tracks t
            LEFT JOIN sae.artist_album_track aat ON t.track_id = aat.track_id
            LEFT JOIN sae.artist ar ON aat.artist_id = ar.artist_id
            LEFT JOIN sae.album alb ON aat.album_id = alb.album_id
            WHERE 
                t.track_title ILIKE %s
                OR ar.artist_name ILIKE %s
                OR alb.album_title ILIKE %s
            GROUP BY t.track_id, t.track_title, t.track_duration, 
                     t.track_genre_top, t.track_image_file
            LIMIT %s
        """
        
        search_term = f"%{query}%"
        cur.execute(search_query, (search_term, search_term, search_term, limit))
        tracks = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return {
            "query": query,
            "count": len(tracks),
            "results": tracks
        }
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Lance le serveur sur le port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)