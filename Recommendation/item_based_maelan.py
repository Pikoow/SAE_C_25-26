import psycopg2
import psutil
import os
from dotenv import load_dotenv
import time

load_dotenv()

DB_CONFIG = {
    'dbname': os.getenv("POSTGRES_DBNAME"),
    'user': os.getenv("POSTGRES_USER"),
    'password': os.getenv("POSTGRES_PASSWORD"),
    'host': 'localhost',
    'port': os.getenv("POSTGRES_PORT", '5432')
}

##########################################################
# FONCTIONS GÉNÉRALES BASE DE DONNÉES
##########################################################

def db_connect():
    """Retourne une connexion PostgreSQL."""
    return psycopg2.connect(**DB_CONFIG)

##########################################################
# FONCTION POUR AFFICHER TOUS LES GENRES PRINCIPAUX EXISTANTS DE LA BASE DE DONNÉES
##########################################################

def afficher_genres_principaux(par_ligne):

    query = """SELECT DISTINCT genre_title FROM SAE.genre INNER JOIN sae.tracks ON genre_title=track_genre_top;"""

    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(query)
        genres = [g[0] for g in cur.fetchall()]
        cur.close()
        conn.close()

        print("\nGenres disponibles :\n")
        for i, genre in enumerate(genres, 1):
            print(f"-{genre:<25}", end="")
            if i % par_ligne == 0:
                print()

    except Exception as e:
        print("Erreur lors du chargement des genres :", e)

##########################################################
# FONCTION POUR AFFICHER TOUS LES GENRES SECONDAIRES EXISTANTS DE LA BASE DE DONNÉES
##########################################################

def afficher_genres_secondaires(par_ligne):

    query = """SELECT DISTINCT g.genre_title
        FROM sae.tracks t
        JOIN sae.genre g
          ON g.genre_id = ANY(string_to_array(t.track_genre, ',')::INT[])
        WHERE t.track_genre IS NOT NULL
          AND t.track_genre <> ''
        ORDER BY g.genre_title;"""

    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(query)
        genres = [g[0] for g in cur.fetchall()]
        cur.close()
        conn.close()

        print("\nGenres disponibles :\n")
        for i, genre in enumerate(genres, 1):
            print(f"-{genre:<25}", end="")
            if i % par_ligne == 0:
                print()

    except Exception as e:
        print("Erreur lors du chargement des genres :", e)


##########################################################
# FONCTION POUR OBTENIR LES 5 MEILLEURS MUSIQUES DU STYLE  AVEC GENRE PRINCIPALE
##########################################################

def top_5_genre_principal(genre_pref):

    query = """
    SELECT 
        track_title,
        SUM(track_listens) AS total_listens,
        SUM(track_favorite) AS total_favorites,
        (SUM(track_listens) + SUM(track_favorite)) AS score
    FROM sae.tracks
    WHERE track_genre_top = %s
    GROUP BY track_title
    ORDER BY score DESC
    LIMIT 5;
    """

    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(query, [genre_pref])
        resutats = cur.fetchall()
        cur.close()
        conn.close()
        return resutats

    except Exception as e:
        print("Erreur :", e)
        return []

##########################################################
# FONCTION POUR OBTENIR ID DU GENRE DEMANDE
##########################################################

def obtient_id_genre(genre_pref):

    query = """SELECT genre_id FROM sae.genre WHERE genre_title = %s LIMIT 1;"""

    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(query, [genre_pref])
        resutat = cur.fetchone()
        cur.close()
        conn.close()
        return resutat[0] if resutat else None

    except Exception as e:
        print("Erreur :", e)
        return []


##########################################################
# FONCTION POUR OBTENIR LES 5 MUSIQUES LES PLUS ECOUTER AVEC LE GENRE EN SECONDAIRE
##########################################################

def top_5_avec_genre_secondaire(genre_pref):

    genre_id = obtient_id_genre(genre_pref)

    if genre_id is None:
        return []

    query = """
    SELECT 
        track_title,
        SUM(track_listens) AS total_listens,
        SUM(track_favorite) AS total_favorites,
        (SUM(track_listens) + SUM(track_favorite)) AS score
    FROM sae.tracks
    WHERE %s = ANY(string_to_array(track_genre, ',')::INT[])
    GROUP BY track_title
    ORDER BY score DESC
    LIMIT 5;
    """

    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(query,[genre_id])
        resutats = cur.fetchall()
        cur.close()
        conn.close()
        return resutats

    except Exception as e:
        print("Erreur :", e)
        return []


##########################################################
# MENU PRINCIPAL
##########################################################

def main():

    print("Choisis le type de genre de la musique:")
    print("1 - Genre principal du son")
    print("2 - Genre secondaire du son(Pour de nouvelles découvertes)")

    choix = input("Ton choix : ").strip()
    
    if choix == "1":
        afficher_genres_principaux(6)
    if choix == "2":
        afficher_genres_secondaires(6)

    genre_pref = input("\n \nNom du genre : ").strip()

    process = psutil.Process(os.getpid())
    start_time = time.perf_counter()
    cpu_start = process.cpu_times()
    mem_start = process.memory_info().rss

    if choix == "1":
        resutats = top_5_genre_principal(genre_pref)
    elif choix == "2":
        resutats = top_5_avec_genre_secondaire(genre_pref)
    else:
        print("\n \nChoix invalide")
        return

    end_time = time.perf_counter()
    cpu_end = process.cpu_times()
    mem_end = process.memory_info().rss
    elapsed_time = end_time - start_time
    cpu_used = (cpu_end.user + cpu_end.system) - (cpu_start.user + cpu_start.system)
    ram_used = (mem_end - mem_start)/1024/1024
    
    psutil.cpu_times()

    if not resutats:
        print(f"\nAucun titre trouvé pour le genre : {genre_pref}")
    else:
        print(f"\nTop 5 titres pour le genre '{genre_pref}':\n")
        for i, track in enumerate(resutats, 1):
            title, listens, favorites, score = track
            print(f"{i}. {title} — Écoutes : {listens}, Favoris : {favorites}, Score : {score}")

    print(f"\nTemps de réponse : {elapsed_time:.3f} secondes")
    print(f"CPU utilisé par le modèle : {cpu_used:.3f} secondes")
    print(f"RAM utilisé par le modèle: {ram_used:.3f} MB")

if __name__ == "__main__":
    main()
