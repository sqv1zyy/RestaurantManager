import psycopg2
from config import DB_CONFIG
from tkinter import messagebox

def query(sql, params=None, fetch=False):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(sql, params)
        if fetch:
            result = cur.fetchall()
        else:
            conn.commit()
            result = True
        cur.close()
        conn.close()
        return result
    except Exception as e:
        messagebox.showerror("Ошибка БД", str(e))
        return None
    
def query_with_commit(sql, params=None, fetch=False):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(sql, params)
        if fetch:
            result = cur.fetchall()
        else:
            result = None
        conn.commit()  
        cur.close()
        conn.close()
        return result
    except Exception as e:
        messagebox.showerror("Ошибка БД", str(e))
        return None