import tkinter as tk
from tkinter import ttk, messagebox
from db import query
from forms.gen_check import open_check_view 


def open_cook_orders(parent):
    win = tk.Toplevel(parent)
    win.title("Заказы для приготовления")
    win.geometry("950x500")

    cols = ("ID заказа", "Стол", "Блюдо", "Кол-во", "Стоимость", "Статус", "Дата")
    tree = ttk.Treeview(win, columns=cols, show="headings")
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=110)
    tree.column("Блюдо", width=220)
    tree.column("Дата", width=140)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    def load_orders():
        for item in tree.get_children():
            tree.delete(item)
        orders = query("""
            SELECT 
                o.id_order,
                t.table_number,
                d.name_dish,
                oi.amount,
                o.total_cost,
                o.status,
                o.order_created
            FROM Orderr o
            JOIN TableInfo t ON o.id_table = t.id_table
            JOIN Order_item oi ON o.id_order = oi.id_order
            JOIN Dish d ON oi.id_dish = d.id_dish
            WHERE o.status IN ('Создан', 'В приготовлении')
            ORDER BY o.order_created, o.id_order, d.name_dish
        """, fetch=True)
        if orders:
            for row in orders:
                dt_str = row[6].strftime("%d.%m.%Y %H:%M") if row[6] else ""
                cost_str = f"{row[4]:.2f}" if row[4] is not None else "0.00"
                tree.insert("", "end", values=(
                    row[0], row[1], row[2], row[3], cost_str, row[5], dt_str
                ))

    load_orders()

    def start_cooking():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите заказ")
            return
        order_id = tree.item(sel[0])["values"][0]
        status = tree.item(sel[0])["values"][5]  

        if status == "Создан":
            cook_res = query("""
                SELECT id_employee 
                FROM Employee e 
                JOIN Post p ON e.id_pos = p.id_pos 
                WHERE p.title IN ('Повар', 'Помощник повара', 'Су-шеф', 'Шеф-повар')
                AND e.status = 'Активен' 
                LIMIT 1
            """, fetch=True)
            if not cook_res:
                messagebox.showerror("Ошибка", "Нет активных поваров")
                return
            cook_id = cook_res[0][0]

            query("""
                UPDATE Orderr 
                SET status = 'В приготовлении', id_cook = %s
                WHERE id_order = %s
            """, (cook_id, order_id))
            messagebox.showinfo("Успех", "Приготовление начато!")
            load_orders()
        else:
            messagebox.showinfo("Информация", "Заказ уже в приготовлении")

    def finish_cooking():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите заказ")
            return
        order_id = tree.item(sel[0])["values"][0]
        status = tree.item(sel[0])["values"][5] 

        if status == "В приготовлении":
            try:
                query("UPDATE Orderr SET status = 'Готов' WHERE id_order = %s", (order_id,))
                messagebox.showinfo("Успех", "Заказ завершён!")
                load_orders()
                open_check_view(parent, order_id)
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
        else:
            messagebox.showinfo("Информация", "Можно завершать только заказы 'В приготовлении'")

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Начать приготовление", command=start_cooking, width=20).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Завершить приготовление", command=finish_cooking, width=20).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Обновить", command=load_orders, width=12).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Закрыть", command=win.destroy, width=12).pack(side="right", padx=5)