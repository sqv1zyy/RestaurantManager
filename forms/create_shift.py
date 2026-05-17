import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from db import query


def open_create_shift(parent):
    win = tk.Toplevel(parent)
    win.title("Создать новую смену")
    win.geometry("360x220")
    win.transient(parent)
    win.grab_set()

    tk.Label(win, text="Дата смены (ГГГГ-ММ-ДД):", font=("Arial", 10)).pack(pady=(10, 2))
    date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
    date_ent = tk.Entry(win, textvariable=date_var, font=("Arial", 10), width=20)
    date_ent.pack()

    tk.Label(win, text="Начало смены (ЧЧ:ММ):", font=("Arial", 10)).pack(pady=(8, 2))
    start_var = tk.StringVar(value="09:00")
    start_ent = tk.Entry(win, textvariable=start_var, font=("Arial", 10), width=20)
    start_ent.pack()

    tk.Label(win, text="Окончание смены (ЧЧ:ММ):", font=("Arial", 10)).pack(pady=(8, 2))
    end_var = tk.StringVar(value="18:00")
    end_ent = tk.Entry(win, textvariable=end_var, font=("Arial", 10), width=20)
    end_ent.pack()

    def save_shift():
        try:
            shift_date = datetime.strptime(date_var.get().strip(), "%Y-%m-%d").date()
            start_time = datetime.strptime(start_var.get().strip(), "%H:%M").time()
            end_time = datetime.strptime(end_var.get().strip(), "%H:%M").time()

            shift_start = datetime.combine(shift_date, start_time)
            shift_end = datetime.combine(shift_date, end_time)

            if shift_end <= shift_start:
                messagebox.showerror("Ошибка", "Окончание смены должно быть позже начала.")
                return

        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты или времени.\nИспользуйте: ГГГГ-ММ-ДД и ЧЧ:ММ")
            return

        try:
            query("""
                INSERT INTO Shift (shift_date, shift_start, shift_end)
                VALUES (%s, %s, %s)
            """, (shift_date, shift_start, shift_end))

            messagebox.showinfo("Успех", f"Смена на {shift_date} ({start_time}–{end_time}) успешно создана!")
            win.destroy()

        except Exception as e:
            messagebox.showerror("Ошибка БД", f"Не удалось создать смену:\n{e}")

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=15)

    tk.Button(btn_frame, text="Создать", command=save_shift, width=12, font=("Arial", 10)).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Отмена", command=win.destroy, width=12, font=("Arial", 10)).pack(side="left", padx=5)

    date_ent.focus()