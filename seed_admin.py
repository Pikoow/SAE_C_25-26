"""
Script pour créer le compte super-admin dans la base de données MuSE.
Usage : python seed_admin.py
"""
import psycopg2
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": "localhost",
    "dbname": os.getenv("POSTGRES_DBNAME"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "port": int(os.getenv("POSTGRES_PORT", 5432))
}

ADMIN_EMAIL    = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_FIRST    = os.getenv("ADMIN_FIRST_NAME")
ADMIN_LAST     = os.getenv("ADMIN_LAST_NAME")

def main():
    print("=== Création du compte Super Admin ===\n")

    hashed = bcrypt.hashpw(ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cur = conn.cursor()

        # Verifier si le compte admin existe deja
        cur.execute("SELECT user_id FROM sae.users WHERE user_mail = %s", (ADMIN_EMAIL,))
        existing = cur.fetchone()

        if existing:
            # Mettre a jour le statut en super_admin si le compte existe
            cur.execute(
                "UPDATE sae.users SET user_status = 'super_admin', user_password = %s WHERE user_mail = %s",
                (hashed, ADMIN_EMAIL)
            )
            print(f" Compte super_admin existant mis a jour (ID: {existing[0]})")
        else:
            cur.execute(
                """INSERT INTO sae.users
                    (user_firstname, user_lastname, user_mail, user_password, user_status, user_year_created)
                 VALUES (%s, %s, %s, %s, 'super_admin', NOW())
                 RETURNING user_id""",
                (ADMIN_FIRST, ADMIN_LAST, ADMIN_EMAIL, hashed)
            )
            new_id = cur.fetchone()[0]
            print(f" Compte admin créé avec succès (ID: {new_id})")

        print(f"\n  Email    : {ADMIN_EMAIL}")
        print(f"  Password : {ADMIN_PASSWORD}")
        print(f"  Rôle     : admin")
        print("\n=== Terminé ===")

        cur.close()
        conn.close()

    except Exception as e:
        print(f" Erreur : {e}")

if __name__ == "__main__":
    main()
