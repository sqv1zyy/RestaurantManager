import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from db import query

def open_reserve_table(parent):
    win = tk.Toplevel(parent)
    win.title("Бронирование столиков")
    win.geometry("700x450")
    win.grab_set()

    cols = ("ID", "Номер", "Мест", "Статус", "Время брони")
    tree = ttk.Treeview(win, columns=cols, show="headings")
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=100 if col == "ID" else 120)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    def load_tables():
        for item in tree.get_children():
            tree.delete(item)
        tables = query("SELECT id_table, table_number, seats, reserved, reservation_time FROM TableInfo ORDER BY table_number", fetch=True)
        for row in tables:
            status = "Забронирован" if row[3] else "Свободен"
            time_str = row[4].strftime('%Y-%m-%d %H:%M') if row[4] else ""
            tree.insert("", "end", values=(row[0], row[1], row[2], status, time_str))

    load_tables()

    def reserve():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите столик")
            return

        table_id = tree.item(sel[0])["values"][0]
        is_reserved = tree.item(sel[0])["values"][3] == "Забронирован"

        if is_reserved:
            confirm = messagebox.askyesno("Подтверждение", "Столик уже забронирован. Отменить бронь?")
            if confirm:
                query("UPDATE TableInfo SET reserved = FALSE, reservation_time = NULL WHERE id_table = %s", (table_id,))
                messagebox.showinfo("Успех", "Бронь отменена")
                load_tables()
            return


        dialog = tk.Toplevel(win)
        dialog.title("Забронировать столик")
        dialog.geometry("300x180")
        dialog.transient(win)
        dialog.grab_set()

        tk.Label(dialog, text="Дата (ГГГГ-ММ-ДД):").pack(pady=3)
        date_var = tk.StringVar(value=(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))
        tk.Entry(dialog, textvariable=date_var).pack(pady=3)

        tk.Label(dialog, text="Время (ЧЧ:ММ):").pack(pady=3)
        time_var = tk.StringVar(value="19:00")
        tk.Entry(dialog, textvariable=time_var).pack(pady=3)

        def confirm_reserve():
            try:
                dt_str = f"{date_var.get()} {time_var.get()}"
                reservation_dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
                if reservation_dt <= datetime.now():
                    raise ValueError("Время брони должно быть в будущем")

                query("""
                    UPDATE TableInfo 
                    SET reserved = TRUE, reservation_time = %s 
                    WHERE id_table = %s
                """, (reservation_dt, table_id))
                messagebox.showinfo("Успех", "Столик забронирован")
                dialog.destroy()
                load_tables()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Неверный формат даты/времени или дата в прошлом:\n{e}")

        tk.Button(dialog, text="Забронировать", command=confirm_reserve).pack(pady=8)
        tk.Button(dialog, text="Отмена", command=dialog.destroy).pack()

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Забронировать / Отменить", command=reserve, width=20).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Обновить", command=load_tables, width=10).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Закрыть", command=win.destroy, width=10).pack(side="right", padx=5)