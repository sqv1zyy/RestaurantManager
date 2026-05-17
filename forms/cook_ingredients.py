import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from db import query


def open_cook_ingredients(parent):
    win = tk.Toplevel(parent)
    win.title("Ингредиенты — Повар")
    win.geometry("850x600")
    win.transient(parent)
    win.grab_set()

    cols = ("ID", "Название", "Ед. изм.", "Остаток", "Срок годности", "Цена закупки")
    tree = ttk.Treeview(win, columns=cols, show="headings")
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=120 if col == "Название" else 90)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    filter_frame = tk.Frame(win)
    filter_frame.pack(fill="x", padx=10, pady=(0, 5))

    tk.Label(filter_frame, text="Фильтр:").pack(side="left", padx=(0, 5))

    tk.Label(filter_frame, text="Название:").pack(side="left", padx=(5, 2))
    name_filter = tk.Entry(filter_frame, width=12)
    name_filter.pack(side="left", padx=(0, 10))
    name_filter.bind("<KeyRelease>", lambda e: apply_filters())

    tk.Label(filter_frame, text="Остаток <=").pack(side="left", padx=(5, 2))
    stock_filter = tk.Entry(filter_frame, width=8)
    stock_filter.pack(side="left", padx=(0, 10))
    stock_filter.bind("<KeyRelease>", lambda e: apply_filters())

    tk.Label(filter_frame, text="Годен ≤ дней:").pack(side="left", padx=(5, 2))
    exp_days_filter = tk.Entry(filter_frame, width=6)
    exp_days_filter.pack(side="left", padx=(0, 10))
    exp_days_filter.bind("<KeyRelease>", lambda e: apply_filters())

    tk.Label(filter_frame, text="Поставка от (ГГГГ-ММ-ДД):").pack(side="left", padx=(5, 2))
    delivery_from = tk.Entry(filter_frame, width=10)
    delivery_from.pack(side="left", padx=(0, 5))
    delivery_from.bind("<KeyRelease>", lambda e: apply_filters())

    tk.Label(filter_frame, text="до:").pack(side="left", padx=(2, 2))
    delivery_to = tk.Entry(filter_frame, width=10)
    delivery_to.pack(side="left", padx=(0, 10))
    delivery_to.bind("<KeyRelease>", lambda e: apply_filters())

    def last_week():
        today = datetime.today().date()
        week_ago = today - timedelta(days=7)
        delivery_from.delete(0, tk.END)
        delivery_from.insert(0, week_ago.strftime("%Y-%m-%d"))
        delivery_to.delete(0, tk.END)
        delivery_to.insert(0, today.strftime("%Y-%m-%d"))
        apply_filters()

    tk.Button(filter_frame, text="Прошлая неделя", command=last_week, width=13).pack(side="left", padx=(0, 10))

    def reset_filters():
        name_filter.delete(0, tk.END)
        stock_filter.delete(0, tk.END)
        exp_days_filter.delete(0, tk.END)
        delivery_from.delete(0, tk.END)
        delivery_to.delete(0, tk.END)
        apply_filters()

    tk.Button(filter_frame, text="Сбросить", command=reset_filters, width=8).pack(side="right")

    def apply_filters():
        name_val = name_filter.get().strip()
        stock_val = stock_filter.get().strip()
        exp_days_val = exp_days_filter.get().strip()
        del_from = delivery_from.get().strip()
        del_to = delivery_to.get().strip()

        conditions = []
        params = []

        if name_val:
            conditions.append("LOWER(name_i) LIKE LOWER(%s)")
            params.append(f"%{name_val}%")
        if stock_val:
            try:
                stock_num = float(stock_val)
                conditions.append("amount <= %s")
                params.append(stock_num)
            except ValueError:
                pass
        if exp_days_val:
            try:
                days = int(exp_days_val)
                conditions.append("expiration_date <= %s")
                params.append(datetime.today().date() + timedelta(days=days))
            except ValueError:
                pass
        if del_from:
            try:
                d_from = datetime.strptime(del_from, "%Y-%m-%d").date()
                conditions.append("delivery_date >= %s")
                params.append(d_from)
            except ValueError:
                pass
        if del_to:
            try:
                d_to = datetime.strptime(del_to, "%Y-%m-%d").date()
                conditions.append("delivery_date <= %s")
                params.append(d_to)
            except ValueError:
                pass

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        query_sql = f"""
            SELECT id_ingredient, name_i, ed_izmer, amount, expiration_date, purchase_price
            FROM Ingredient
            {where_clause}
            ORDER BY name_i
        """

        for item in tree.get_children():
            tree.delete(item)

        rows = query(query_sql, tuple(params), fetch=True)
        for row in rows:
            tree.insert("", "end", values=row)

    def edit_amount():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите ингредиент")
            return

        values = tree.item(sel[0])["values"]
        ing_id = int(values[0])
        name = values[1]
        current = float(values[3])

        dialog = tk.Toplevel(win)
        dialog.title(f"Изменить остаток: {name}")
        dialog.geometry("300x150")
        dialog.transient(win)
        dialog.grab_set()

        tk.Label(dialog, text=f"Текущий остаток: {current}").pack(pady=5)
        tk.Label(dialog, text="Новое количество (≥0):").pack(pady=5)

        new_var = tk.StringVar(value=str(current))
        entry = tk.Entry(dialog, textvariable=new_var)
        entry.pack(pady=5)
        entry.focus()

        def save():
            try:
                new_val = float(new_var.get())
                if new_val < 0:
                    raise ValueError
                query("UPDATE Ingredient SET amount = %s WHERE id_ingredient = %s", (new_val, ing_id))
                messagebox.showinfo("Успех", "Остаток обновлён")
                dialog.destroy()
                apply_filters()
            except ValueError:
                messagebox.showerror("Ошибка", "Введите неотрицательное число")

        tk.Button(dialog, text="Сохранить", command=save, width=12).pack(pady=5)
        tk.Button(dialog, text="Отмена", command=dialog.destroy, width=12).pack()

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Изменить количество", command=edit_amount, width=20).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Обновить", command=reset_filters, width=12).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Закрыть", command=win.destroy, width=12).pack(side="right", padx=5)

    apply_filters()