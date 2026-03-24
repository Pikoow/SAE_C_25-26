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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Recommendation'))

from item_based_pierre import recommend_similar_tracks
from item_based_stanislas import recommend_artists, initialize_artist_system

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_artist_system()
    # Auto-migration: add position column to playlist_track if missing
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("ALTER TABLE sae.playlist_track ADD COLUMN IF NOT EXISTS position INT DEFAULT 0;")
            # Backfill position for existing rows that have position=0
            cur.execute("""
                WITH numbered AS (
                    SELECT ctid, ROW_NUMBER() OVER (PARTITION BY playlist_id ORDER BY track_id) - 1 AS pos
                    FROM sae.playlist_track
                    WHERE position = 0
                )
                UPDATE sae.playlist_track SET position = numbered.pos
                FROM numbered WHERE sae.playlist_track.ctid = numbered.ctid AND sae.playlist_track.position = 0;
            """)
            # Migration: add playlist_image column
            cur.execute("ALTER TABLE sae.playlist ADD COLUMN IF NOT EXISTS playlist_image TEXT;")
            conn.commit()
            cur.close()
            conn.close()
            print("Migration: playlist_track.position + playlist.playlist_image OK")
            # Create user_reaction table for likes/dislikes/favorites
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
            print("Migration: sae.user_reaction OK")
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
    {"name": "Admin",            "description": "⚙️ Endpoints d'administration — statistiques globales, gestion des utilisateurs, modération du contenu."},
]

app = FastAPI(
    title="API MuSE",
    description="API pour accéder à la base de données musicale MuSE, gérer des playlists et obtenir des recommandations personnalisées.",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    docs_url=None,
)

# Servir les fichiers statiques (images, CSS, JS)
web_dir = os.path.join(os.path.dirname(__file__), '..', 'web')
app.mount("/static", StaticFiles(directory=web_dir), name="static")

