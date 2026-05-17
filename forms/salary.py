from tkinter import ttk
import tkinter as tk
from db import query

def open_salary(parent):
    win = tk.Toplevel(parent)
    win.title("Расчёт зарплаты")
    win.geometry("500x300")

    emps = query("""
        SELECT e.ful_name, e.hours, p.salary
        FROM Employee e
        JOIN Post p ON e.id_pos = p.id_pos
        WHERE e.status = 'Активен' AND e.hours IS NOT NULL
    """, fetch=True)

    if not emps:
        tk.Label(win, text="Нет данных о зарплате").pack()
        return

    tk.Label(win, text="Сотрудник:").pack()
    names = [e[0] for e in emps]
    combo = ttk.Combobox(win, values=names, state="readonly")
    combo.pack()

    result_label = tk.Label(win, text="", justify="left")
    result_label.pack(pady=10)

    def show():
        name = combo.get()
        for emp in emps:
            if emp[0] == name:
                hours, salary = emp[1], emp[2]
                total = (salary / 160) * hours
                result_label.config(text=f"Оклад: {salary}₽\nЧасы: {hours}\nК выплате: {total:.2f}₽")
                break

    combo.bind("<<ComboboxSelected>>", lambda e: show())