import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from db import query


def open_ingredients(parent):
    win = tk.Toplevel(parent)
    win.title("Управление ингредиентами — Менеджер")
    win.geometry("850x600")
    win.transient(parent)
    win.grab_set() 

    cols = ("ID", "Название", "Ед.изм.", "Остаток", "Поставка", "Годен до", "Цена")
    tree = ttk.Treeview(win, columns=cols, show="headings")
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=100 if col in ("Название", "Годен до") else 80)
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
            SELECT id_ingredient, name_i, ed_izmer, amount, 
                   delivery_date, expiration_date, purchase_price
            FROM Ingredient
            {where_clause}
            ORDER BY name_i
        """

        for item in tree.get_children():
            tree.delete(item)

        rows = query(query_sql, tuple(params), fetch=True)
        for row in rows:
            tree.insert("", "end", values=row)

    def add_ingredient():
        dialog = tk.Toplevel(win)
        dialog.title("Добавить ингредиент")
        dialog.geometry("380x340")
        dialog.transient(win)
        dialog.grab_set()

        tk.Label(dialog, text="Название:").pack(pady=2)
        name_ent = tk.Entry(dialog)
        name_ent.pack()

        tk.Label(dialog, text="Ед. измерения:").pack(pady=2)
        unit_ent = tk.Entry(dialog)
        unit_ent.pack()

        tk.Label(dialog, text="Остаток (≥0):").pack(pady=2)
        amount_ent = tk.Entry(dialog)
        amount_ent.insert(0, "0")
        amount_ent.pack()

        tk.Label(dialog, text="Цена закупки (≥0):").pack(pady=2)
        price_ent = tk.Entry(dialog)
        price_ent.insert(0, "0.00")
        price_ent.pack()

        tk.Label(dialog, text="Срок годности (ГГГГ-ММ-ДД):").pack(pady=2)
        exp_ent = tk.Entry(dialog)
        exp_ent.insert(0, (datetime.today() + timedelta(days=30)).strftime("%Y-%m-%d"))
        exp_ent.pack()

        def save():
            try:
                name = name_ent.get().strip()
                unit = unit_ent.get().strip()
                amount = float(amount_ent.get())
                price = float(price_ent.get())
                exp_date = datetime.strptime(exp_ent.get(), "%Y-%m-%d").date()
                delivery_date = datetime.today().date()

                if not name or not unit:
                    raise ValueError("Название и ед. изм. обязательны")
                if amount < 0 or price < 0:
                    raise ValueError("Остаток и цена ≥ 0")
                if exp_date <= delivery_date:
                    raise ValueError("Срок годности должен быть в будущем")

                query("""
                    INSERT INTO Ingredient (name_i, ed_izmer, amount, delivery_date, expiration_date, purchase_price)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (name, unit, amount, delivery_date, exp_date, price))

                messagebox.showinfo("Успех", f"Добавлен: {name}")
                dialog.destroy()
                apply_filters()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Неверные данные:\n{e}")

        tk.Button(dialog, text="Добавить", command=save, width=15).pack(pady=10)
        tk.Button(dialog, text="Отмена", command=dialog.destroy, width=15).pack()

    def delete_ingredient():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите ингредиент")
            return
        ing_id = int(tree.item(sel[0])["values"][0])
        name = tree.item(sel[0])["values"][1]

        if messagebox.askyesno("Подтверждение", f"Удалить «{name}»? Это может нарушить рецепты!"):
            try:
                query("DELETE FROM Ingredient WHERE id_ingredient = %s", (ing_id,))
                messagebox.showinfo("Успех", "Ингредиент удалён")
                apply_filters()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Невозможно удалить:\n{e}")

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Добавить", command=add_ingredient, width=12).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Удалить", command=delete_ingredient, width=12).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Обновить", command=reset_filters, width=12).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Закрыть", command=win.destroy, width=12).pack(side="right", padx=5)

    apply_filters()