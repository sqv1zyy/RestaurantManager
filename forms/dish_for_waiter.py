import tkinter as tk
from tkinter import ttk
from db import query


def open_menu_view(parent):
    win = tk.Toplevel(parent)
    win.title("Меню ресторана")
    win.geometry("800x550")
    win.transient(parent)
    win.grab_set()

    cols = ("ID", "Блюдо", "Ед. изм.", "Цена", "Ингредиенты")
    tree = ttk.Treeview(win, columns=cols, show="headings")
    for col in cols:
        tree.heading(col, text=col, command=lambda c=col: sort_by(tree, c, False))
        if col == "Блюдо":
            tree.column(col, width=180)
        elif col == "Ингредиенты":
            tree.column(col, width=250)
        elif col == "Цена":
            tree.column(col, width=80, anchor="e")
        else:
            tree.column(col, width=70)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    filter_frame = tk.Frame(win)
    filter_frame.pack(fill="x", padx=10, pady=(0, 5))

    tk.Label(filter_frame, text="Поиск:").pack(side="left", padx=(0, 5))

    tk.Label(filter_frame, text="Название:").pack(side="left", padx=(5, 2))
    name_filter = tk.Entry(filter_frame, width=15)
    name_filter.pack(side="left", padx=(0, 10))
    name_filter.bind("<KeyRelease>", lambda e: apply_filters())

    tk.Label(filter_frame, text="Цена от:").pack(side="left", padx=(5, 2))
    price_from = tk.Entry(filter_frame, width=8)
    price_from.pack(side="left", padx=(0, 5))
    price_from.bind("<KeyRelease>", lambda e: apply_filters())

    tk.Label(filter_frame, text="до:").pack(side="left", padx=(2, 2))
    price_to = tk.Entry(filter_frame, width=8)
    price_to.pack(side="left", padx=(0, 10))
    price_to.bind("<KeyRelease>", lambda e: apply_filters())

    def reset_filters():
        name_filter.delete(0, tk.END)
        price_from.delete(0, tk.END)
        price_to.delete(0, tk.END)
        apply_filters()

    tk.Button(filter_frame, text="Сбросить", command=reset_filters, width=8).pack(side="right")

    def apply_filters():
        name_val = name_filter.get().strip()
        price_from_val = price_from.get().strip()
        price_to_val = price_to.get().strip()

        conditions = []
        params = []

        if name_val:
            conditions.append("LOWER(d.name_dish) LIKE LOWER(%s)")
            params.append(f"%{name_val}%")
        if price_from_val:
            try:
                p_from = float(price_from_val)
                conditions.append("d.price >= %s")
                params.append(p_from)
            except ValueError:
                pass
        if price_to_val:
            try:
                p_to = float(price_to_val)
                conditions.append("d.price <= %s")
                params.append(p_to)
            except ValueError:
                pass

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        query_sql = f"""
            SELECT 
                d.id_dish,
                d.name_dish,
                d.ed_izmer,
                d.price,
                COALESCE(STRING_AGG(i.name_i, ', ' ORDER BY i.name_i), '—')
            FROM Dish d
            LEFT JOIN Recipe r ON d.id_dish = r.id_dish
            LEFT JOIN Ingredient i ON r.id_ingredient = i.id_ingredient
            {where_clause}
            GROUP BY d.id_dish, d.name_dish, d.ed_izmer, d.price
            ORDER BY d.name_dish
        """

        for item in tree.get_children():
            tree.delete(item)

        rows = query(query_sql, tuple(params), fetch=True)
        for row in rows:
            tree.insert("", "end", values=(
                row[0], row[1], row[2], f"{row[3]:.2f}", row[4]
            ))

    def sort_by(tree, col, reverse):
        data = [(tree.set(child, col), child) for child in tree.get_children()]
        try:
            if col == "Цена":
                data.sort(key=lambda t: float(t[0]), reverse=reverse)
            else:
                data.sort(key=lambda t: t[0], reverse=reverse)
        except ValueError:
            data.sort(key=lambda t: t[0], reverse=reverse)
        for idx, (_, child) in enumerate(data):
            tree.move(child, "", idx)
        tree.heading(col, command=lambda: sort_by(tree, col, not reverse))

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Обновить", command=reset_filters, width=10).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Закрыть", command=win.destroy, width=10).pack(side="right", padx=5)

    apply_filters()