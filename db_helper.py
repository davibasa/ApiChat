# Author: Dhaval Patel. Codebasics Inc.

import mysql.connector

def get_db_cursor():
    # Open database connection
    db = mysql.connector.connect(
        host="auth-db470.hstgr.io",
        user="u627443942_cb001",
        password="Cb20@52&",
        database="u627443942_cb001"
    )
    # Create a new cursor instance
    cursor = db.cursor()
    return db, cursor


def close_db_connection(db, cursor):
    # disconnect from server
    cursor.close()
    db.close()

def get_dentist_info(params):
    db, cursor = get_db_cursor()
    print(params.get('name', ''))
    print(params.get('specialist', ''))
    print(params.get('procedure', ''))

    cursor.callproc('sp_get_dentist_info', [params.get('name', ''), params.get('specialist', ''), params.get('procedure', '')])
    result = []
    for res in cursor.stored_results():
        result.extend(res.fetchall())
        print(result)

    close_db_connection(db, cursor)
    return result


def get_specialist():
    db, cursor = get_db_cursor()
    cursor.callproc('sp_get_all_specialities')
    result = []
    for res in cursor.stored_results():
        result.extend(res.fetchall())
        print(result)
    close_db_connection(db, cursor)
    return result

def get_procedures(params):
    db, cursor = get_db_cursor()
    cursor.callproc('sp_get_procedures_by_specialty', [params.get("specialist", '')])
    result = []
    for res in cursor.stored_results():
        result.extend(res.fetchall())
        print(result)
    close_db_connection(db, cursor)
    return result
