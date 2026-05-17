import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from db import query

def open_shift_assignment(parent):
    win = tk.Toplevel(parent)
    win.title("Назначение смен")
    win.geometry("900x500")
    win.grab_set()

    top_frame = tk.Frame(win)
    top_frame.pack(fill="x", padx=10, pady=5)

    tk.Label(top_frame, text="Смена:").pack(side="left")
    shift_combo = ttk.Combobox(top_frame, state="readonly", width=40)
    shift_combo.pack(side="left", padx=5)

    def load_shifts():
        shifts = query("""
            SELECT id_shift, shift_date, shift_start, shift_end
            FROM Shift
            ORDER BY shift_date DESC, shift_start DESC
        """, fetch=True)
        shift_list = []
        shift_ids = []
        for sid, date, start, end in shifts:
            label = f"{date} | {start.strftime('%H:%M')}–{end.strftime('%H:%M')}"
            shift_list.append(label)
            shift_ids.append(sid)
        shift_combo['values'] = shift_list
        shift_combo.shift_ids = shift_ids  
        if shift_list:
            shift_combo.current(0)
            load_assigned()

    cols = ("ID", "ФИО", "Должность", "Часы", "Статус")
    tree = ttk.Treeview(win, columns=cols, show="headings", height=18)
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=140 if col == "ФИО" else 80)
    tree.pack(fill="both", expand=True, padx=10, pady=5)

    assigned_ids = set()

    def load_assigned():
        if not shift_combo.get():
            return
        idx = shift_combo.current()
        shift_id = shift_combo.shift_ids[idx]

        employees = query("""
            SELECT e.id_employee, e.ful_name, p.title, e.hours, e.status
            FROM Employee e
            JOIN Post p ON e.id_pos = p.id_pos
            WHERE e.status = 'Активен'
            ORDER BY e.ful_name
        """, fetch=True)

        assigned = query("SELECT id_employee FROM Employee_Shift WHERE id_shift = %s", (shift_id,), fetch=True)
        assigned_ids.clear()
        assigned_ids.update(row[0] for row in assigned)

        for item in tree.get_children():
            tree.delete(item)

        for emp in employees:
            emp_id = emp[0]
            tag = "assigned" if emp_id in assigned_ids else ""
            tree.insert("", "end", values=emp, tags=(tag,))

        tree.tag_configure("assigned", background="#d4edda")

    def toggle_assignment():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите сотрудника")
            return

        emp_id = tree.item(sel[0])["values"][0]
        idx = shift_combo.current()
        if idx == -1:
            messagebox.showwarning("Ошибка", "Выберите смену")
            return
        shift_id = shift_combo.shift_ids[idx]

        if emp_id in assigned_ids:
            query("DELETE FROM Employee_Shift WHERE id_shift = %s AND id_employee = %s", (shift_id, emp_id))
            assigned_ids.remove(emp_id)
            messagebox.showinfo("Успех", "Сотрудник удалён из смены")
        else:
            query("INSERT INTO Employee_Shift (id_employee, id_shift) VALUES (%s, %s)", (emp_id, shift_id))
            assigned_ids.add(emp_id)
            messagebox.showinfo("Успех", "Сотрудник добавлен в смену")

        load_assigned()

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Добавить/Удалить из смены", command=toggle_assignment, width=22).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Обновить", command=load_shifts, width=10).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Закрыть", command=win.destroy, width=10).pack(side="right", padx=5)

    load_shifts()