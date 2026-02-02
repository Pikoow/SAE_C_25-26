import subprocess
import psycopg2
import sys

# --- CONFIGURATION ---
DB_CONFIG = {
    "host": "localhost",
    "dbname": "postgres",
    "user": "postgres",
    "password": "PASSWORD_HERE",
    "port": 5432
}

def run_sql_file(filename):
    print(f"--- Exécution de {filename} ---")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cur = conn.cursor()
        with open(filename, 'r', encoding='utf-8') as f:
            cur.execute(f.read())
        cur.close()
        conn.close()
        print(f"Succès : {filename} appliqué.\n")
    except Exception as e:
        print(f"Erreur lors de l'exécution de {filename}: {e}")
        sys.exit(1)

def run_python_script(filename):
    print(f"--- Lancement de {filename} ---")
    try:
        # On utilise sys.executable pour s'assurer d'utiliser le même interpréteur
        result = subprocess.run([sys.executable, filename], check=True)
        print(f"Succès : {filename} terminé.\n")
    except subprocess.CalledProcessError as e:
        print(f"Erreur dans le script {filename}: {e}")
        sys.exit(1)

def main():
    print("=== DÉMARRAGE DE LA MISE EN SERVICE DE LA BDD ===\n")

    run_sql_file("Tables/scriptBDDv1.sql")
    # run_sql_file("Tables/scriptBDDdlc.sql")

    run_python_script("script_peuplement/populateFinale.py")
    run_python_script("script_peuplement/populateFinal2.py")
    run_python_script("script_peuplement/populateFinalDLC.py")
    # run_python_script("script_peuplement/populateKeynouns.py")

    print("=== BASE DE DONNÉES OPÉRATIONNELLE ! ===")

if __name__ == "__main__":
    main()