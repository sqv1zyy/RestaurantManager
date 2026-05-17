import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from db import query


def open_all_orders(parent):
    win = tk.Toplevel(parent)
    win.title("Все заказы")
    win.geometry("1920x1080")
    win.transient(parent)
    win.grab_set()

    cols = ("ID", "Стол", "Официант", "Повар", "Содержимое", "Статус", "Сумма", "Создан", "Закрыт")
    tree = ttk.Treeview(win, columns=cols, show="headings")
    for col in cols:
        tree.heading(col, text=col)
        if col == "Официант" or col == "Повар":
            tree.column(col, width=130)
        elif col == "Содержимое":
            tree.column(col, width=250)
        elif col == "Создан" or col == "Закрыт":
            tree.column(col, width=120)
        else:
            tree.column(col, width=80)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    filter_frame = tk.Frame(win)
    filter_frame.pack(fill="x", padx=10, pady=(0, 5))

    tk.Label(filter_frame, text="Фильтр:").pack(side="left", padx=(0, 5))

    tk.Label(filter_frame, text="Блюдо:").pack(side="left", padx=(5, 2))
    dish_filter = tk.Entry(filter_frame, width=12)
    dish_filter.pack(side="left", padx=(0, 10))
    dish_filter.bind("<KeyRelease>", lambda e: apply_filters())

    tk.Label(filter_frame, text="Статус:").pack(side="left", padx=(5, 2))
    status_var = tk.StringVar(value="Все")
    status_combo = ttk.Combobox(
        filter_frame,
        textvariable=status_var,
        values=["Все", "Создан", "В приготовлении", "Готов"],
        state="readonly",
        width=14
    )
    status_combo.pack(side="left", padx=(0, 10))
    status_combo.bind("<<ComboboxSelected>>", lambda e: apply_filters())

    tk.Label(filter_frame, text="Стол №:").pack(side="left", padx=(5, 2))
    table_filter = tk.Entry(filter_frame, width=6)
    table_filter.pack(side="left", padx=(0, 10))
    table_filter.bind("<KeyRelease>", lambda e: apply_filters())

    tk.Label(filter_frame, text="Дата от (ГГГГ-ММ-ДД):").pack(side="left", padx=(5, 2))
    date_from = tk.Entry(filter_frame, width=10)
    date_from.pack(side="left", padx=(0, 5))
    date_from.bind("<KeyRelease>", lambda e: apply_filters())

    tk.Label(filter_frame, text="до:").pack(side="left", padx=(2, 2))
    date_to = tk.Entry(filter_frame, width=10)
    date_to.pack(side="left", padx=(0, 10))
    date_to.bind("<KeyRelease>", lambda e: apply_filters())

    def today_filter():
        today_str = datetime.today().strftime("%Y-%m-%d")
        date_from.delete(0, tk.END)
        date_from.insert(0, today_str)
        date_to.delete(0, tk.END)
        date_to.insert(0, today_str)
        apply_filters()

    tk.Button(filter_frame, text="Сегодня", command=today_filter, width=8).pack(side="left", padx=(0, 10))

    def reset_filters():
        dish_filter.delete(0, tk.END)
        status_var.set("Все")
        table_filter.delete(0, tk.END)
        date_from.delete(0, tk.END)
        date_to.delete(0, tk.END)
        apply_filters()

    tk.Button(filter_frame, text="Сбросить", command=reset_filters, width=8).pack(side="right")

    def apply_filters():
        dish_val = dish_filter.get().strip()
        status_val = status_var.get()
        table_val = table_filter.get().strip()
        date_from_val = date_from.get().strip()
        date_to_val = date_to.get().strip()

        dish_condition = ""
        main_params = []

        conditions = []
        if status_val != "Все":
            conditions.append("o.status = %s")
            main_params.append(status_val)
        if table_val:
            try:
                table_num = int(table_val)
                conditions.append("t.table_number = %s")
                main_params.append(table_num)
            except ValueError:
                pass
        if date_from_val:
            try:
                d_from = datetime.strptime(date_from_val, "%Y-%m-%d").date()
                conditions.append("o.order_created >= %s")
                main_params.append(d_from)
            except ValueError:
                pass
        if date_to_val:
            try:
                d_to = datetime.strptime(date_to_val, "%Y-%m-%d").date()
                end_of_day = datetime(d_to.year, d_to.month, d_to.day, 23, 59, 59)
                conditions.append("o.order_created <= %s")
                main_params.append(end_of_day)
            except ValueError:
                pass

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        if dish_val:
            dish_ids = query("SELECT id_dish FROM Dish WHERE LOWER(name_dish) LIKE LOWER(%s)", (f"%{dish_val}%",), fetch=True)
            if not dish_ids:
                rows = []
            else:
                dish_id_list = [str(row[0]) for row in dish_ids]
                dish_ids_str = ",".join(dish_id_list)
                dish_condition = f"AND o.id_order IN (SELECT DISTINCT id_order FROM Order_item WHERE id_dish IN ({dish_ids_str}))"
        else:
            dish_condition = ""

        if dish_val and not dish_ids:
            rows = []
        else:
            query_sql = f"""
                SELECT 
                    o.id_order,
                    t.table_number,
                    w.ful_name,
                    COALESCE(c.ful_name, '—'),
                    STRING_AGG(d.name_dish || ' x' || oi.amount, ', ' ORDER BY d.name_dish),
                    o.status,
                    o.total_cost,
                    o.order_created,
                    o.close_datetime
                FROM Orderr o
                JOIN TableInfo t ON o.id_table = t.id_table
                JOIN Employee w ON o.id_waiter = w.id_employee
                LEFT JOIN Employee c ON o.id_cook = c.id_employee
                JOIN Order_item oi ON o.id_order = oi.id_order
                JOIN Dish d ON oi.id_dish = d.id_dish
                {where_clause}
                {dish_condition}
                GROUP BY o.id_order, t.table_number, w.ful_name, c.ful_name, o.status, o.total_cost, o.order_created, o.close_datetime
                ORDER BY o.order_created DESC
            """
            rows = query(query_sql, tuple(main_params), fetch=True)

        for item in tree.get_children():
            tree.delete(item)

        for row in rows:
            created = row[7].strftime("%d.%m.%Y %H:%M") if row[7] else ""
            closed = row[8].strftime("%d.%m.%Y %H:%M") if row[8] else "—"
            tree.insert("", "end", values=(
                row[0], row[1], row[2], row[3], row[4], row[5],
                f"{row[6]:.2f}" if row[6] is not None else "0.00",
                created, closed
            ))

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Обновить", command=reset_filters, width=10).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Закрыть", command=win.destroy, width=10).pack(side="right", padx=5)

    apply_filters()