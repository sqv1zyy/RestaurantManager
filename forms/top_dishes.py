import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from db import query

def open_top_dishes(parent):
    win = tk.Toplevel(parent)
    win.title("Топ-N блюд по выручке")
    win.geometry("600x520")

    def pick_date(entry):
        def set_date():
            entry.delete(0, tk.END)
            entry.insert(0, cal.selection_get())
            top.destroy()

        top = tk.Toplevel(win)
        top.title("Выберите дату")
        cal = Calendar(top, selectmode="day", date_pattern="y-mm-dd")
        cal.pack(padx=10, pady=10)
        tk.Button(top, text="Выбрать", command=set_date).pack(pady=5)

    frame = tk.Frame(win)
    frame.pack(pady=10)

    tk.Label(frame, text="Начало:").grid(row=0, column=0, padx=5, sticky='e')
    start = tk.Entry(frame, width=12)
    start.insert(0, "2024-01-01")
    start.grid(row=0, column=1, padx=5)
    tk.Button(frame, text="📅", command=lambda: pick_date(start)).grid(row=0, column=2, padx=2)

    tk.Label(frame, text="Конец:").grid(row=0, column=3, padx=5, sticky='e')
    end = tk.Entry(frame, width=12)
    end.insert(0, "2025-12-31")
    end.grid(row=0, column=4, padx=5)
    tk.Button(frame, text="📅", command=lambda: pick_date(end)).grid(row=0, column=5, padx=2)

    tk.Label(frame, text="Кол-во:").grid(row=1, column=0, padx=5, sticky='e', pady=(10, 0))
    top_n_var = tk.StringVar(value="5")
    top_n_combo = ttk.Combobox(frame, textvariable=top_n_var, values=[str(i) for i in range(1, 21)], width=5, state="readonly")
    top_n_combo.grid(row=1, column=1, padx=5, pady=(10, 0), sticky='w')

    tree = ttk.Treeview(win, columns=("Блюдо", "Продано", "Выручка"), show="headings")
    tree.heading("Блюдо", text="Блюдо")
    tree.heading("Продано", text="Продано (шт)")
    tree.heading("Выручка", text="Выручка (₽)")
    tree.column("Продано", width=80, anchor='center')
    tree.column("Выручка", width=100, anchor='e')
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    def load():
        start_val = start.get()
        end_val = end.get()
        try:
            top_n = int(top_n_var.get())
            if top_n < 1 or top_n > 20:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Количество блюд должно быть от 1 до 20")
            return

        for item in tree.get_children():
            tree.delete(item)

        data = query("SELECT * FROM top_blud(%s, %s, %s)", (start_val, end_val, top_n), fetch=True)
        if data:
            for row in data:
                tree.insert("", "end", values=(row[0], row[1], f"{row[2]:.2f}"))
        else:
            tree.insert("", "end", values=("", "", "Нет данных"))

    tk.Button(win, text="Показать топ", command=load).pack(pady=10)
    load()
