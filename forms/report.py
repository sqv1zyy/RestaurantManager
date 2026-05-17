from tkinter import ttk
import tkinter as tk
from db import query

def open_report(parent):
    win = tk.Toplevel(parent)
    win.title("Отчёт по столам")
    win.geometry("500x300")

    tree = ttk.Treeview(win, columns=("Стол", "Выручка"), show="headings")
    tree.heading("Стол", text="Номер стола")
    tree.heading("Выручка", text="Выручка (₽)")
    tree.pack(fill="both", expand=True)

    data = query("""
        SELECT t.table_number, COALESCE(SUM(o.total_cost), 0)
        FROM TableInfo t
        LEFT JOIN Orderr o ON t.id_table = o.id_table AND o.status = 'Готов'
        GROUP BY t.table_number
        ORDER BY 2 DESC
    """, fetch=True)

    for row in data or []:
        tree.insert("", "end", values=(row[0], f"{row[1]:.2f}"))