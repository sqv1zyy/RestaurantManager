import tkinter as tk
from tkinter import ttk, messagebox
from db import query, query_with_commit


def open_new_order(parent, current_user):
    win = tk.Toplevel(parent)
    win.title("Новый заказ")
    win.geometry("600x500")

    tk.Label(win, text="Стол:").pack()
    tables = query("SELECT id_table, table_number FROM TableInfo WHERE reserved = FALSE", fetch=True)
    if not tables:
        messagebox.showinfo("Информация", "Нет свободных столов")
        win.destroy()
        return
    table_var = tk.StringVar()
    table_combo = ttk.Combobox(win, textvariable=table_var, state="readonly")
    table_combo['values'] = [f"{t[1]}" for t in tables]
    table_combo.pack()


    waiter_res = query("""
    SELECT e.id_employee
    FROM Employee e
    JOIN Post p ON e.id_pos = p.id_pos
    WHERE p.title = 'Официант' AND e.status = 'Активен'
    LIMIT 1
""", fetch=True)
    if not waiter_res:
        messagebox.showerror("Ошибка", "Нет активных официантов в базе")
        win.destroy()
        return
    
    waiter_id = waiter_res[0][0]

    dishes = query("SELECT id_dish, name_dish, price FROM Dish", fetch=True)
    dish_var = tk.StringVar()
    dish_combo = ttk.Combobox(win, textvariable=dish_var, state="readonly")
    dish_combo['values'] = [f"{d[1]} ({d[2]} руб.)" for d in dishes]
    dish_combo.pack()

    tk.Label(win, text="Количество:").pack()
    amount_spin = tk.Spinbox(win, from_=1, to=10, width=5)
    amount_spin.pack()

    cart = []
    cart_listbox = tk.Listbox(win, height=8)
    cart_listbox.pack(fill="x", pady=5)

    def add_to_cart():
        idx = dish_combo.current()
        if idx == -1:
            messagebox.showwarning("Внимание", "Выберите блюдо")
            return
        dish_id, name, price = dishes[idx]
        qty = int(amount_spin.get())
        cart.append((dish_id, name, qty, price))
        cart_listbox.insert("end", f"{name} x{qty} = {qty * price} руб.")

    tk.Button(win, text="Добавить в заказ", command=add_to_cart).pack()

    def create_order():
        if not table_var.get():
            messagebox.showwarning("Внимание", "Выберите стол")
            return
        if not cart:
            messagebox.showwarning("Внимание", "Добавьте хотя бы одно блюдо")
            return

        table_id = tables[table_combo.current()][0]

        result = query_with_commit("""
        INSERT INTO Orderr (id_table, id_waiter, status, total_cost)
        VALUES (%s, %s, 'Создан', 0) RETURNING id_order
    """, (table_id, waiter_id), fetch=True)
        if not result:
            messagebox.showerror("Ошибка", "Не удалось создать заказ")
            return
        order_id = result[0][0]

        total = 0
        for dish_id, _, qty, price in cart:
            item_cost = qty * price
            query("""
                INSERT INTO Order_item (id_order, id_dish, amount, item_cost)
                VALUES (%s, %s, %s, %s)
            """, (order_id, dish_id, qty, item_cost))
            total += item_cost

        query("UPDATE Orderr SET total_cost = %s WHERE id_order = %s", (total, order_id))
        messagebox.showinfo("Успех", f"Заказ №{order_id} создан!")
        win.destroy()

    tk.Button(win, text="Оформить заказ", command=create_order, bg="green", fg="white").pack(pady=10)