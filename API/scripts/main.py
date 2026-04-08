from fastapi import FastAPI, HTTPException, Query, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from pydantic import BaseModel
import os
import shutil
import uuid
import sys
import math
import bcrypt
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Recommendation'))

from item_based_pierre import recommend_similar_tracks
from item_based_stanislas import recommend_artists, initialize_artist_system

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_artist_system()
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("ALTER TABLE sae.playlist_track ADD COLUMN IF NOT EXISTS position INT DEFAULT 0;")
            cur.execute("""
                WITH numbered AS (
                    SELECT ctid, ROW_NUMBER() OVER (PARTITION BY playlist_id ORDER BY track_id) - 1 AS pos
                    FROM sae.playlist_track
                    WHERE position = 0
                )
                UPDATE sae.playlist_track SET position = numbered.pos
                FROM numbered WHERE sae.playlist_track.ctid = numbered.ctid AND sae.playlist_track.position = 0;
            """)
            cur.execute("ALTER TABLE sae.playlist ADD COLUMN IF NOT EXISTS playlist_image TEXT;")
            conn.commit()
            cur.close()
            conn.close()
            
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sae.user_reaction (
                    user_id INT REFERENCES sae.users(user_id),
                    target_type VARCHAR(20) NOT NULL,
                    target_id INT NOT NULL,
                    liked BOOLEAN DEFAULT FALSE,
                    disliked BOOLEAN DEFAULT FALSE,
                    favorite BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (user_id, target_type, target_id)
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
    except Exception as e:
        print(f"Migration warning: {e}")
    yield

tags_metadata = [
    {"name": "Général",          "description": "Endpoint racine de l'API."},
    {"name": "Tracks",           "description": "Accès aux musiques : liste, détails complets (audio features, album, artiste associés)."},
    {"name": "Artistes",         "description": "Accès aux artistes : liste, profil complet, discographie."},
    {"name": "Albums",           "description": "Accès aux albums : liste, détails, tracklist complète."},
    {"name": "Genres",           "description": "Liste des genres musicaux et leurs musiques associées."},
    {"name": "Recommandations",  "description": "Moteur de recommandations basé sur la similarité entre musiques et artistes (item-based)."},
    {"name": "Playlists",        "description": "Création, consultation, modification et suppression de playlists utilisateur."},
    {"name": "Utilisateurs",     "description": "Consultation et gestion du profil utilisateur (playlists, mise à jour, suppression)."},
    {"name": "Recherche",        "description": "Recherche textuelle de musiques par titre, artiste ou album."},
    {"name": "Favoris",          "description": "Consultation et enregistrement des favoris (tracks, artistes, genres) d'un utilisateur."},
    {"name": "Blindtests",       "description": "Génération de sessions de jeu et historique de l'utilisateur."},
    {"name": "Admin",            "description": "⚙️ Endpoints d'administration — statistiques globales, gestion des utilisateurs, modération du contenu."},
]

app = FastAPI(
    title="API 10Heures",
    description="API pour accéder à la base de données musicale 10Heures, gérer des playlists et obtenir des recommandations personnalisées.",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    docs_url=None,
)

web_dir = os.path.join(os.path.dirname(__file__), '..', 'web')
app.mount("/static", StaticFiles(directory=web_dir), name="static")

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), '..', 'web', 'uploads')
os.makedirs(os.path.join(UPLOADS_DIR, 'playlists'), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

@app.get("/docs", include_in_schema=False)
async def custom_swagger_docs():
    return HTMLResponse('''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Documentation - API 10Heures</title>
    <link rel="icon" type="image/png" sizes="32x32" href="/static/images/logos/muse.png">
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css"/>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: sans-serif; color: #000; font-size: 0.875rem; }
        .swagger-ui .topbar { display: none; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        SwaggerUIBundle({
            url: "/openapi.json",
            dom_id: "#swagger-ui",
            presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
            layout: "BaseLayout",
            deepLinking: true,
            defaultModelsExpandDepth: -1
        });
    </script>
</body>
</html>
    ''')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

DB_CONFIG = {
    "host": "localhost",
    "dbname": os.getenv("POSTGRES_DBNAME"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "port": int(os.getenv("POSTGRES_PORT", 5432))
}

def clean_nan(obj):
    if isinstance(obj, float) and math.isnan(obj): return None
    elif isinstance(obj, dict): return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list): return [clean_nan(v) for v in obj]
    return obj

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        return None

# =================================================================
# ===== GENERAL & TRACKS =====
# =================================================================

@app.get("/", tags=["Général"], summary="Accueil de l'API")
def read_root():
    return {"message": "Bienvenue sur l'API de Muse!"}

@app.get("/tracks", tags=["Tracks"], summary="Liste de toutes les musiques")
def get_all_tracks(limit: Optional[int] = Query(50, ge=1, le=100000), offset: Optional[int] = Query(0, ge=0)):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="DB Error")
    try:
        cur = conn.cursor()
        query = """
            SELECT tf.track_id, tf.track_title, tf.track_duration, tf.track_genre_top,
                   tf.track_listens, tf.track_file, tf.album_titles, tf.artist_names,
                   tf.audio_features_instrumentalness, tf.audio_features_speechiness,
                   t.track_language_code
            FROM sae.tracks_features tf
            LEFT JOIN sae.tracks t ON tf.track_id = t.track_id
            ORDER BY tf.track_listens DESC LIMIT %s OFFSET %s
        """
        cur.execute(query, (limit, offset))
        tracks = cur.fetchall()
        
        cur.execute("SELECT COUNT(*) as total FROM sae.tracks")
        total = cur.fetchone()['total']
        cur.close(); conn.close()
        
        return {"total": total, "count": len(tracks), "limit": limit, "offset": offset, "results": tracks}
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tracks/{track_id}", tags=["Tracks"], summary="Détails complets d'une musique")
def get_track_by_id(track_id: int):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="DB error")
    try:
        cur = conn.cursor()
        query = "SELECT * FROM sae.tracks_features WHERE track_id = %s"
        cur.execute(query, (track_id,))
        track = cur.fetchone()
        if not track:
            cur.close(); conn.close()
            raise HTTPException(status_code=404, detail="Musique non trouvée")
        
        cur.execute("SELECT g.genre_title FROM sae.track_genre tg JOIN sae.genre g ON tg.genre_id = g.genre_id WHERE tg.track_id = %s", (track_id,))
        track['genres'] = [g['genre_title'] for g in cur.fetchall()]
        
        if track['album_ids']:
            album_id = track['album_ids'].split(',')[0]
            cur.execute("SELECT album_id, album_title, album_type, album_tracks, album_image_file, album_date_released FROM sae.album WHERE album_id = %s", (int(album_id),))
            track['album_info'] = cur.fetchone()
        
        if track['artist_ids']:
            artist_id = track['artist_ids'].split(',')[0]
            cur.execute("SELECT artist_id, artist_name, artist_bio, artist_location, artist_favorites, artist_website FROM sae.artist WHERE artist_id = %s", (int(artist_id),))
            track['artist_info'] = cur.fetchone()
        
        cur.close(); conn.close()
        return clean_nan(track)
    except HTTPException: raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

# =================================================================
# ===== ARTISTS & ALBUMS =====
# =================================================================

