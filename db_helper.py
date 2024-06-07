import mysql.connector
from mysql.connector import Error

def get_db_cursor():
    try:
        db = mysql.connector.connect(
            host="auth-db470.hstgr.io",
            user="u627443942_cb001",
            password="Cb20@52&",
            database="u627443942_cb001"
        )
        cursor = db.cursor()
        return db, cursor
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None, None

def close_db_connection(db, cursor):
    if cursor:
        cursor.close()
    if db:
        db.close()

def get_dentist_info(params):
    db, cursor = get_db_cursor()
    if not db or not cursor:
        return {"error": "Failed to connect to the database"}

    try:
        cursor.callproc('sp_get_dentist_info', [params.get('name', ''), params.get('specialist', ''), params.get('procedure', '')])
        result = []
        for res in cursor.stored_results():
            result.extend(res.fetchall())
            print(result)
        return result
    except Error as e:
        print(f"Error executing stored procedure 'sp_get_dentist_info': {e}")
        return {"error": f"Failed to retrieve dentist info: {e}"}
    finally:
        close_db_connection(db, cursor)

def get_specialist():
    db, cursor = get_db_cursor()
    if not db or not cursor:
        return {"error": "Failed to connect to the database"}

    try:
        cursor.callproc('sp_get_all_specialities')
        result = []
        for res in cursor.stored_results():
            result.extend(res.fetchall())
            print(result)
        return result
    except Error as e:
        print(f"Error executing stored procedure 'sp_get_all_specialities': {e}")
        return {"error": f"Failed to retrieve specialists: {e}"}
    finally:
        close_db_connection(db, cursor)

def get_procedures(params):
    db, cursor = get_db_cursor()
    if not db or not cursor:
        return {"error": "Failed to connect to the database"}

    try:
        cursor.callproc('sp_get_procedures_by_specialty', [params.get("specialist", '')])
        result = []
        for res in cursor.stored_results():
            result.extend(res.fetchall())
            print(result)
        return result
    except Error as e:
        print(f"Error executing stored procedure 'sp_get_procedures_by_specialty': {e}")
        return {"error": f"Failed to retrieve procedures: {e}"}
    finally:
        close_db_connection(db, cursor)
