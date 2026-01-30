import psycopg2

import en_core_web_sm

DB_CONFIG = {
    'dbname': 'mydb',
    'user': 'admin',
    'password': 'admin',
    'host': 'localhost',
    'port': '5432'
}

# liste de nom (titre même éventuellement)
# liste d'instruments
# liste de genre

def check_keys(id) :
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    query = """
        SELECT album_keynames,album_keynouns
        FROM sae.album
        WHERE album_id = %s
    """
    print("c'est l'id qu'on utilise : ",id,"de type : ",type(id))
    cur.execute(query,id)
    row = cur.fetchall()
    print("keys :  \n\n",row)
    cur.close()
    conn.close()

    if row:
        # print("sigma boy \n\n\n",row[0])
        return row  # album_ids
    return "ça marche pas je crois"


def related_albums_by_keynouns(album_id, limit=10) :
#    Retourne les albums les plus similaires
#    selon le nombre de keynouns en commun.

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    query = """
    WITH target AS (
        SELECT album_keynouns
        FROM sae.album
        WHERE album_id = %s
    )
    SELECT
        al.album_id,
        al.album_title,
        al.album_keynouns,
        COUNT(*) AS score
    FROM sae.album al,
         target t,
         jsonb_array_elements_text(al.album_keynouns) AS kw
    WHERE
        al.album_id != %s
        AND kw IN (
            SELECT jsonb_array_elements_text(t.album_keynouns)
        )
    GROUP BY al.album_id, al.album_title
    ORDER BY score DESC
    LIMIT %s;
    """

    cur.execute(query, (album_id, album_id, limit))
    results = cur.fetchall()

    cur.close()
    conn.close()

    return results

def get_album_id(title):
    # print("ouais on est la")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    query = ("""
        SELECT album_id
        FROM sae.album
        WHERE album_title = %s
    """ )
    # print(title)
    cur.execute(query,(title,))
    row = cur.fetchone()
    # print("voila",row[0])
    # print("row \n\n",row)
    cur.close()
    conn.close()

    if row:
        # print("sigma boy \n\n\n",row[0])
        return row  # album_title
    elif row == "" :
        print("c'est vide")
        return ""
    return "ça marche pas je crois"

def main() : 
    print("\n" + "-"*40)
    album_title = input("Entrez le nom de l'album (ou partie du nom): ").strip()
    # print("not yet",album_title,"is ",type(album_title))
    
    while not album_title:
        print("Le nom de l'album est requis!")
        album_title = input("Entrez le nom de l'album (ou partie du nom): ").strip()
    
    # Recherche standard
    album_id = get_album_id(album_title)
    albums = related_albums_by_keynouns(album_id)
    
    for album in albums :
        print("id :",album[0], "titre :",album[1],"score : ",album[3],"\n")
    print("fin du script")
    return ""
    
    
if __name__ == "__main__":
    main()