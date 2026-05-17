import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from db import query


def open_employee_management(parent):
    win = tk.Toplevel(parent)
    win.title("Управление сотрудниками")
    win.geometry("1000x600")
    win.grab_set()

    cols = ("ID", "ФИО", "Должность", "Телефон", "Часы", "Статус")
    tree = ttk.Treeview(win, columns=cols, show="headings")
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=120 if col == "ФИО" else 80)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    filter_frame = tk.Frame(win)
    filter_frame.pack(fill="x", padx=10, pady=(0, 5))

    tk.Label(filter_frame, text="Фильтр:").pack(side="left", padx=(0, 5))

    filter_entries = {}
    for col in ["Поиск", "Должность", "Телефон"]:
        tk.Label(filter_frame, text=f"{col}:").pack(side="left", padx=(5, 2))
        ent = tk.Entry(filter_frame, width=12)
        ent.pack(side="left", padx=(0, 5))
        ent.bind("<KeyRelease>", lambda e: apply_filters())
        filter_entries[col] = ent

    tk.Label(filter_frame, text="Статус:").pack(side="left", padx=(10, 2))
    status_var = tk.StringVar(value="Все")
    status_combo = ttk.Combobox(
        filter_frame,
        textvariable=status_var,
        values=["Все", "Активен", "Уволен"],
        state="readonly",
        width=10
    )
    status_combo.pack(side="left", padx=(0, 10))
    status_combo.bind("<<ComboboxSelected>>", lambda e: apply_filters())

    def reset_filters():
        for ent in filter_entries.values():
            ent.delete(0, tk.END)
        status_var.set("Все")
        apply_filters()

    tk.Button(filter_frame, text="Сбросить", command=reset_filters, width=8).pack(side="right")

    def apply_filters():
        search_fio = filter_entries["Поиск"].get().strip()
        search_pos = filter_entries["Должность"].get().strip()
        search_phone = filter_entries["Телефон"].get().strip()
        status_filter = status_var.get()

        conditions = []
        params = []

        if search_fio:
            conditions.append("LOWER(e.ful_name) LIKE LOWER(%s)")
            params.append(f"%{search_fio}%")
        if search_pos:
            conditions.append("LOWER(p.title) LIKE LOWER(%s)")
            params.append(f"%{search_pos}%")
        if search_phone:
            conditions.append("e.contact_info LIKE %s")
            params.append(f"%{search_phone}%")
        if status_filter != "Все":
            conditions.append("e.status = %s")
            params.append(status_filter)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        query_sql = f"""
            SELECT e.id_employee, e.ful_name, p.title, e.contact_info, e.hours, e.status
            FROM Employee e
            JOIN Post p ON e.id_pos = p.id_pos
            {where_clause}
            ORDER BY e.status DESC, e.ful_name
        """

        for item in tree.get_children():
            tree.delete(item)

        emps = query(query_sql, tuple(params), fetch=True)
        for row in emps:
            tree.insert("", "end", values=row)

    btn_frame = tk.Frame(win)
    btn_frame.pack(fill="x", padx=10, pady=(0, 10))

    def toggle_status():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите сотрудника")
            return

        values = tree.item(sel[0])["values"]
        emp_id = values[0]
        current_status = values[5]
        new_status = "Уволен" if current_status == "Активен" else "Активен"

        confirm = messagebox.askyesno(
            "Подтверждение",
            f"Изменить статус сотрудника «{values[1]}» на «{new_status}»?"
        )
        if not confirm:
            return

        query("UPDATE Employee SET status = %s WHERE id_employee = %s", (new_status, emp_id))
        messagebox.showinfo("Успех", f"Статус изменён на «{new_status}»")
        apply_filters()

    def edit_hours():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите сотрудника")
            return

        values = tree.item(sel[0])["values"]
        emp_id = values[0]
        name = values[1]
        current_hours = values[4] if values[4] is not None else 0

        dialog = tk.Toplevel(win)
        dialog.title(f"Изменить часы: {name}")
        dialog.geometry("300x120")
        dialog.transient(win)
        dialog.grab_set()

        tk.Label(dialog, text="Отработано часов (≥0):").pack(pady=5)
        hours_var = tk.StringVar(value=str(current_hours))
        entry = tk.Entry(dialog, textvariable=hours_var)
        entry.pack(pady=5)
        entry.focus()

        def save_hours():
            try:
                hours = int(hours_var.get())
                if hours < 0:
                    raise ValueError
                query("UPDATE Employee SET hours = %s WHERE id_employee = %s", (hours, emp_id))
                messagebox.showinfo("Успех", "Часы обновлены")
                dialog.destroy()
                apply_filters()
            except ValueError:
                messagebox.showerror("Ошибка", "Введите целое неотрицательное число")

        tk.Button(dialog, text="Сохранить", command=save_hours).pack(pady=5)
        tk.Button(dialog, text="Отмена", command=dialog.destroy).pack()

    def hire_employee():
        positions = query("SELECT id_pos, title FROM Post ORDER BY title", fetch=True)
        if not positions:
            messagebox.showerror("Ошибка", "Нет доступных должностей")
            return

        dialog = tk.Toplevel(win)
        dialog.title("Принять на работу")
        dialog.geometry("350x320")
        dialog.transient(win)
        dialog.grab_set()

        tk.Label(dialog, text="ФИО:").pack(pady=2)
        name_ent = tk.Entry(dialog)
        name_ent.pack()

        tk.Label(dialog, text="Дата рождения (ГГГГ-ММ-ДД):").pack(pady=2)
        birth_ent = tk.Entry(dialog)
        birth_ent.pack()

        tk.Label(dialog, text="Телефон (логин):").pack(pady=2)
        phone_ent = tk.Entry(dialog)
        phone_ent.pack()

        tk.Label(dialog, text="Пароль:").pack(pady=2)
        pass_ent = tk.Entry(dialog, show="*")
        pass_ent.pack()

        tk.Label(dialog, text="Должность:").pack(pady=2)
        pos_combo = ttk.Combobox(dialog, state="readonly", width=30)
        pos_combo['values'] = [title for _, title in positions]
        pos_combo.current(0)
        pos_combo.pack()

        def save_new_employee():
            ful_name = name_ent.get().strip()
            birth_str = birth_ent.get().strip()
            phone = phone_ent.get().strip()
            password = pass_ent.get()
            selected_title = pos_combo.get()

            if not all([ful_name, birth_str, phone, password, selected_title]):
                messagebox.showwarning("Ошибка", "Все поля обязательны")
                return

            pos_id = next((pid for pid, title in positions if title == selected_title), None)

            try:
                birth_date = datetime.strptime(birth_str, "%Y-%m-%d").date()
                if (datetime.today().date() - birth_date).days < 18 * 365:
                    messagebox.showerror("Ошибка", "Сотрудник должен быть старше 18 лет")
                    return
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД")
                return

            try:
                query("""
                    INSERT INTO Employee (ful_name, id_pos, date_of_birth, contact_info, login, pass, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'Активен')
                """, (ful_name, pos_id, birth_date, phone, phone, password))
                messagebox.showinfo("Успех", f"Сотрудник «{ful_name}» принят на должность «{selected_title}»")
                dialog.destroy()
                apply_filters()
            except Exception as e:
                messagebox.showerror("Ошибка БД", f"Не удалось добавить сотрудника:\n{e}")

        tk.Button(dialog, text="Сохранить", command=save_new_employee, width=15).pack(pady=10)
        tk.Button(dialog, text="Отмена", command=dialog.destroy, width=15).pack()

    tk.Button(btn_frame, text="Принять на работу", command=hire_employee, width=18).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Изменить статус", command=toggle_status, width=15).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Изменить часы", command=edit_hours, width=15).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Обновить", command=reset_filters, width=10).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Закрыть", command=win.destroy, width=10).pack(side="right", padx=5)

    apply_filters()