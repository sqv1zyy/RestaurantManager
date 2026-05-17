import tkinter as tk
from tkinter import ttk, messagebox
from db import query


def open_dish_recipe_view(parent):
    win = tk.Toplevel(parent)
    win.title("Меню и рецепты")
    win.geometry("900x550")
    win.transient(parent)
    win.grab_set()

    left_frame = tk.Frame(win)
    left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    tk.Label(left_frame, text="Блюда", font=("Arial", 12, "bold")).pack(pady=(0, 5))

    dish_cols = ("ID", "Название", "Цена", "Себестоимость")
    dish_tree = ttk.Treeview(left_frame, columns=dish_cols, show="headings", height=15)
    for col in dish_cols:
        dish_tree.heading(col, text=col)
        dish_tree.column(col, width=90 if col == "Название" else 70)
    dish_tree.pack(fill="both", expand=True)

    right_frame = tk.Frame(win)
    right_frame.pack(side="right", fill="both", expand=True, padx=(0, 10), pady=10)

    recipe_label = tk.Label(right_frame, text="Состав блюда", font=("Arial", 12, "bold"))
    recipe_label.pack(pady=(0, 5))

    recipe_cols = ("Ингредиент", "Кол-во", "Ед.изм.", "Склад", "Годен")
    recipe_tree = ttk.Treeview(right_frame, columns=recipe_cols, show="headings", height=15)
    for col in recipe_cols:
        recipe_tree.heading(col, text=col)
        recipe_tree.column(col, width=100 if col == "Ингредиент" else 60)
    recipe_tree.pack(fill="both", expand=True)

    def load_dishes():
        for item in dish_tree.get_children():
            dish_tree.delete(item)
        dishes = query("""
            SELECT id_dish, name_dish, price, calk_cost
            FROM Dish
            ORDER BY name_dish
        """, fetch=True)
        for row in dishes:
            dish_tree.insert("", "end", values=row)

    def on_dish_select(event):
        sel = dish_tree.selection()
        if not sel:
            return

        dish_id = int(dish_tree.item(sel[0])["values"][0])
        dish_name = dish_tree.item(sel[0])["values"][1]
        recipe_label.config(text=f"Состав: {dish_name}")


        for item in recipe_tree.get_children():
            recipe_tree.delete(item)

        ingredients = query("""
            SELECT i.name_i, r.amount, i.ed_izmer, i.amount AS stock, i.expiration_date
            FROM Recipe r
            JOIN Ingredient i ON r.id_ingredient = i.id_ingredient
            WHERE r.id_dish = %s
            ORDER BY i.name_i
        """, (dish_id,), fetch=True)

        if not ingredients:
            recipe_tree.insert("", "end", values=("— Рецепт пуст —", "", "", "", ""))
        else:
            for name, amount, unit, stock, exp in ingredients:
                exp_str = exp.strftime("%d.%m.%Y") if exp else "—"
                recipe_tree.insert("", "end", values=(name, f"{amount:.3f}", unit, f"{stock:.3f}", exp_str))

    dish_tree.bind("<<TreeviewSelect>>", on_dish_select)

    btn_frame = tk.Frame(left_frame)
    btn_frame.pack(pady=10, fill="x")
    tk.Button(btn_frame, text="Обновить", command=load_dishes, width=12).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Закрыть", command=win.destroy, width=12).pack(side="right", padx=5)

    load_dishes()