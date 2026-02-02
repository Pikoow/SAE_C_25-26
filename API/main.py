from fastapi import FastAPI, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Ma Base Musicale API")

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
    return {"message": "Bienvenue sur l'API de ma base de données musicale ! Accédez à /all pour voir les titres."}

@app.get("/all")
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
            LEFT JOIN sae.artist art ON t.artist_id = art.artist_id;
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

if __name__ == "__main__":
    import uvicorn
    # Lance le serveur sur le port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)