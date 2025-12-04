# track_search.py
import psycopg2
from psycopg2 import sql

DB_CONFIG = {
    'dbname': 'mydb',
    'user': 'admin',
    'password': 'admin',
    'host': 'localhost',
    'port': '5432'
}

def search_track_by_name_and_artist(track_name, artist_name):
    """
    Recherche une track par son nom et celui de l'artiste
    Retourne les informations détaillées de la track
    """
    try:
        # Établir la connexion
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print(f"\nRecherche de la track: '{track_name}' par l'artiste: '{artist_name}'")
        
        # Requête SQL pour rechercher la track avec les informations de l'artiste
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
            t.track_composer,
            t.track_lyricist,
            t.track_bit_rate,
            a.artist_name,
            a.artist_id,
            al.album_title,
            al.album_id
        FROM sae.tracks t
        LEFT JOIN sae.album_artist_track aat ON t.track_id = aat.track_id
        LEFT JOIN sae.artist a ON a.artist_id = aat.artist_id
        LEFT JOIN sae.album al ON al.album_id = aat.album_id
        WHERE LOWER(t.track_title) LIKE LOWER(%s)
            AND LOWER(a.artist_name) LIKE LOWER(%s)
        ORDER BY t.track_listens DESC
        LIMIT 10;
        """
        
        # Recherche avec correspondance partielle (LIKE)
        cursor.execute(query, (f'%{track_name}%', f'%{artist_name}%'))
        tracks = cursor.fetchall()
        
        if not tracks:
            print(f"\nAucune track trouvée pour '{track_name}' par '{artist_name}'")
            
            # Recherche alternative: juste par nom de track
            cursor.execute("""
            SELECT
                track_id, --
                track_title, --
                track_duration, --
                track_genre, --
                track_tags,
                track_listens, --
                track_favorite, --
                track_interest, --
                track_date_recorded,
                track_composer, --
                track_lyricist, --
                track_bit_rate, --
                album_id, --
                album_titles, --
                artist_ids, --
                artist_names, --  
            FROM sae.tracks_features
            WHERE LOWER(t.track_title) LIKE LOWER(%s)
            ORDER BY t.track_listens DESC;
            """, (f'%{track_name}%',))
        
        else:
            print(f"\n{len(tracks)} track(s) trouvée(s):")
            
            for i, track in enumerate(tracks, 1):
                print(f"\n{'='*60}")
                print(f"TRACK #{i}")
                print(f"{'='*60}")
                
                # Formatage des informations
                print(f"Id: {track[0]}")
                print(f"Titre: {track[1]}")
                print(f"Artiste: {track[12] or 'Inconnu'}")
                
                if track[2]:  # Durée
                    minutes = track[2] // 60
                    seconds = track[2] % 60
                    print(f"Durée: {minutes}:{seconds:02d}")

                if track[3]:
                    print(f"Tags : {track[3]}")

                if track[4]:  # Genres
                    genres_list = eval(track[4])
                    genre_titles = [g.get('genre_title') for g in genres_list if 'genre_title' in g]
                    print("Genres:", ", ".join(genre_titles))

                if track[5]:  # Écoutes
                    print(f"Nombre d'écoutes: {track[5]:,}")
                
                if track[6]:  # Favoris
                    print(f"Favoris: {track[6]}")
                
                if track[7]:  # Intérêt
                    print(f"Score d'intérêt: {track[7]:.2f}")
                
                if track[8]:  # Date d'enregistrement
                    print(f"Enregistrée le: {track[8]}")
                
                if track[9]:  # Compositeur
                    print(f"Compositeur: {track[9]}")
                
                if track[10]:  # Parolier
                    print(f"Parolier: {track[10]}")
                
                if track[11]:  # Bitrate
                    print(f"Bitrate: {track[11]} kbps")
                
                if track[14]:  # Album
                    print(f"Album: {track[14]}")
                
                print(f"ID de la track: {track[0]}")
                if track[13]:  # ID artiste
                    print(f"ID de l'artiste: {track[13]}")
        
        cursor.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        print(f"Erreur de connexion: {e}")
    except psycopg2.Error as e:
        print(f"Erreur SQL: {e}")

def main():
    while True:
        print("\n" + "-"*40)
        track_name = input("Entrez le nom de la track (ou partie du nom): ").strip()
        
        if not track_name:
            print("Le nom de la track est requis!")
            continue
            
        artist_name = input("Entrez le nom de l'artiste (optionnel): ").strip()
        
        # Recherche standard
        search_track_by_name_and_artist(track_name, artist_name)

if __name__ == "__main__":
    main()