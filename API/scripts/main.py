from fastapi import FastAPI, HTTPException, Query
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional
from dotenv import load_dotenv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Recommendation'))

from item_based_pierre import recommend_similar_tracks
from item_based_stanislas import recommend_artists

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="API Muse")

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
    limit: Optional[int] = Query(50, ge=1, le=500, description="Nombre maximum de résultats"),
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
    limit: Optional[int] = Query(50, ge=1, le=500, description="Nombre maximum de résultats"),
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

@app.get("/tracks/{track_id}/reco")
def get_track_recommendations(
    track_id: int,
    limit: Optional[int] = Query(5, ge=1, le=50, description="Nombre de recommandations")
):
    try:
        # Vérifier si la track existe
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
        
        cur = conn.cursor()
        check_query = "SELECT track_id FROM sae.tracks WHERE track_id = %s"
        cur.execute(check_query, (track_id,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Track non trouvée")
        
        cur.close()
        conn.close()
        
        # Appeler la fonction de recommandation
        recommendations = recommend_similar_tracks(target_track_id=track_id, top_n=limit)

        if not recommendations:
            raise HTTPException(status_code=404, detail="Aucune recommandation possible")
        
        return {
            "target_track_id": track_id,
            "count": len(recommendations),
            "results": recommendations
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recommandation : {str(e)}")
    
@app.get("/artists/{artist_id}/reco")
def get_artist_recommendations(
    artist_id: int,
    limit: Optional[int] = Query(5, ge=1, le=50, description="Nombre d'artistes similaires")
):
    try:
        # Vérifier si l'artiste existe
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
        
        cur = conn.cursor()
        check_query = "SELECT artist_id FROM sae.artist WHERE artist_id = %s"
        cur.execute(check_query, (artist_id,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Artiste non trouvé")
        
        cur.close()
        conn.close()
        
        recommendations = recommend_artists(artist_id=artist_id, top_k=limit)
        
        if not recommendations:
            raise HTTPException(status_code=404, detail="Pas de recommandation disponible")
        
        return {
            "target_artist_id": artist_id,
            "count": len(recommendations),
            "results": recommendations
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur recommandation artiste : {str(e)}")

@app.get("/genres")
def get_all_genres(
    limit: Optional[int] = Query(50, ge=1, le=500, description="Nombre maximum de résultats"),
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

if __name__ == "__main__":
    import uvicorn
    # Lance le serveur sur le port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)