@app.get("/artists", tags=["Artistes"], summary="Liste de tous les artistes")
def get_artists(
    limit: Optional[int] = Query(50, ge=1, le=100000, description="Nombre maximum de résultats"),
    offset: Optional[int] = Query(0, ge=0, description="Décalage pour la pagination")
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        query = """
            SELECT artist_id, artist_name, artist_location, artist_favorites,
                   artist_active_year_begin, artist_active_year_end, artist_tags, artist_image_file
            FROM sae.artist ORDER BY artist_favorites DESC LIMIT %s OFFSET %s
        """
        cur.execute(query, (limit, offset))
        artists = cur.fetchall()
        
        cur.execute("SELECT COUNT(*) as total FROM sae.artist")
        total = cur.fetchone()['total']
        cur.close()
        conn.close()
        
        return {"total": total, "count": len(artists), "limit": limit, "offset": offset, "results": artists}
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/artists/{artist_id}", tags=["Artistes"], summary="Détails complets d'un artiste")
def get_artist_by_id(artist_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        query = """
            SELECT artist_id, artist_name, artist_bio, artist_location, artist_favorites,
                   artist_active_year_begin, artist_active_year_end, artist_tags,
                   artist_image_file, artist_website, artist_associated_label
            FROM sae.artist WHERE artist_id = %s
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

@app.get("/artists/{artist_id}/tracks", tags=["Artistes"], summary="Musiques d'un artiste")
def get_artist_tracks(
    artist_id: int,
    limit: Optional[int] = Query(50, ge=1, le=500, description="Nombre maximum de résultats"),
    offset: Optional[int] = Query(0, ge=0, description="Décalage pour la pagination")
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT artist_name FROM sae.artist WHERE artist_id = %s", (artist_id,))
        artist = cur.fetchone()
        if not artist:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Artiste non trouvé")
        
        query = """
            SELECT DISTINCT t.track_id, t.track_title, t.track_duration, t.track_genre_top,
                   t.track_listens, t.track_favorite, t.track_file, aat.album_id, a.album_title, a.album_image_file
            FROM sae.tracks t
            JOIN sae.artist_album_track aat ON t.track_id = aat.track_id
            LEFT JOIN sae.album a ON aat.album_id = a.album_id
            WHERE aat.artist_id = %s ORDER BY t.track_listens DESC LIMIT %s OFFSET %s
        """
        cur.execute(query, (artist_id, limit, offset))
        tracks = cur.fetchall()
        
        cur.execute("""
            SELECT COUNT(DISTINCT t.track_id) as total
            FROM sae.tracks t JOIN sae.artist_album_track aat ON t.track_id = aat.track_id
            WHERE aat.artist_id = %s
        """, (artist_id,))
        total = cur.fetchone()['total']
        
        cur.close()
        conn.close()
        return {"artist": artist['artist_name'], "total": total, "count": len(tracks), "limit": limit, "offset": offset, "tracks": tracks}
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/albums", tags=["Albums"], summary="Liste de tous les albums")
def get_albums(
    limit: Optional[int] = Query(50, ge=1, le=500, description="Nombre maximum de résultats"),
    offset: Optional[int] = Query(0, ge=0, description="Décalage pour la pagination"),
    title: Optional[str] = Query(None, description="Filtrer par titre d'album")
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        base_query = """
            SELECT album_id, album_title, album_type, album_tracks, album_listens,
                   album_favorites, album_image_file, album_date_released, album_tags, artists
            FROM sae.album_features WHERE 1=1
        """
        params = []
        if title:
            base_query += " AND album_title ILIKE %s"
            params.append(f"%{title}%")
        
        base_query += " ORDER BY album_date_released DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        cur.execute(base_query, params)
        albums = cur.fetchall()
        
        count_query = "SELECT COUNT(*) as total FROM sae.album"
        if title:
            count_query += " WHERE album_title ILIKE %s"
            cur.execute(count_query, (f"%{title}%",))
        else:
            cur.execute(count_query)
        total = cur.fetchone()['total']
        
        cur.close()
        conn.close()
        return {"total": total, "count": len(albums), "limit": limit, "offset": offset, "results": albums}
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/albums/{album_id}", tags=["Albums"], summary="Détails complets d'un album")
def get_album_by_id(album_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    try:
        cur = conn.cursor()
        query = """
            SELECT album_id, album_title, album_type, album_tracks, album_listens,
                   album_favorites, album_image_file, album_date_released, album_tags, artists
            FROM sae.album_features WHERE album_id = %s
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

@app.get("/albums/{album_id}/tracks", tags=["Albums"], summary="Musiques d'un album")
def get_album_tracks(
    album_id: int,
    limit: Optional[int] = Query(50, ge=1, le=500, description="Nombre maximum de résultats"),
    offset: Optional[int] = Query(0, ge=0, description="Décalage pour la pagination")
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        album_query = "SELECT album_title, album_type, album_tracks, album_image_file, album_date_released FROM sae.album WHERE album_id = %s"
        cur.execute(album_query, (album_id,))
        album = cur.fetchone()
        
        if not album:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Album non trouvé")
        
        tracks_query = """
            SELECT t.track_id, t.track_title, t.track_duration, t.track_genre_top,
                   t.track_listens, t.track_file, t.track_favorite, art.artist_name
            FROM sae.tracks t
            JOIN sae.artist_album_track aat ON t.track_id = aat.track_id
            JOIN sae.artist art ON aat.artist_id = art.artist_id
            WHERE aat.album_id = %s
            ORDER BY t.track_disk_number, t.track_title LIMIT %s OFFSET %s
        """
        cur.execute(tracks_query, (album_id, limit, offset))
        tracks = cur.fetchall()
        
        artists_query = """
            SELECT DISTINCT art.artist_name FROM sae.artist_album_track aat
            JOIN sae.artist art ON aat.artist_id = art.artist_id WHERE aat.album_id = %s
        """
        cur.execute(artists_query, (album_id,))
        artists = cur.fetchall()
        
        cur.execute("SELECT COUNT(*) as total FROM sae.artist_album_track WHERE album_id = %s", (album_id,))
        total = cur.fetchone()['total']
        
        cur.close()
        conn.close()
        return {"album": album, "artists": [artist['artist_name'] for artist in artists], "total": total, "count": len(tracks), "limit": limit, "offset": offset, "tracks": tracks}
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

# =================================================================
# ===== REACTIONS & FAVORIS =====
# =================================================================

@app.post("/reactions/{target_type}/{target_id}")
def toggle_reaction(target_type: str, target_id: int, payload: dict):
    if target_type not in ("artist", "album", "track"):
        raise HTTPException(status_code=400, detail="target_type must be 'artist', 'album' or 'track'")

    user_id = payload.get("user_id")
    action = payload.get("action")
    value = payload.get("value")

    if not user_id or action not in ("like", "dislike", "favorite") or not isinstance(value, bool):
        raise HTTPException(status_code=400, detail="Invalid payload")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB connexion failed")

    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM sae.users WHERE user_id = %s", (user_id,))
        if not cur.fetchone():
            cur.close(); conn.close()
            raise HTTPException(status_code=404, detail="User not found")

        if target_type == "artist":
            cur.execute("SELECT artist_id FROM sae.artist WHERE artist_id = %s", (target_id,))
        elif target_type == "album":
            cur.execute("SELECT album_id FROM sae.album WHERE album_id = %s", (target_id,))
        else:
            cur.execute("SELECT track_id FROM sae.tracks WHERE track_id = %s", (target_id,))
        if not cur.fetchone():
            cur.close(); conn.close()
            raise HTTPException(status_code=404, detail=f"{target_type} not found")

        liked = False; disliked = False; favorite = False
        if action == "like":
            liked = value
            if value:
                disliked = False
            favorite = value
        elif action == "dislike":
            disliked = value
            if value:
                liked = False
            favorite = False
        elif action == "favorite":
            favorite = value

        cur.execute("""
            INSERT INTO sae.user_reaction (user_id, target_type, target_id, liked, disliked, favorite, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (user_id, target_type, target_id) DO UPDATE
            SET liked = EXCLUDED.liked,
                disliked = EXCLUDED.disliked,
                favorite = EXCLUDED.favorite,
                updated_at = NOW();
        """, (user_id, target_type, target_id, liked, disliked, favorite))

        if action == "favorite":
            if favorite:
                if target_type == "artist":
                    cur.execute("UPDATE sae.artist SET artist_favorites = COALESCE(artist_favorites,0) + 1 WHERE artist_id = %s", (target_id,))
                elif target_type == "album":
                    cur.execute("UPDATE sae.album SET album_favorites = COALESCE(album_favorites,0) + 1 WHERE album_id = %s", (target_id,))
                else:
                    cur.execute("UPDATE sae.tracks SET track_favorite = COALESCE(track_favorite,0) + 1 WHERE track_id = %s", (target_id,))
            else:
                if target_type == "artist":
                    cur.execute("UPDATE sae.artist SET artist_favorites = GREATEST(COALESCE(artist_favorites,0) - 1, 0) WHERE artist_id = %s", (target_id,))
                elif target_type == "album":
                    cur.execute("UPDATE sae.album SET album_favorites = GREATEST(COALESCE(album_favorites,0) - 1, 0) WHERE album_id = %s", (target_id,))
                else:
                    cur.execute("UPDATE sae.tracks SET track_favorite = GREATEST(COALESCE(track_favorite,0) - 1, 0) WHERE track_id = %s", (target_id,))

        if target_type == 'track' and action in ('like', 'dislike'):
            try:
                def _maybe_delete_playlist(cur, pid):
                    cur.execute("SELECT COUNT(*) as cnt FROM sae.playlist_track WHERE playlist_id = %s", (pid,))
                    cnt = cur.fetchone()['cnt']
                    if cnt == 0:
                        cur.execute("SELECT playlist_image FROM sae.playlist WHERE playlist_id = %s", (pid,))
                        img = cur.fetchone()
                        image_file = img.get('playlist_image') if img else None
                        cur.execute("DELETE FROM sae.playlist_user WHERE playlist_id = %s", (pid,))
                        cur.execute("DELETE FROM sae.playlist WHERE playlist_id = %s", (pid,))
                        if image_file:
                            try:
                                image_path = os.path.join(os.path.dirname(__file__), '..', 'web', 'uploads', 'playlists', image_file)
                                if os.path.exists(image_path):
                                    os.remove(image_path)
                            except Exception:
                                pass

                if action == 'like':
                    if liked:
                        cur.execute("SELECT p.playlist_id FROM sae.playlist p JOIN sae.playlist_user pu ON p.playlist_id=pu.playlist_id WHERE pu.user_id=%s AND lower(trim(p.playlist_name)) = 'titres liké'", (user_id,))
                        row = cur.fetchone()
                        if row:
                            pid = row['playlist_id']
                        else:
                            cur.execute("INSERT INTO sae.playlist (playlist_name, playlist_description) VALUES (%s,%s) RETURNING playlist_id", ('Titres liké','Playlist de titres likés'))
                            pid = cur.fetchone()['playlist_id']
                            cur.execute("INSERT INTO sae.playlist_user (playlist_id, user_id) VALUES (%s,%s)", (pid, user_id))
                        cur.execute("INSERT INTO sae.playlist_track (playlist_id, track_id, position) VALUES (%s,%s, COALESCE((SELECT MAX(position)+1 FROM sae.playlist_track WHERE playlist_id=%s), 0)) ON CONFLICT DO NOTHING", (pid, target_id, pid))
                    else:
                        cur.execute("SELECT p.playlist_id FROM sae.playlist p JOIN sae.playlist_user pu ON p.playlist_id=pu.playlist_id WHERE pu.user_id=%s AND lower(trim(p.playlist_name)) = 'titres liké'", (user_id,))
                        row = cur.fetchone()
                        if row:
                            pid = row['playlist_id']
                            cur.execute("DELETE FROM sae.playlist_track WHERE playlist_id=%s AND track_id=%s", (pid, target_id))
                            _maybe_delete_playlist(cur, pid)

                if action == 'dislike':
                    if disliked:
                        cur.execute("SELECT p.playlist_id FROM sae.playlist p JOIN sae.playlist_user pu ON p.playlist_id=pu.playlist_id WHERE pu.user_id=%s AND lower(trim(p.playlist_name)) = 'titres liké'", (user_id,))
                        row2 = cur.fetchone()
                        if row2:
                            pid2 = row2['playlist_id']
                            cur.execute("DELETE FROM sae.playlist_track WHERE playlist_id=%s AND track_id=%s", (pid2, target_id))
                            _maybe_delete_playlist(cur, pid2)
            except Exception:
                pass

        try:
            if target_type == 'track':
                cur.execute("SELECT user_favorite_tracks FROM sae.favorite WHERE user_id = %s", (user_id,))
                fav_row = cur.fetchone()
                existing = ''
                if fav_row and fav_row.get('user_favorite_tracks'):
                    existing = fav_row.get('user_favorite_tracks')
                parts = [p for p in (existing or '').split(',') if p.strip()]
                str_tid = str(target_id)
                if liked:
                    if str_tid not in parts:
                        parts.append(str_tid)
                else:
                    parts = [p for p in parts if p != str_tid]

                new_val = ','.join(parts)
                if fav_row:
                    cur.execute("UPDATE sae.favorite SET user_favorite_tracks = %s WHERE user_id = %s", (new_val, user_id))
                else:
                    cur.execute("INSERT INTO sae.favorite (user_favorite_tracks, user_favorite_artist, user_favorite_genre, user_id) VALUES (%s,%s,%s,%s)", (new_val, '', '', user_id))
        except Exception:
            pass

        conn.commit()
        cur.execute("SELECT liked, disliked, favorite FROM sae.user_reaction WHERE user_id=%s AND target_type=%s AND target_id=%s", (user_id, target_type, target_id))
        state = cur.fetchone()
        cur.close()
        conn.close()

        return {"success": True, "reaction": state}
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reactions/{target_type}/{target_id}/{user_id}")
def get_reaction(target_type: str, target_id: int, user_id: int):
    if target_type not in ("artist", "album", "track"):
        raise HTTPException(status_code=400, detail="target_type must be 'artist', 'album' or 'track'")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB connexion failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT liked, disliked, favorite FROM sae.user_reaction WHERE user_id=%s AND target_type=%s AND target_id=%s", (user_id, target_type, target_id))
        state = cur.fetchone()
        cur.close(); conn.close()
        if not state:
            return {"liked": False, "disliked": False, "favorite": False}
        return state
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/disliked_tracks")
def get_user_disliked_tracks(user_id: int, limit: Optional[int] = Query(200, ge=1, le=2000), offset: Optional[int] = Query(0, ge=0)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB connexion failed")
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT t.track_id, t.track_title, t.track_duration, t.track_genre_top, t.track_listens, t.track_file, t.track_image_file,
                   (SELECT string_agg(art.artist_name, ', ') FROM sae.artist art JOIN sae.artist_album_track aat ON art.artist_id = aat.artist_id WHERE aat.track_id = t.track_id) AS artist_names
            FROM sae.user_reaction ur
            JOIN sae.tracks t ON ur.target_id = t.track_id
            WHERE ur.user_id = %s AND ur.target_type = 'track' AND ur.disliked = TRUE
            ORDER BY ur.updated_at DESC
            LIMIT %s OFFSET %s
        """, (user_id, limit, offset))
        tracks = cur.fetchall()
        cur.close(); conn.close()
        return {"playlist_name": "Titres dislike", "playlist_description": "Titres que vous avez dislikés", "tracks": tracks, "count": len(tracks)}
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voir_favorite/{user_id}", tags=["Favoris"], summary="Favoris d'un utilisateur")
def get_all_favorite(user_id : int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        query = """
            SELECT 
                f.favorite_id,
                f.user_id,
                (SELECT string_agg(a.artist_name, ', ') 
                 FROM sae.artist a 
                 WHERE a.artist_id::text = ANY(string_to_array(f.user_favorite_artist, ','))) as user_favorite_artist,
                (SELECT string_agg(t.track_title, ', ') 
                 FROM sae.tracks t 
                 WHERE t.track_id::text = ANY(string_to_array(f.user_favorite_tracks, ','))) as user_favorite_tracks,
                (SELECT string_agg(g.genre_title, ', ') 
                 FROM sae.genre g 
                 WHERE g.genre_id::text = ANY(string_to_array(f.user_favorite_genre, ','))) as user_favorite_genre,
                f.user_favorite_artist as ids_artists,
                f.user_favorite_tracks as ids_tracks,
                f.user_favorite_genre as ids_genres
            FROM sae.favorite f
            WHERE f.user_id = %s
            ORDER BY f.favorite_id DESC
            LIMIT 1
        """
        cur.execute(query, (user_id,))
        tracks = cur.fetchall()
        
        count_query = "SELECT COUNT(*) as total FROM sae.favorite"
        cur.execute(count_query)
        total = cur.fetchone()['total']
        
        cur.close()
        conn.close()
        
        return {
            "total": total,
            "count": len(tracks),
            "results": tracks
        }
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-favorites", tags=["Favoris"], summary="Enregistrer les favoris d'un utilisateur")
async def saveFavorite(request : Request):
    conn = get_db_connection()

    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    data = await request.json()
    
    user_id = data.get("user_id")
    genres_str = ",".join(map(str, data.get("genres", [])))
    artists_str = ",".join(map(str, data.get("artists", [])))
    tracks_str = ",".join(map(str, data.get("tracks", [])))

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id manquant")

    try:
        cur = conn.cursor()
        query = """
            INSERT INTO sae.favorite
                (user_favorite_tracks,user_favorite_artist,user_favorite_genre,user_id) 
            VALUES (%s,%s,%s,%s)
            ON CONFLICT (user_id) 
            DO UPDATE SET 
                user_favorite_genre = EXCLUDED.user_favorite_genre,
                user_favorite_artist = EXCLUDED.user_favorite_artist,
                user_favorite_tracks = EXCLUDED.user_favorite_tracks;
        """
        cur.execute(query, (tracks_str,artists_str,genres_str,user_id))
        conn.commit()
        cur.close()
        conn.close()
        
        return {"success": True}

    except Exception as e:
        print(f"Erreur : {e}")
        return {"success": False, "error": str(e)}

# =================================================================
# ===== RECOMMENDATIONS =====
# =================================================================

@app.get("/reco/tracks", tags=["Recommandations"], summary="Recommandations de musiques similaires")
def recommend_tracks(
    track_ids: List[int] = Query(..., description="One or more track IDs to base recommendations on"),
    limit: int = Query(10, ge=1, le=50),
    exclude_user_id: Optional[int] = Query(None, description="Optional user id whose disliked tracks should be excluded")
):
    try:
        recommendations = recommend_similar_tracks(track_ids, top_n=limit)

        if not recommendations:
            raise HTTPException(status_code=404, detail="No recommendations found for the given IDs")

        if exclude_user_id is not None:
            try:
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor()
                    cur.execute("SELECT target_id FROM sae.user_reaction WHERE user_id=%s AND target_type='track' AND disliked = TRUE", (exclude_user_id,))
                    rows = cur.fetchall()
                    disliked = set(r['target_id'] for r in rows) if rows else set()
                    cur.close()
                    conn.close()
                else:
                    disliked = set()
            except Exception:
                disliked = set()

            def _id_of(item):
                if isinstance(item, dict):
                    return item.get('track_id') or item.get('trackId') or item.get('id')
                return int(item)

            filtered = [r for r in recommendations if (_id_of(r) not in disliked)]
        else:
            filtered = recommendations

        return {
            "input_ids": track_ids,
            "count": len(filtered),
            "results": filtered
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reco/artists", tags=["Recommandations"], summary="Recommandations d'artistes similaires")
def get_artist_recommendations(
    artist_ids: List[int] = Query(..., description="One or more artist IDs to base recommendations on"),
    limit: int = Query(5, ge=1, le=50)
):
    try:
        recommendations = recommend_artists(artist_ids=artist_ids, top_k=limit)
        
        if not recommendations:
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

# =================================================================
# ===== GENRES =====
# =================================================================

@app.get("/genres", tags=["Genres"], summary="Liste de tous les genres")
def get_all_genres(
    limit: Optional[int] = Query(500, ge=1, le=500, description="Nombre maximum de résultats"),
    offset: Optional[int] = Query(0, ge=0, description="Décalage pour la pagination")
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
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

@app.get("/genres/{genre_id}/tracks", tags=["Genres"], summary="Musiques d'un genre")
def get_genre_tracks(
    genre_id: int,
    limit: Optional[int] = Query(50, ge=1, le=500, description="Nombre maximum de résultats"),
    offset: Optional[int] = Query(0, ge=0, description="Décalage pour la pagination")
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        genre_query = "SELECT genre_title FROM sae.genre WHERE genre_id = %s"
        cur.execute(genre_query, (genre_id,))
        genre = cur.fetchone()
        
        if not genre:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Genre non trouvé")
        
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

# =================================================================
# ===== PLAYLISTS =====
# =================================================================

class PlaylistCreate(BaseModel):
    name: str
    description: Optional[str] = None
    user_id: int
    track_ids: List[int] = []

class PlaylistUpdateTracks(BaseModel):
    track_ids: List[int]

class PlaylistUpdateInfo(BaseModel):
    name: str
    description: Optional[str] = None

@app.post("/playlists", tags=["Playlists"], summary="Créer une nouvelle playlist")
def create_playlist(data: PlaylistCreate):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM sae.users WHERE user_id = %s", (data.user_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
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
        
        cur.execute(
            "INSERT INTO sae.playlist_user (playlist_id, user_id) VALUES (%s, %s)",
            (playlist_id, data.user_id)
        )
        
        tracks_added = 0
        if data.track_ids and len(data.track_ids) > 0:
            for idx, track_id in enumerate(data.track_ids):
                try:
                    cur.execute(
                        "INSERT INTO sae.playlist_track (playlist_id, track_id, position) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                        (playlist_id, track_id, idx)
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

@app.get("/playlists/{playlist_id}", tags=["Playlists"], summary="Détails complets d'une playlist")
def get_playlist_by_id(playlist_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        playlist_query = """
            SELECT 
                p.playlist_id,
                p.playlist_name,
                p.playlist_description,
                p.playlist_image,
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
            ORDER BY MIN(pt.position)
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

@app.delete("/playlists/{playlist_id}", tags=["Playlists"], summary="Supprimer une playlist")
def delete_playlist(playlist_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT playlist_name, playlist_image FROM sae.playlist WHERE playlist_id = %s", (playlist_id,))
        row = cur.fetchone()
        playlist_name = None
        playlist_image = None
        if row:
            playlist_name = row.get('playlist_name')
            playlist_image = row.get('playlist_image')

        try:
            if playlist_name and playlist_name.lower().strip() in ('titres liké',):
                cur.execute("SELECT user_id FROM sae.playlist_user WHERE playlist_id = %s", (playlist_id,))
                users = cur.fetchall()
                user_ids = [u['user_id'] for u in users if u.get('user_id')]
                if user_ids:
                    cur.execute(
                        "DELETE FROM sae.user_reaction WHERE target_type = 'track' AND target_id IN (SELECT track_id FROM sae.playlist_track WHERE playlist_id = %s) AND user_id = ANY(%s)",
                        (playlist_id, user_ids)
                    )
                    try:
                        cur.execute("SELECT track_id FROM sae.playlist_track WHERE playlist_id = %s", (playlist_id,))
                        track_rows = cur.fetchall()
                        track_ids = [str(r['track_id']) for r in track_rows if r.get('track_id')]
                        if track_ids:
                            for uid in user_ids:
                                try:
                                    cur.execute("SELECT user_favorite_tracks FROM sae.favorite WHERE user_id = %s", (uid,))
                                    fav_row = cur.fetchone()
                                    if fav_row and fav_row.get('user_favorite_tracks'):
                                        existing = fav_row.get('user_favorite_tracks') or ''
                                        parts = [p for p in (existing or '').split(',') if p.strip()]
                                        new_parts = [p for p in parts if p not in track_ids]
                                        new_str = ','.join(new_parts)
                                        cur.execute("UPDATE sae.favorite SET user_favorite_tracks = %s WHERE user_id = %s", (new_str, uid))
                                except Exception:
                                    pass
                    except Exception:
                        pass
        except Exception:
            pass

        cur.execute("SET session_replication_role = 'replica';")
        cur.execute("DELETE FROM sae.playlist_track WHERE playlist_id = %s", (playlist_id,))
        cur.execute("DELETE FROM sae.playlist_user WHERE playlist_id = %s", (playlist_id,))
        cur.execute("DELETE FROM sae.playlist WHERE playlist_id = %s", (playlist_id,))

        try:
            if playlist_image:
                uploads_dir = os.path.join(os.path.dirname(__file__), '..', 'web', 'uploads', 'playlists')
                image_path = os.path.join(uploads_dir, playlist_image)
                if os.path.exists(image_path):
                    os.remove(image_path)
        except Exception:
            pass
        
        cur.execute("SET session_replication_role = 'origin';")
        
        conn.commit()
        return {"message": "Playlist supprimée"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/playlist/{user_id}", tags=["Playlists"], summary="Playlists d'un utilisateur", deprecated=True)
def get_playlist_for_user(
    user_id: int,
    limit: Optional[int] = Query(20, ge=1, le=100, description="Nombre maximum de résultats"),
    offset: Optional[int] = Query(0, ge=0, description="Décalage pour la pagination")
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        cur.execute("SET session_replication_role = 'replica';")
        cur.execute("DELETE FROM sae.playlist_track WHERE playlist_id = %s", (playlist_id,))
        cur.execute("DELETE FROM sae.playlist_user WHERE playlist_id = %s", (playlist_id,))
        cur.execute("DELETE FROM sae.playlist WHERE playlist_id = %s", (playlist_id,))
        cur.execute("SET session_replication_role = 'origin';")
        conn.commit()
        return {"message": "Playlist supprimée"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/playlists/{playlist_id}/tracks", tags=["Playlists"], summary="Remplacer les musiques d'une playlist")
def update_tracks_in_playlist(playlist_id: int, data: PlaylistUpdateTracks):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM sae.playlist_track WHERE playlist_id = %s", (playlist_id,))
        for idx, t_id in enumerate(data.track_ids):
            cur.execute("INSERT INTO sae.playlist_track (playlist_id, track_id, position) VALUES (%s, %s, %s)", (playlist_id, t_id, idx))
        conn.commit()
        return {"message": "Liste de lecture mise à jour"}
    finally:
        conn.close()

@app.delete("/playlists/{playlist_id}/tracks/{track_id}", tags=["Playlists"], summary="Supprimer une musique d'une playlist")
def remove_track_from_playlist(playlist_id: int, track_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        check_query = """
            SELECT * FROM sae.playlist_track 
            WHERE playlist_id = %s AND track_id = %s
        """
        cur.execute(check_query, (playlist_id, track_id))
        if not cur.fetchone():
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Cette track n'est pas dans la playlist")
        
        cur.execute(
            "DELETE FROM sae.playlist_track WHERE playlist_id = %s AND track_id = %s",
            (playlist_id, track_id)
        )

        cur.execute("SELECT COUNT(*) as cnt FROM sae.playlist_track WHERE playlist_id = %s", (playlist_id,))
        cnt = cur.fetchone()['cnt']

        playlist_deleted = False
        if cnt == 0:
            try:
                cur.execute("SELECT playlist_image FROM sae.playlist WHERE playlist_id = %s", (playlist_id,))
                img = cur.fetchone()
                if img and img.get('playlist_image'):
                    image_file = img.get('playlist_image')
                    uploads_dir = os.path.join(os.path.dirname(__file__), '..', 'web', 'uploads', 'playlists')
                    image_path = os.path.join(uploads_dir, image_file)
                    try:
                        if os.path.exists(image_path):
                            os.remove(image_path)
                    except Exception:
                        pass

                cur.execute("DELETE FROM sae.playlist_user WHERE playlist_id = %s", (playlist_id,))
                cur.execute("DELETE FROM sae.playlist WHERE playlist_id = %s", (playlist_id,))
                playlist_deleted = True
            except Exception:
                pass

        conn.commit()
        cur.close()
        conn.close()

        return {"message": "Track supprimée de la playlist", "playlist_deleted": playlist_deleted}
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/playlists", tags=["Utilisateurs"], summary="Playlists d'un utilisateur")
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

@app.get("/users/{user_id}/playlists/detailed", tags=["Utilisateurs"], summary="Playlists détaillées d'un utilisateur")
def get_user_playlists_detailed(user_id: int):
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
                p.playlist_image,
                p.created_at,
                COUNT(DISTINCT pt.track_id) as tracks_count
            FROM sae.playlist p
            JOIN sae.playlist_user pu ON p.playlist_id = pu.playlist_id
            LEFT JOIN sae.playlist_track pt ON p.playlist_id = pt.playlist_id
            WHERE pu.user_id = %s
            GROUP BY p.playlist_id, p.playlist_name, p.playlist_description, p.playlist_image, p.created_at
            ORDER BY p.created_at DESC
        """
        
        cur.execute(query, (user_id,))
        playlists = cur.fetchall()
        
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

@app.put("/playlists/{playlist_id}", tags=["Playlists"], summary="Modifier les informations d'une playlist")
def update_playlist_info(playlist_id: int, data: PlaylistUpdateInfo):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        cur.execute("SELECT playlist_id FROM sae.playlist WHERE playlist_id = %s", (playlist_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Playlist non trouvée")

        query = """
            UPDATE sae.playlist 
            SET playlist_name = %s, playlist_description = %s 
            WHERE playlist_id = %s
        """
        cur.execute(query, (data.name, data.description, playlist_id))
        conn.commit()
        
        return {"message": "Playlist mise à jour avec succès"}
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()

@app.post("/playlists/{playlist_id}/image", tags=["Playlists"], summary="Uploader une image de playlist")
async def upload_playlist_image(playlist_id: int, file: UploadFile = File(...)):
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/avif"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Type de fichier non supporté. Utilisez JPG, PNG, WebP ou AVIF.")
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        cur.execute("SELECT playlist_id, playlist_image FROM sae.playlist WHERE playlist_id = %s", (playlist_id,))
        playlist = cur.fetchone()
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist non trouvée")
        
        if playlist['playlist_image']:
            old_path = os.path.join(UPLOADS_DIR, 'playlists', playlist['playlist_image'])
            if os.path.exists(old_path):
                os.remove(old_path)
        
        ext = os.path.splitext(file.filename)[1] or '.jpg'
        filename = f"{playlist_id}_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(UPLOADS_DIR, 'playlists', filename)
        
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        cur.execute(
            "UPDATE sae.playlist SET playlist_image = %s WHERE playlist_id = %s",
            (filename, playlist_id)
        )
        conn.commit()
        
        return {
            "message": "Image mise à jour avec succès",
            "playlist_image": filename
        }
    except HTTPException:
        if conn: conn.rollback()
        raise
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()

@app.delete("/playlists/{playlist_id}/image", tags=["Playlists"], summary="Supprimer l'image d'une playlist")
def delete_playlist_image(playlist_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        cur.execute("SELECT playlist_id, playlist_image FROM sae.playlist WHERE playlist_id = %s", (playlist_id,))
        playlist = cur.fetchone()
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist non trouvée")
        
        if playlist['playlist_image']:
            old_path = os.path.join(UPLOADS_DIR, 'playlists', playlist['playlist_image'])
            if os.path.exists(old_path):
                os.remove(old_path)
            
            cur.execute(
                "UPDATE sae.playlist SET playlist_image = NULL WHERE playlist_id = %s",
                (playlist_id,)
            )
            conn.commit()
        
        return {"message": "Image supprimée avec succès"}
    except HTTPException:
        if conn: conn.rollback()
        raise
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()

# =================================================================
# ===== SEARCH =====
# =================================================================

@app.get("/search/tracks", tags=["Recherche"], summary="Rechercher des musiques")
def search_tracks(
    query: str = Query(..., description="Terme de recherche"),
    limit: Optional[int] = Query(10, ge=1, le=50, description="Nombre maximum de résultats")
):
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

# =================================================================
# ===== BLINDTESTS =====
# =================================================================

class TrackOrder(BaseModel):
    track_id: int
    order: int

class BlindtestCreate(BaseModel):
    name: str
    user_id: int
    difficulty: int
    tracks: List[TrackOrder]

class BlindtestScoreUpdate(BaseModel):
    score: int

@app.get("/blindtests/generate/{user_id}", tags=["Blindtests"], summary="Générer un blindtest personnalisé filtré")
def generate_personalized_blindtest(
    user_id: int,
    limit: int = 10,
    genre: Optional[str] = Query(None, description="Filtrer par genre"),
    min_year: Optional[int] = Query(None, description="Année d'enregistrement minimum"),
    popularity: Optional[str] = Query(None, description="Popularité (high, medium, low)"),
    artist: Optional[str] = Query(None, description="Filtrer par artiste"),
    track_type: Optional[str] = Query(None, description="instrumental, vocal, spoken"),
    lang: Optional[str] = Query(None, description="Code langue (fr, en, etc.)")
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")

    try:
        cur = conn.cursor()
        
        def fetch_tracks(custom_conditions, custom_params, limit_n, exclude_ids=None):
            base_q = """
                SELECT t.track_id, t.track_title, t.track_file, t.track_genre_top, 
                       t.track_listens,
                       (SELECT string_agg(art.artist_name, ', ') 
                        FROM sae.artist art 
                        JOIN sae.artist_album_track aat ON art.artist_id = aat.artist_id 
                        WHERE aat.track_id = t.track_id) as artist_names
                FROM sae.tracks t
                LEFT JOIN sae.tracks_features tf ON t.track_id = tf.track_id
                WHERE t.track_file IS NOT NULL AND t.track_file != ''
            """
            conds = custom_conditions.copy()
            prms = custom_params.copy()
            
            if exclude_ids:
                conds.append("NOT (t.track_id = ANY(%s))")
                prms.append(exclude_ids)
                
            if conds:
                base_q += " AND " + " AND ".join(conds)
                
            base_q += " ORDER BY RANDOM() LIMIT %s"
            prms.append(limit_n)
            
            cur.execute(base_q, prms)
            return [dict(row) for row in cur.fetchall()]

        cur.execute("SELECT user_favorite_tracks FROM sae.favorite WHERE user_id = %s", (user_id,))
        fav_row = cur.fetchone()
        liked_tracks = []
        if fav_row and fav_row.get('user_favorite_tracks'):
            liked_tracks = [int(tid) for tid in fav_row['user_favorite_tracks'].split(',') if tid.strip().isdigit()]

        if not liked_tracks:
            cur.execute("SELECT target_id FROM sae.user_reaction WHERE user_id = %s AND target_type = 'track' AND liked = TRUE", (user_id,))
            liked_tracks = [row['target_id'] for row in cur.fetchall()]

        recommended_ids = []
        if liked_tracks:
            try:
                recos = recommend_similar_tracks(liked_tracks[:5], top_n=200)
                recommended_ids = [int(r.get('track_id', r.get('id'))) for r in recos if r.get('track_id') or r.get('id')]
            except Exception as e:
                pass

        conditions = []
        params = []

        if genre:
            conditions.append("t.track_genre_top ILIKE %s")
            params.append(f"%{genre}%")
            
        if artist:
            conditions.append("EXISTS (SELECT 1 FROM sae.artist_album_track aat JOIN sae.artist a ON aat.artist_id = a.artist_id WHERE aat.track_id = t.track_id AND a.artist_name ILIKE %s)")
            params.append(f"%{artist}%")

        if popularity == 'high':
            conditions.append("t.track_listens >= 5000")
        elif popularity == 'medium':
            conditions.append("t.track_listens >= 1000 AND t.track_listens < 5000")
        elif popularity == 'low':
            conditions.append("t.track_listens < 1000")
            
        if track_type == 'instrumental':
            conditions.append("tf.audio_features_instrumentalness >= 0.5")
        elif track_type == 'spoken':
            conditions.append("tf.audio_features_speechiness >= 0.5")
        elif track_type == 'vocal':
            conditions.append("tf.audio_features_instrumentalness < 0.5 AND tf.audio_features_speechiness < 0.5")
            
        if lang:
            conditions.append("t.track_language_code ILIKE %s")
            params.append(f"{lang}%")

        if min_year:
            conditions.append("t.track_date_recorded IS NOT NULL AND LENGTH(CAST(t.track_date_recorded AS TEXT)) >= 4 AND CAST(SUBSTRING(CAST(t.track_date_recorded AS TEXT) FROM 1 FOR 4) AS INTEGER) >= %s")
            params.append(min_year)

        final_tracks = []

        if recommended_ids:
            reco_conds = conditions.copy()
            reco_conds.append("t.track_id = ANY(%s)")
            reco_params = params.copy()
            reco_params.append(recommended_ids)
            try:
                final_tracks.extend(fetch_tracks(reco_conds, reco_params, limit))
            except Exception as e:
                conn.rollback()

        if len(final_tracks) < limit:
            needed = limit - len(final_tracks)
            existing_ids = [t['track_id'] for t in final_tracks] if final_tracks else None
            try:
                final_tracks.extend(fetch_tracks(conditions, params, needed, existing_ids))
            except Exception as e:
                conn.rollback()

        if len(final_tracks) < limit:
            needed = limit - len(final_tracks)
            existing_ids = [t['track_id'] for t in final_tracks] if final_tracks else None
            try:
                final_tracks.extend(fetch_tracks([], [], needed, existing_ids))
            except Exception as e:
                conn.rollback()

        if not final_tracks:
            raise HTTPException(status_code=404, detail="Impossible de générer le blindtest.")

        random.shuffle(final_tracks)

        return {
            "success": True,
            "count": len(final_tracks),
            "tracks": final_tracks
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()

@app.post("/blindtests", tags=["Blindtests"], summary="Enregistrer un blindtest généré")
def create_blindtest(bt: BlindtestCreate):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
        
    try:
        cur = conn.cursor()
        query = """
            INSERT INTO sae.blindtest (blindtest_name, user_id, difficulty_seconds, total_tracks)
            VALUES (%s, %s, %s, %s) RETURNING blindtest_id;
        """
        cur.execute(query, (bt.name, bt.user_id, bt.difficulty, len(bt.tracks)))
        blindtest_id = cur.fetchone()['blindtest_id']

        for track in bt.tracks:
            if isinstance(track.track_id, int) or str(track.track_id).isdigit():
                cur.execute("""
                    INSERT INTO sae.blindtest_track (blindtest_id, track_id, track_order)
                    VALUES (%s, %s, %s)
                """, (blindtest_id, int(track.track_id), track.order))

        conn.commit()
        return {"success": True, "blindtest_id": blindtest_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()

@app.put("/blindtests/{blindtest_id}/score", tags=["Blindtests"], summary="Mettre à jour le score d'un blindtest")
def update_blindtest_score(blindtest_id: int, data: BlindtestScoreUpdate):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
        
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE sae.blindtest 
            SET score = %s 
            WHERE blindtest_id = %s
        """, (data.score, blindtest_id))
        
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Blindtest non trouvé")
            
        conn.commit()
        return {"success": True, "message": "Score mis à jour"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()

@app.get("/users/{user_id}/blindtests", tags=["Blindtests"], summary="Récupérer l'historique des blindtests")
def get_user_blindtests(user_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
        
    try:
        cur = conn.cursor()
        query = """
            SELECT b.blindtest_id, b.blindtest_name, b.difficulty_seconds, b.score, b.total_tracks, b.created_at
            FROM sae.blindtest b
            WHERE b.user_id = %s
            ORDER BY b.created_at DESC;
        """
        cur.execute(query, (user_id,))
        results = cur.fetchall()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()

@app.get("/blindtests/{blindtest_id}", tags=["Blindtests"], summary="Récupérer un blindtest spécifique")
def get_blindtest(blindtest_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM sae.blindtest WHERE blindtest_id = %s", (blindtest_id,))
        bt = cur.fetchone()
        if not bt:
            raise HTTPException(status_code=404, detail="Blindtest non trouvé")
        
        query = """
            SELECT bt_tr.track_order, t.track_id, t.track_title, t.track_file,
                   (SELECT string_agg(art.artist_name, ', ') FROM sae.artist art JOIN sae.artist_album_track aat ON art.artist_id = aat.artist_id WHERE aat.track_id = t.track_id) as artist_names
            FROM sae.blindtest_track bt_tr
            JOIN sae.tracks t ON bt_tr.track_id = t.track_id
            WHERE bt_tr.blindtest_id = %s
            ORDER BY bt_tr.track_order
        """
        cur.execute(query, (blindtest_id,))
        tracks = cur.fetchall()
        
        formatted_tracks = []
        for tr in tracks:
            track_url = tr['track_file']
            if track_url and track_url.startswith('music/'):
                track_url = 'https://files.freemusicarchive.org/storage-freemusicarchive-org/music/' + track_url[6:]
            formatted_tracks.append({
                "track_id": tr['track_id'],
                "title": tr['track_title'],
                "artist": tr['artist_names'] or "Artiste inconnu",
                "url": track_url,
                "guessed": None
            })
            
        bt['tracks'] = formatted_tracks
        return bt
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()

@app.delete("/blindtests/{blindtest_id}", tags=["Blindtests"], summary="Supprimer un blindtest")
def delete_blindtest_endpoint(blindtest_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM sae.blindtest_track WHERE blindtest_id = %s", (blindtest_id,))
        cur.execute("DELETE FROM sae.blindtest WHERE blindtest_id = %s", (blindtest_id,))
        conn.commit()
        return {"success": True, "message": "Blindtest supprimé"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()

# =================================================================
# ===== USERS & ADMIN =====
# =================================================================

class UpdateUserRequest(BaseModel):
    user_firstname: Optional[str] = None
    user_lastname:  Optional[str] = None
    user_password:  Optional[str] = None
    user_age:       Optional[int] = None
    user_gender:    Optional[str] = None
    user_location:  Optional[str] = None

@app.put("/users/{user_id}", tags=["Utilisateurs"], summary="Modifier le profil d'un utilisateur")
def update_user(user_id: int, body: UpdateUserRequest):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")

    try:
        cur = conn.cursor()

        fields = []
        params = []

        if body.user_firstname is not None:
            fields.append("user_firstname = %s")
            params.append(body.user_firstname)
        if body.user_lastname is not None:
            fields.append("user_lastname = %s")
            params.append(body.user_lastname)
        if body.user_password is not None:
            fields.append("user_password = %s")
            hashed = bcrypt.hashpw(body.user_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            params.append(hashed)
        if body.user_age is not None:
            fields.append("user_age = %s")
            params.append(body.user_age)
        if body.user_gender is not None:
            fields.append("user_gender = %s")
            params.append(body.user_gender)
        if body.user_location is not None:
            fields.append("user_location = %s")
            params.append(body.user_location)

        if not fields:
            raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")

        params.append(user_id)
        query = f"UPDATE sae.users SET {', '.join(fields)} WHERE user_id = %s"
        cur.execute(query, params)

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

        conn.commit()
        cur.close()
        conn.close()

        return {"success": True, "message": "Profil mis à jour"}

    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/users/{user_id}", tags=["Utilisateurs"], summary="Supprimer un utilisateur")
def delete_user(user_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")

    try:
        cur = conn.cursor()

        cur.execute("DELETE FROM sae.favorite WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM sae.playlist_user WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM sae.users WHERE user_id = %s", (user_id,))

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

        conn.commit()
        cur.close()
        conn.close()

        return {"success": True, "message": "Compte supprimé"}

    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

class UpdateUserRole(BaseModel):
    role: str

class BanUser(BaseModel):
    banned: bool

class AdminUpdateProfile(BaseModel):
    user_firstname: Optional[str] = None
    user_lastname: Optional[str] = None
    user_mail: Optional[str] = None
    user_age: Optional[int] = None
    user_gender: Optional[str] = None
    user_location: Optional[str] = None
    user_phonenumber: Optional[str] = None

@app.get("/admin/stats", tags=["Admin"], summary="Statistiques globales")
def admin_stats():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")

    try:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) as total FROM sae.users")
        total_users = cur.fetchone()['total']

        cur.execute("SELECT COUNT(*) as total FROM sae.users WHERE user_status = 'admin'")
        total_admins = cur.fetchone()['total']

        cur.execute("SELECT COUNT(*) as total FROM sae.users WHERE user_status = 'super_admin'")
        total_super_admins = cur.fetchone()['total']

        cur.execute("SELECT COUNT(*) as total FROM sae.users WHERE user_status = 'banned'")
        total_banned = cur.fetchone()['total']

        cur.execute("SELECT COUNT(*) as total FROM sae.tracks")
        total_tracks = cur.fetchone()['total']

        cur.execute("SELECT COUNT(*) as total FROM sae.album")
        total_albums = cur.fetchone()['total']

        cur.execute("SELECT COUNT(*) as total FROM sae.artist")
        total_artists = cur.fetchone()['total']

        cur.execute("SELECT COUNT(*) as total FROM sae.playlist")
        total_playlists = cur.fetchone()['total']

        cur.execute("SELECT COUNT(*) as total FROM sae.genre")
        total_genres = cur.fetchone()['total']

        cur.close()
        conn.close()

        return {
            "users": total_users,
            "admins": total_admins,
            "super_admins": total_super_admins,
            "banned": total_banned,
            "tracks": total_tracks,
            "albums": total_albums,
            "artists": total_artists,
            "playlists": total_playlists,
            "genres": total_genres
        }
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/users", tags=["Admin"], summary="Liste de tous les utilisateurs")
def admin_list_users(
    limit: Optional[int] = Query(50, ge=1, le=500),
    offset: Optional[int] = Query(0, ge=0),
    search: Optional[str] = Query(None, description="Rechercher par nom, prénom ou email"),
    role: Optional[str] = Query(None, description="Filtrer par rôle (admin, user, banned)")
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")

    try:
        cur = conn.cursor()

        where_clauses = []
        params = []

        if search:
            where_clauses.append(
                "(user_firstname ILIKE %s OR user_lastname ILIKE %s OR user_mail ILIKE %s)"
            )
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])

        if role:
            where_clauses.append("LOWER(user_status) = %s")
            params.append(role.lower())

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        count_query = f"SELECT COUNT(*) as total FROM sae.users {where_sql}"
        cur.execute(count_query, params)
        total = cur.fetchone()['total']

        query = f"""
            SELECT
                user_id, user_firstname, user_lastname, user_mail,
                user_age, user_gender, user_location, user_status,
                user_year_created
            FROM sae.users
            {where_sql}
            ORDER BY user_id ASC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        cur.execute(query, params)
        users = cur.fetchall()

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

@app.get("/admin/users/{user_id}", tags=["Admin"], summary="Détails d'un utilisateur")
def admin_get_user(user_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT user_id, user_firstname, user_lastname, user_mail,
                   user_age, user_gender, user_location, user_status,
                   user_year_created, user_phonenumber
            FROM sae.users WHERE user_id = %s
        """, (user_id,))
        user = cur.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

        cur.execute("""
            SELECT COUNT(*) as total FROM sae.playlist_user WHERE user_id = %s
        """, (user_id,))
        user['playlists_count'] = cur.fetchone()['total']

        cur.execute("""
            SELECT COUNT(*) as total FROM sae.favorite WHERE user_id = %s
        """, (user_id,))
        user['favorites_count'] = cur.fetchone()['total']

        cur.close()
        conn.close()

        return user
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/admin/users/{user_id}/role", tags=["Admin"], summary="Changer le rôle d'un utilisateur")
def admin_update_role(user_id: int, body: UpdateUserRole, requester_id: Optional[int] = Query(None)):
    if body.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="Rôle invalide. Utiliser 'admin' ou 'user'.")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")

    try:
        cur = conn.cursor()

        cur.execute("SELECT user_status FROM sae.users WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

        target_status = row['user_status']

        if target_status == 'super_admin':
            raise HTTPException(status_code=403, detail="Impossible de modifier le rôle du super administrateur")

        if target_status == 'admin':
            requester_role = None
            if requester_id:
                cur.execute("SELECT user_status FROM sae.users WHERE user_id = %s", (requester_id,))
                req_row = cur.fetchone()
                requester_role = req_row['user_status'] if req_row else None
            if requester_role != 'super_admin':
                raise HTTPException(status_code=403, detail="Seul le super administrateur peut modifier le rôle d'un admin")

        cur.execute(
            "UPDATE sae.users SET user_status = %s WHERE user_id = %s",
            (body.role, user_id)
        )

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

        conn.commit()
        cur.close()
        conn.close()

        return {"success": True, "message": f"Rôle mis à jour en '{body.role}'"}
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/admin/users/{user_id}/ban", tags=["Admin"], summary="Bannir ou débannir un utilisateur")
def admin_ban_user(user_id: int, body: BanUser, requester_id: Optional[int] = Query(None)):
    new_status = "banned" if body.banned else "user"

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")

    try:
        cur = conn.cursor()

        cur.execute("SELECT user_status FROM sae.users WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

        target_status = row['user_status']

        if target_status == 'super_admin' and body.banned:
            raise HTTPException(status_code=403, detail="Impossible de bannir le super administrateur")

        if target_status == 'admin' and body.banned:
            requester_role = None
            if requester_id:
                cur.execute("SELECT user_status FROM sae.users WHERE user_id = %s", (requester_id,))
                req_row = cur.fetchone()
                requester_role = req_row['user_status'] if req_row else None
            if requester_role != 'super_admin':
                raise HTTPException(status_code=403, detail="Seul le super administrateur peut bannir un admin")

        cur.execute(
            "UPDATE sae.users SET user_status = %s WHERE user_id = %s",
            (new_status, user_id)
        )
        conn.commit()
        cur.close()
        conn.close()

        action = "banni" if body.banned else "débanni"
        return {"success": True, "message": f"Utilisateur {action}"}
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/admin/users/{user_id}/profile", tags=["Admin"], summary="Modifier le profil d'un utilisateur (admin)")
def admin_update_profile(user_id: int, body: AdminUpdateProfile, requester_id: Optional[int] = Query(None)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")

    try:
        cur = conn.cursor()

        cur.execute("SELECT user_id, user_status FROM sae.users WHERE user_id = %s", (user_id,))
        target = cur.fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

        if target['user_status'] in ('admin', 'super_admin'):
            requester_role = None
            if requester_id:
                cur.execute("SELECT user_status FROM sae.users WHERE user_id = %s", (requester_id,))
                req_row = cur.fetchone()
                requester_role = req_row['user_status'] if req_row else None
            if requester_role != 'super_admin':
                raise HTTPException(status_code=403, detail="Seul le super administrateur peut modifier le profil d'un admin")

        fields = []
        params = []

        if body.user_firstname is not None:
            fields.append("user_firstname = %s")
            params.append(body.user_firstname)
        if body.user_lastname is not None:
            fields.append("user_lastname = %s")
            params.append(body.user_lastname)
        if body.user_mail is not None:
            fields.append("user_mail = %s")
            params.append(body.user_mail)
        if body.user_age is not None:
            fields.append("user_age = %s")
            params.append(body.user_age)
        if body.user_gender is not None:
            fields.append("user_gender = %s")
            params.append(body.user_gender)
        if body.user_location is not None:
            fields.append("user_location = %s")
            params.append(body.user_location)
        if body.user_phonenumber is not None:
            fields.append("user_phonenumber = %s")
            params.append(body.user_phonenumber)

        if not fields:
            raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")

        params.append(user_id)
        query = f"UPDATE sae.users SET {', '.join(fields)} WHERE user_id = %s"
        cur.execute(query, params)

        conn.commit()
        cur.close()
        conn.close()

        return {"success": True, "message": "Profil utilisateur mis à jour"}
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/users/{user_id}", tags=["Admin"], summary="Supprimer un utilisateur")
def admin_delete_user(user_id: int, requester_id: Optional[int] = Query(None)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")

    try:
        cur = conn.cursor()

        cur.execute("SELECT user_status FROM sae.users WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

        target_status = row['user_status']

        if target_status == 'super_admin':
            raise HTTPException(status_code=403, detail="Impossible de supprimer le super administrateur")

        if target_status == 'admin':
            requester_role = None
            if requester_id:
                cur.execute("SELECT user_status FROM sae.users WHERE user_id = %s", (requester_id,))
                req_row = cur.fetchone()
                requester_role = req_row['user_status'] if req_row else None
            if requester_role != 'super_admin':
                raise HTTPException(status_code=403, detail="Seul le super administrateur peut supprimer un admin")

        cur.execute("DELETE FROM sae.favorite WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM sae.playlist_user WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM sae.users_track WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM sae.users WHERE user_id = %s", (user_id,))

        conn.commit()
        cur.close()
        conn.close()

        return {"success": True, "message": "Utilisateur supprimé"}
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/tracks/{track_id}", tags=["Admin"], summary="Supprimer une musique (modération)")
def admin_delete_track(track_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")

    try:
        cur = conn.cursor()

        cur.execute("DELETE FROM sae.playlist_track WHERE track_id = %s", (track_id,))
        cur.execute("DELETE FROM sae.users_track WHERE track_id = %s", (track_id,))
        cur.execute("DELETE FROM sae.track_genre WHERE track_id = %s", (track_id,))
        cur.execute("DELETE FROM sae.license WHERE track_id = %s", (track_id,))
        cur.execute("DELETE FROM sae.song_social_score WHERE track_id = %s", (track_id,))
        cur.execute("DELETE FROM sae.song_rank WHERE track_id = %s", (track_id,))
        cur.execute("DELETE FROM sae.audio WHERE track_id = %s", (track_id,))
        cur.execute("DELETE FROM sae.temporal_features WHERE track_id = %s", (track_id,))
        cur.execute("DELETE FROM sae.artist_album_track WHERE track_id = %s", (track_id,))
        cur.execute("DELETE FROM sae.artist_track_publisher WHERE track_id = %s", (track_id,))
        cur.execute("DELETE FROM sae.tracks WHERE track_id = %s", (track_id,))

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Track non trouvée")

        conn.commit()
        cur.close()
        conn.close()

        return {"success": True, "message": "Track supprimée"}
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/playlists/{playlist_id}", tags=["Admin"], summary="Supprimer une playlist (modération)")
def admin_delete_playlist(playlist_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")

    try:
        cur = conn.cursor()

        cur.execute("DELETE FROM sae.playlist_track WHERE playlist_id = %s", (playlist_id,))
        cur.execute("DELETE FROM sae.playlist_user WHERE playlist_id = %s", (playlist_id,))
        cur.execute("DELETE FROM sae.playlist WHERE playlist_id = %s", (playlist_id,))

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Playlist non trouvée")

        conn.commit()
        cur.close()
        conn.close()

        return {"success": True, "message": "Playlist supprimée"}
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)