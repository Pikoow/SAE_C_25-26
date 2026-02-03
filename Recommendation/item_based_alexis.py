import psycopg2
import sys
from dotenv import load_dotenv
import os

load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================
DB_CONFIG = {
    "host": "localhost",
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DBNAME"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "options": "-c search_path=sae,public"
}

def get_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Erreur connexion BDD : {e}")
        sys.exit(1)

# ============================================================
# FONCTIONS
# ============================================================

def print_stats(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM sae.tracks")
        nb_tracks = cur.fetchone()[0]
        
        # On regarde la table des vecteurs
        try:
            cur.execute("SELECT COUNT(*) FROM sae.temporal_features_vectors")
            nb_vectors = cur.fetchone()[0]
        except:
            print("Table 'temporal_features_vectors' introuvable.")
            return

        ratio = (nb_vectors / nb_tracks * 100) if nb_tracks > 0 else 0
        print("\n" + "="*75)
        print(f"Nombre total de tracks : {nb_tracks}")
        print(f"Tracks pouvant recevoir des recommandations : {nb_vectors} ({ratio:.1f}%)")
        print("="*75)

def search_track(conn, term):
    query = """
        SELECT 
            t.track_id, 
            t.track_title, 
            -- On vérifie juste si le vecteur existe pour savoir si on peut recommander
            (tfv.track_id IS NOT NULL) as has_vector
        FROM sae.tracks t
        LEFT JOIN sae.temporal_features_vectors tfv ON t.track_id = tfv.track_id
        WHERE t.track_title ILIKE %s
        ORDER BY has_vector DESC, length(t.track_title) ASC
        LIMIT 10;
    """
    with conn.cursor() as cur:
        cur.execute(query, (f"%{term}%",))
        return cur.fetchall()

def get_recommendations(conn, track_id):
    query = """
        SELECT 
            t.track_title,
            -- Calcul de distance Cosinus via pgvector
            (tfv.audio_vector <=> (SELECT audio_vector FROM sae.temporal_features_vectors WHERE track_id = %s)) as distance
        FROM sae.temporal_features_vectors tfv
        JOIN sae.tracks t ON t.track_id = tfv.track_id
        WHERE t.track_id != %s
        ORDER BY distance ASC
        LIMIT 5;
    """
    with conn.cursor() as cur:
        cur.execute(query, (track_id, track_id))
        return cur.fetchall()

# ============================================================
# MAIN
# ============================================================
def main():
    conn = get_connection()
    print("\nRecommendation sur les données d'echonest")
    print_stats(conn)

    while True:
        try:
            print("\n" + "-"*60)
            search = input("Recherche (Titre) [ou 'q' pour quitter] : ").strip()
            if not search or search.lower() == 'q': break

            results = search_track(conn, search)
            if not results:
                print("Aucun résultat trouvé.")
                continue

            print(f"\nRésultats pour '{search}':")
            # Affichage simplifié sans artiste
            print(f"{'#':<3} {'Musique':<50} | {'Recommendation'}")
            print("-" * 65)
            
            for i, (tid, title, has_vec) in enumerate(results):
                status = "Possible" if has_vec else "Pas de données"
                # Coupe le titre s'il est trop long
                t_aff = (title[:48] + "..") if len(title) > 48 else title
                print(f"{i+1:<3} {t_aff:<50} | {status}")

            choice = input("\nChoisissez un numéro : ")
            if not choice.isdigit(): continue
            idx = int(choice) - 1
            
            if 0 <= idx < len(results):
                sel_id, sel_title, sel_has_vec = results[idx]
                
                if not sel_has_vec:
                    print("\nImpossible : Ce morceau n'a pas été analysé par l'IA (vecteur manquant).")
                    continue

                print(f"\nCalcul des similarités pour '{sel_title}'...")
                recos = get_recommendations(conn, sel_id)
                
                if not recos:
                    print("Aucune recommandation trouvée (peut-être pas assez de vecteurs en base ?).")
                else:
                    print("\nRECOMMANDATIONS (Les plus proches musicalement) :")
                    print(f"{'TITRE':<50} | {'DISTANCE'}")
                    print("=" * 65)
                    for r_title, dist in recos:
                        d_aff = f"{dist:.4f}"
                        rt_aff = (r_title[:48] + "..") if len(r_title) > 48 else r_title
                        print(f"{rt_aff:<50} | {d_aff}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Erreur : {e}")

    conn.close()
    print("\nAu revoir !")

if __name__ == "__main__":
    main()