# Servir les fichiers uploadés (images de playlists)
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
    <title>Documentation - API MuSE</title>
    <link rel="icon" type="image/png" sizes="32x32" href="/static/images/logos/muse.png">
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css"/>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&family=Rammetto+One&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: "Outfit", sans-serif; color: #000; font-size: 0.875rem; }
        .swagger-ui .topbar { display: none; }

        /* === HEADER === */
        header { background-color: #fff; border-bottom: 5px solid #ED7A26; display: flex; align-items: center; justify-content: space-between; padding: 1.5em 3em; position: sticky; top: 0; z-index: 1000; }
        header>a { text-decoration: none; }
        header h2 { font-family: "Rammetto One", sans-serif; font-size: 1.875rem; color: #000; }
        header nav { flex: 1; display: flex; justify-content: center; gap: 2em; }
        header nav>a { color: #000; font-weight: bold; font-size: 1.25rem; text-decoration: none; }
        header nav>a:hover { color: #ED7A26; }
        .connexion-inscription>a { font-size: 1.25rem; font-weight: bold; color: #000; text-decoration: none; padding-right: 1em; }
        .connexion-inscription>a:hover { color: #ED7A26; }
        .connexion-inscription button { background-color: #ED7A26; font-family: "Outfit", sans-serif; font-size: 1.25rem; font-weight: bold; border-radius: 0.313em; border: none; width: 7em; height: 1.9em; cursor: pointer; transition: transform 0.2s; }
        .connexion-inscription button:hover { transform: scale(1.05); }
        .connexion-inscription button>a { color: #fff; text-decoration: none; }
        header nav .dropdown { position: relative; display: flex; align-items: center; }
        header nav .dropdown>a { color: #000; font-weight: bold; font-size: 1.25rem; text-decoration: none; cursor: pointer; }
        header nav .dropdown-content { display: none; position: absolute; background-color: #fff; min-width: 200px; box-shadow: 0 8px 16px rgba(0,0,0,0.1); z-index: 100; top: 100%; left: 50%; transform: translateX(-50%); border-radius: 8px; border: 1px solid #c8c8c8; margin-top: 25px; overflow: visible; }
        header nav .dropdown-content::before { content: ""; position: absolute; top: -25px; left: 0; width: 100%; height: 25px; background: transparent; }
        header nav .dropdown-content a { color: #000; padding: 12px 16px; text-decoration: none; display: block; font-size: 1rem; text-align: center; transition: background 0.2s; font-weight: normal; }
        header nav .dropdown-content a:first-child { border-radius: 8px 8px 0 0; }
        header nav .dropdown-content a:last-child { border-radius: 0 0 8px 8px; }
        header nav .dropdown-content a:hover { background-color: #fff5e6; color: #ED7A26; }
        header nav .dropdown:hover .dropdown-content { display: block; }
        header nav .dropdown:hover>a { color: #ED7A26; }

        /* === FOOTER === */
        footer { background-color: #000; color: #fff; padding: 3.125em; }
        .titre-footer { display: flex; justify-content: center; }
        .titre-footer h2 { font-family: "Rammetto One", sans-serif; font-size: 1.875rem; }
        .navigation-footer { display: flex; justify-content: center; margin: 2em 0; flex-wrap: wrap; gap: 6em; }
        .navigation-footer>div { display: flex; flex-direction: column; gap: 0.625em; }
        .navigation-footer>div>p { font-weight: bold; margin-bottom: 0.5em; }
        .navigation-footer>div>div { display: flex; flex-direction: column; gap: 0.5em; }
        .navigation-footer a { text-decoration: none; color: #fff; transition: color 0.25s ease; }
        .navigation-footer a:hover { color: #ED7A26; }
        .barre-separation-footer { width: 100%; height: 1px; background-color: #fff; margin-bottom: 1.25em; }
        .fin-footer { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }
        .reseaux-sociaux-footer img { width: 1.25em; height: 1.25em; margin-right: 0.625em; }
    </style>
</head>
<body>
    <header>
        <a href="/static/accueil.html"><h2>MuSE</h2></a>
        <nav>
            <a href="/static/accueil.html">Accueil</a>
            <a href="/static/playlists.html">Playlists</a>
            <a href="/static/preferences.html">Préférences</a>
            <div class="dropdown">
                <a href="#">API &nbsp;<span style="display:inline-block;transform:translateY(-1px)">\u25be</span></a>
                <div class="dropdown-content">
                    <a href="/static/api-installation.html">Installation</a>
                    <a href="/docs">Doc. Swagger</a>
                    <a href="/static/api-documentation.html">Doc Legacy</a>
                    <a href="/static/api-test.html">Testez l\'API</a>
                </div>
            </div>
        </nav>
        <div class="header-right">
            <div class="connexion-inscription">
                <a href="/static/connexion.html?mode=login">Connexion</a>
                <button><a href="/static/connexion.html?mode=register">Inscription</a></button>
            </div>
        </div>
    </header>

    <div id="swagger-ui"></div>

    <footer>
        <div class="titre-footer"><h2>MuSE</h2></div>
        <div class="navigation-footer">
            <div><p>Société</p><div><a href="#">À propos de nous</a><a href="#">Offre d\'emploi</a></div></div>
            <div><p>Liens utiles</p><div><a href="/static/contact.html">Nous contacter</a></div></div>
            <div><p>Communauté</p><div><a href="#">Développeurs</a></div></div>
            <div><p>Légal</p><div><a href="#">Mentions légales</a></div></div>
        </div>
        <div class="barre-separation-footer"></div>
        <div class="fin-footer">
            <div class="reseaux-sociaux-footer">
                <a href="#"><img src="/static/images/icones/instagram.avif" alt="Instagram"/></a>
                <a href="#"><img src="/static/images/icones/linkedin.avif" alt="LinkedIn"/></a>
                <a href="#"><img src="/static/images/icones/github.avif" alt="GitHub"/></a>
                <a href="#"><img src="/static/images/icones/facebook.avif" alt="Facebook"/></a>
            </div>
            <p>&copy; 2026 MuSE Français</p>
        </div>
    </footer>

    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        const userRole = localStorage.getItem("userRole");
        const isAdmin = (userRole === "admin" || userRole === "super_admin");
        SwaggerUIBundle({
            url: "/openapi.json",
            dom_id: "#swagger-ui",
            presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
            layout: "BaseLayout",
            deepLinking: true,
            defaultModelsExpandDepth: -1,
            supportedSubmitMethods: isAdmin ? ["get","post","put","delete","patch"] : []
        });
    </script>
</body>
</html>
    ''')

# Erreur page web Cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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

def clean_nan(obj):
    if isinstance(obj, float) and math.isnan(obj):
        return None
    elif isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    return obj

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Erreur de connexion : {e}")
        return None

@app.get("/", tags=["Général"], summary="Accueil de l'API")
def read_root():
    return {"message": "Bienvenue sur l'API de Muse!"}

# Récuérer toutes les tracks avec leurs informations
@app.get("/tracks", tags=["Tracks"], summary="Liste de toutes les musiques")
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

# Récupère une musique spécifique par son ID avec toutes ses informations
@app.get("/tracks/{track_id}", tags=["Tracks"], summary="Détails complets d'une musique")
def get_track_by_id(track_id: int):
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
        
        return clean_nan(track)
    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

# Récupère tout les artistes avec leurs informations
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

# Récupère un artiste spécifique par son ID avec toutes ses informations
@app.get("/artists/{artist_id}", tags=["Artistes"], summary="Détails complets d'un artiste")
def get_artist_by_id(artist_id: int):
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

# Récupère toutes les musiques d'un artiste spécifique par son ID
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
                aat.album_id,
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

# Récupère tout les albums avec leurs informations
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

# Récupère un album spécifique par son ID avec toutes ses informations
@app.get("/albums/{album_id}", tags=["Albums"], summary="Détails complets d'un album")
def get_album_by_id(album_id: int):
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


# --- Reactions endpoints: like / dislike / favorite for artists and albums ---
@app.post("/reactions/{target_type}/{target_id}")
def toggle_reaction(target_type: str, target_id: int, payload: dict):
    """Payload: { "user_id": int, "action": "like"|"dislike"|"favorite", "value": true|false }
    target_type: 'artist' or 'album'"""
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
        # verify user exists
        cur.execute("SELECT user_id FROM sae.users WHERE user_id = %s", (user_id,))
        if not cur.fetchone():
            cur.close(); conn.close()
            raise HTTPException(status_code=404, detail="User not found")

        # verify target exists
        if target_type == "artist":
            cur.execute("SELECT artist_id FROM sae.artist WHERE artist_id = %s", (target_id,))
        elif target_type == "album":
            cur.execute("SELECT album_id FROM sae.album WHERE album_id = %s", (target_id,))
        else:
            cur.execute("SELECT track_id FROM sae.tracks WHERE track_id = %s", (target_id,))
        if not cur.fetchone():
            cur.close(); conn.close()
            raise HTTPException(status_code=404, detail=f"{target_type} not found")

        # Prepare values for upsert
        liked = False; disliked = False; favorite = False
        if action == "like":
            liked = value
            if value:
                disliked = False
            # merge likes with favorites: liking a track marks it as favorite
            favorite = value
        elif action == "dislike":
            disliked = value
            if value:
                liked = False
            # disliking should remove favorite
            favorite = False
        elif action == "favorite":
            favorite = value

        # Upsert row
        cur.execute("""
            INSERT INTO sae.user_reaction (user_id, target_type, target_id, liked, disliked, favorite, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (user_id, target_type, target_id) DO UPDATE
            SET liked = EXCLUDED.liked,
                disliked = EXCLUDED.disliked,
                favorite = EXCLUDED.favorite,
                updated_at = NOW();
        """, (user_id, target_type, target_id, liked, disliked, favorite))

        # Update favorites count on target when favorite toggled
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

        # --- Synchronize special playlists for tracks in the same transaction ---
        if target_type == 'track' and action in ('like', 'dislike'):
            try:
                # Helper to delete empty playlist (and associated records + image)
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
                        # ensure 'titres liké' exists for this user
                        cur.execute("SELECT p.playlist_id FROM sae.playlist p JOIN sae.playlist_user pu ON p.playlist_id=pu.playlist_id WHERE pu.user_id=%s AND lower(trim(p.playlist_name)) = 'titres liké'", (user_id,))
                        row = cur.fetchone()
                        if row:
                            pid = row['playlist_id']
                        else:
                            cur.execute("INSERT INTO sae.playlist (playlist_name, playlist_description) VALUES (%s,%s) RETURNING playlist_id", ('Titres liké','Playlist de titres likés'))
                            pid = cur.fetchone()['playlist_id']
                            cur.execute("INSERT INTO sae.playlist_user (playlist_id, user_id) VALUES (%s,%s)", (pid, user_id))
                        # add track to playlist (position = end)
                        cur.execute("INSERT INTO sae.playlist_track (playlist_id, track_id, position) VALUES (%s,%s, COALESCE((SELECT MAX(position)+1 FROM sae.playlist_track WHERE playlist_id=%s), 0)) ON CONFLICT DO NOTHING", (pid, target_id, pid))
                        # Note: disliked tracks are not stored in a playlist anymore; reaction upsert clears the disliked flag.
                    else:
                        # remove from 'titres liké' if exists
                        cur.execute("SELECT p.playlist_id FROM sae.playlist p JOIN sae.playlist_user pu ON p.playlist_id=pu.playlist_id WHERE pu.user_id=%s AND lower(trim(p.playlist_name)) = 'titres liké'", (user_id,))
                        row = cur.fetchone()
                        if row:
                            pid = row['playlist_id']
                            cur.execute("DELETE FROM sae.playlist_track WHERE playlist_id=%s AND track_id=%s", (pid, target_id))
                            _maybe_delete_playlist(cur, pid)

                if action == 'dislike':
                    if disliked:
                        # When a user dislikes a track we do NOT create a special "disliked titres" playlist.
                        # We keep the reaction in `sae.user_reaction` and ensure mutual exclusivity by
                        # removing the track from the "titres liké" playlist if present.
                        cur.execute("SELECT p.playlist_id FROM sae.playlist p JOIN sae.playlist_user pu ON p.playlist_id=pu.playlist_id WHERE pu.user_id=%s AND lower(trim(p.playlist_name)) = 'titres liké'", (user_id,))
                        row2 = cur.fetchone()
                        if row2:
                            pid2 = row2['playlist_id']
                            cur.execute("DELETE FROM sae.playlist_track WHERE playlist_id=%s AND track_id=%s", (pid2, target_id))
                            _maybe_delete_playlist(cur, pid2)
                    else:
                        # On un-dislike we simply stop marking the track as disliked in user_reaction;
                        # no playlist cleanup is required because we never created a disliked playlist.
                        pass
            except Exception:
                # don't fail the whole reaction toggle if playlist cleanup fails
                pass

        # --- Synchronize user's preferences (sae.favorite) when liking/unliking tracks ---
        try:
            if target_type == 'track':
                # fetch existing favorites row for user
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
                    # on unlike, remove from favorites
                    parts = [p for p in parts if p != str_tid]

                new_val = ','.join(parts)
                if fav_row:
                    cur.execute("UPDATE sae.favorite SET user_favorite_tracks = %s WHERE user_id = %s", (new_val, user_id))
                else:
                    cur.execute("INSERT INTO sae.favorite (user_favorite_tracks, user_favorite_artist, user_favorite_genre, user_id) VALUES (%s,%s,%s,%s)", (new_val, '', '', user_id))
        except Exception:
            # don't block main operation if favorites sync fails
            pass

        conn.commit()

        # Return current reaction state
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
    """Return a list of tracks that the user has marked as disliked."""
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

# Récupère toutes les musiques d'un album spécifique par son ID
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

# Récupère une liste de recommandations de musiques similaires à une ou plusieurs musiques d'entrée
@app.get("/reco/tracks", tags=["Recommandations"], summary="Recommandations de musiques similaires")
def recommend_tracks(
    track_ids: List[int] = Query(..., description="One or more track IDs to base recommendations on"),
    limit: int = Query(10, ge=1, le=50),
    exclude_user_id: Optional[int] = Query(None, description="Optional user id whose disliked tracks should be excluded")
):
    """
    Exemple: /reco/tracks?track_ids=69170&track_ids=95976
    """
    try:
        recommendations = recommend_similar_tracks(track_ids, top_n=limit)

        if not recommendations:
            raise HTTPException(status_code=404, detail="No recommendations found for the given IDs")

        # If exclude_user_id provided, remove tracks that the user has disliked
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

# Récupère une liste de recommandations d'artistes similaires à une ou plusieurs artistes d'entrée
@app.get("/reco/artists", tags=["Recommandations"], summary="Recommandations d'artistes similaires")
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

# Récupère tout les genres avec leurs informations
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

# Récupère toutes les musiques d'un genre spécifique par son ID
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

# Créer une nouvelle playlist avec ses informations et les musiques sélectionnées
@app.post("/playlists", tags=["Playlists"], summary="Créer une nouvelle playlist")
def create_playlist(data: PlaylistCreate):
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

# Récupère une playlist spécifique avec toutes ses tracks
@app.get("/playlists/{playlist_id}", tags=["Playlists"], summary="Détails complets d'une playlist")
def get_playlist_by_id(playlist_id: int):
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

# Supprimer une playlist et toutes ses associations (playlist_track, playlist_user)
@app.delete("/playlists/{playlist_id}", tags=["Playlists"], summary="Supprimer une playlist")
def delete_playlist(playlist_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        # Récupérer le nom de la playlist pour décider d'un nettoyage additionnel
        cur.execute("SELECT playlist_name, playlist_image FROM sae.playlist WHERE playlist_id = %s", (playlist_id,))
        row = cur.fetchone()
        playlist_name = None
        playlist_image = None
        if row:
            playlist_name = row.get('playlist_name')
            playlist_image = row.get('playlist_image')

        # Si la playlist est une playlist spéciale de type 'Titres liké',
        # supprimer aussi les réactions associées (liked/disliked) pour les utilisateurs liés.
        try:
            if playlist_name and playlist_name.lower().strip() in ('titres liké',):
                # Récupérer les user_id liés à cette playlist
                cur.execute("SELECT user_id FROM sae.playlist_user WHERE playlist_id = %s", (playlist_id,))
                users = cur.fetchall()
                user_ids = [u['user_id'] for u in users if u.get('user_id')]
                if user_ids:
                    # Supprimer les réactions pour ces users sur les tracks de la playlist
                    cur.execute(
                        "DELETE FROM sae.user_reaction WHERE target_type = 'track' AND target_id IN (SELECT track_id FROM sae.playlist_track WHERE playlist_id = %s) AND user_id = ANY(%s)",
                        (playlist_id, user_ids)
                    )
                    # Also remove these tracks from users' favorites (user_favorite_tracks)
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
                                    # per-user favorite cleanup should not block overall deletion
                                    pass
                    except Exception:
                        # don't block main deletion if favorite cleanup fails
                        pass
        except Exception:
            # ne pas bloquer la suppression principale si cleanup échoue
            pass

        # Désactiver temporairement les triggers si nécessaire
        cur.execute("SET session_replication_role = 'replica';")
        
        # Supprimer dans le bon ordre
        cur.execute("DELETE FROM sae.playlist_track WHERE playlist_id = %s", (playlist_id,))
        cur.execute("DELETE FROM sae.playlist_user WHERE playlist_id = %s", (playlist_id,))
        cur.execute("DELETE FROM sae.playlist WHERE playlist_id = %s", (playlist_id,))

        # Attempt to delete playlist image file from uploads
        try:
            if playlist_image:
                uploads_dir = os.path.join(os.path.dirname(__file__), '..', 'web', 'uploads', 'playlists')
                image_path = os.path.join(uploads_dir, playlist_image)
                if os.path.exists(image_path):
                    os.remove(image_path)
        except Exception:
            pass
        
        # Réactiver les triggers
        cur.execute("SET session_replication_role = 'origin';")
        
        conn.commit()
        return {"message": "Playlist supprimée"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Récupère les playlists d'un utilisateur spécifique par son ID
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

# Met à jour les tracks d'une playlist (remplace toutes les tracks actuelles par une nouvelle liste)
@app.post("/playlists/{playlist_id}/tracks", tags=["Playlists"], summary="Remplacer les musiques d'une playlist")
def update_tracks_in_playlist(playlist_id: int, data: PlaylistUpdateTracks):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # On vide la playlist actuelle pour simplifier la mise à jour
        cur.execute("DELETE FROM sae.playlist_track WHERE playlist_id = %s", (playlist_id,))
        for idx, t_id in enumerate(data.track_ids):
            cur.execute("INSERT INTO sae.playlist_track (playlist_id, track_id, position) VALUES (%s, %s, %s)", (playlist_id, t_id, idx))
        conn.commit()
        return {"message": "Liste de lecture mise à jour"}
    finally:
        conn.close()

# Supprimer une track spécifique d'une playlist
@app.delete("/playlists/{playlist_id}/tracks/{track_id}", tags=["Playlists"], summary="Supprimer une musique d'une playlist")
def remove_track_from_playlist(playlist_id: int, track_id: int):
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

        # Vérifier s'il reste des tracks
        cur.execute("SELECT COUNT(*) as cnt FROM sae.playlist_track WHERE playlist_id = %s", (playlist_id,))
        cnt = cur.fetchone()['cnt']

        playlist_deleted = False
        if cnt == 0:
            # supprimer associations utilisateur puis la playlist
            # optionnel: supprimer fichier image si présent
            try:
                # Récupérer le nom du fichier image pour suppression éventuelle
                cur.execute("SELECT playlist_image FROM sae.playlist WHERE playlist_id = %s", (playlist_id,))
                img = cur.fetchone()
                if img and img.get('playlist_image'):
                    image_file = img.get('playlist_image')
                    # tenter suppression fichier (silencieuse)
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
                # ignore and continue
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

# Récupère les playlists d'un utilisateur sans les détails des tracks
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

# Récupère les playlists d'un utilisateur avec leurs détails
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

# Modifie les informations d'une playlist (nom et description)
@app.put("/playlists/{playlist_id}", tags=["Playlists"], summary="Modifier les informations d'une playlist")
def update_playlist_info(playlist_id: int, data: PlaylistUpdateInfo):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        # Vérifier si la playlist existe
        cur.execute("SELECT playlist_id FROM sae.playlist WHERE playlist_id = %s", (playlist_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Playlist non trouvée")

        # Mise à jour
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

# Upload d'une image personnalisée pour une playlist
@app.post("/playlists/{playlist_id}/image", tags=["Playlists"], summary="Uploader une image de playlist")
async def upload_playlist_image(playlist_id: int, file: UploadFile = File(...)):
    # Vérifier le type de fichier
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/avif"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Type de fichier non supporté. Utilisez JPG, PNG, WebP ou AVIF.")
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        
        # Vérifier que la playlist existe
        cur.execute("SELECT playlist_id, playlist_image FROM sae.playlist WHERE playlist_id = %s", (playlist_id,))
        playlist = cur.fetchone()
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist non trouvée")
        
        # Supprimer l'ancienne image si elle existe
        if playlist['playlist_image']:
            old_path = os.path.join(UPLOADS_DIR, 'playlists', playlist['playlist_image'])
            if os.path.exists(old_path):
                os.remove(old_path)
        
        # Générer un nom de fichier unique
        ext = os.path.splitext(file.filename)[1] or '.jpg'
        filename = f"{playlist_id}_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(UPLOADS_DIR, 'playlists', filename)
        
        # Sauvegarder le fichier
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Mettre à jour la base de données
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

# Supprimer l'image personnalisée d'une playlist (revient à la mosaïque par défaut)
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

# Autocomplete pour la recherche de musiques par titre, artiste ou album
@app.get("/search/tracks", tags=["Recherche"], summary="Rechercher des musiques")
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

@app.get("/voir_favorite/{user_id}", tags=["Favoris"], summary="Favoris d'un utilisateur")
def get_all_favorite(user_id : int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
    
    try:
        cur = conn.cursor()
        # On utilise la vue tracks_features pour simplifier
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
        
        # Compter le total
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

@app.post("/blindtests", tags=["Playlists"], summary="Enregistrer un blindtest généré")
def create_blindtest(bt: BlindtestCreate):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
        
    try:
        cur = conn.cursor()
        # 1. Créer le blindtest principal
        query = """
            INSERT INTO sae.blindtest (blindtest_name, user_id, difficulty_seconds, total_tracks)
            VALUES (%s, %s, %s, %s) RETURNING blindtest_id;
        """
        cur.execute(query, (bt.name, bt.user_id, bt.difficulty, len(bt.tracks)))
        blindtest_id = cur.fetchone()['blindtest_id']

        # 2. Lier les pistes au blindtest
        for track in bt.tracks:
            # On s'assure que le track_id est un entier valide (pour éviter les erreurs avec les mocks)
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

@app.get("/users/{user_id}/blindtests", tags=["Utilisateurs"], summary="Récupérer l'historique des blindtests")
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

@app.get("/blindtests/{blindtest_id}", tags=["Playlists"], summary="Récupérer un blindtest spécifique")
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

@app.delete("/blindtests/{blindtest_id}", tags=["Playlists"], summary="Supprimer un blindtest")
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


# ===== GESTION DU PROFIL UTILISATEUR (non documenté) =====

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

        # Suppression des données liées avant de supprimer l'utilisateur
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


# ===== ADMIN ENDPOINTS =====

class UpdateUserRole(BaseModel):
    role: str  # "admin" ou "user"

class BanUser(BaseModel):
    banned: bool  # True = bannir, False = débannir

class AdminUpdateProfile(BaseModel):
    user_firstname: Optional[str] = None
    user_lastname: Optional[str] = None
    user_mail: Optional[str] = None
    user_age: Optional[int] = None
    user_gender: Optional[str] = None
    user_location: Optional[str] = None
    user_phonenumber: Optional[str] = None


# Statistiques globales pour le dashboard admin
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


# Liste tous les utilisateurs avec pagination et recherche
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

        # Compter le total
        count_query = f"SELECT COUNT(*) as total FROM sae.users {where_sql}"
        cur.execute(count_query, params)
        total = cur.fetchone()['total']

        # Récupérer les utilisateurs
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


# Détails d'un utilisateur
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

        # Nombre de playlists
        cur.execute("""
            SELECT COUNT(*) as total FROM sae.playlist_user WHERE user_id = %s
        """, (user_id,))
        user['playlists_count'] = cur.fetchone()['total']

        # Favoris
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


# Changer le rôle d'un utilisateur
@app.put("/admin/users/{user_id}/role", tags=["Admin"], summary="Changer le rôle d'un utilisateur")
def admin_update_role(user_id: int, body: UpdateUserRole, requester_id: Optional[int] = Query(None)):
    if body.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="Rôle invalide. Utiliser 'admin' ou 'user'.")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")

    try:
        cur = conn.cursor()

        # Verifier le role actuel de la cible
        cur.execute("SELECT user_status FROM sae.users WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

        target_status = row['user_status']

        # super_admin est intouchable
        if target_status == 'super_admin':
            raise HTTPException(status_code=403, detail="Impossible de modifier le rôle du super administrateur")

        # Pour toucher un admin, il faut etre super_admin
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


# Bannir / Débannir un utilisateur
@app.put("/admin/users/{user_id}/ban", tags=["Admin"], summary="Bannir ou débannir un utilisateur")
def admin_ban_user(user_id: int, body: BanUser, requester_id: Optional[int] = Query(None)):
    new_status = "banned" if body.banned else "user"

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")

    try:
        cur = conn.cursor()

        # Empêcher de bannir un admin/super_admin (sauf si requester est super_admin)
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


# Modifier le profil d'un utilisateur (admin) — mot de passe exclu
@app.put("/admin/users/{user_id}/profile", tags=["Admin"], summary="Modifier le profil d'un utilisateur (admin)")
def admin_update_profile(user_id: int, body: AdminUpdateProfile, requester_id: Optional[int] = Query(None)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")

    try:
        cur = conn.cursor()

        # Vérifier que l'utilisateur existe et son role
        cur.execute("SELECT user_id, user_status FROM sae.users WHERE user_id = %s", (user_id,))
        target = cur.fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

        # Un admin ne peut pas modifier le profil d'un autre admin (seul super_admin peut)
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


# Supprimer un utilisateur (admin)
@app.delete("/admin/users/{user_id}", tags=["Admin"], summary="Supprimer un utilisateur")
def admin_delete_user(user_id: int, requester_id: Optional[int] = Query(None)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")

    try:
        cur = conn.cursor()

        # Empêcher de supprimer un admin/super_admin (sauf si requester est super_admin)
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

        # Supprimer les données liées
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


# Supprimer une track (modération)
@app.delete("/admin/tracks/{track_id}", tags=["Admin"], summary="Supprimer une musique (modération)")
def admin_delete_track(track_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")

    try:
        cur = conn.cursor()

        # Supprimer dans les tables liées
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


# Supprimer une playlist (modération)
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
    # Lance le serveur sur le port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)