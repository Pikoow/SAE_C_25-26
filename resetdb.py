import os
import psycopg2
from dotenv import load_dotenv

# Charge les variables du fichier .env
load_dotenv()

# Récupération des identifiants
db_name = os.getenv("POSTGRES_DBNAME")
db_user = os.getenv("POSTGRES_USER")
db_password = os.getenv("POSTGRES_PASSWORD")
db_port = os.getenv("POSTGRES_PORT")

def reset_database():
    try:
        # Connexion à la base de données cible
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            port=db_port,
            host="localhost"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print(f"Connexion à la base '{db_name}' réussie. Suppression des tables en cours...")
        
        # Supprime le schéma public (et tout ce qu'il contient) et le recrée
        cursor.execute("DROP SCHEMA public CASCADE;")
        cursor.execute("CREATE SCHEMA public;")
        cursor.execute(f"GRANT ALL ON SCHEMA public TO {db_user};")
        cursor.execute("GRANT ALL ON SCHEMA public TO public;")
        
        print("Succès : La base de données est maintenant totalement vide.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erreur lors de la réinitialisation : {e}")

if __name__ == "__main__":
    # Demande confirmation avant de tout casser
    confirmation = input("Attention, cela va supprimer TOUTES les données. Continuer ? (o/n) : ")
    if confirmation.lower() == 'o':
        reset_database()
    else:
        print("Annulation.")