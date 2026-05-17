import tkinter as tk
from tkinter import ttk, messagebox
from db import query

def open_new_dish(parent):
    win = tk.Toplevel(parent)
    win.title("Создать новое блюдо с рецептом")
    win.geometry("700x500")

    tk.Label(win, text="Название блюда:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
    name_var = tk.StringVar()
    tk.Entry(win, textvariable=name_var, width=40).grid(row=0, column=1, padx=10, pady=5)

    tk.Label(win, text="Ед. измерения:").grid(row=1, column=0, sticky="w", padx=10)
    ed_var = tk.StringVar(value="порция")
    ed_combo = ttk.Combobox(win, textvariable=ed_var, values=["порция", "шт", "стакан", "г", "кг", "л"], state="readonly", width=37)
    ed_combo.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(win, text="Наценка:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
    markup_var = tk.StringVar(value="2.50")
    tk.Entry(win, textvariable=markup_var, width=40).grid(row=2, column=1, padx=10, pady=5)

    tk.Label(win, text="Выберите ингредиенты для рецепта:", font=("Arial", 10, "bold")).grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=(15,5))

    ingredients = query("SELECT id_ingredient, name_i, ed_izmer FROM Ingredient ORDER BY name_i", fetch=True)
    if not ingredients:
        messagebox.showerror("Ошибка", "Нет ингредиентов в базе")
        win.destroy()
        return

    ing_list = tk.Listbox(win, selectmode=tk.MULTIPLE, height=8, width=50)
    for ing in ingredients:
        ing_list.insert(tk.END, f"{ing[1]} ({ing[2]})")
    ing_list.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="w")

    tk.Label(win, text="Количество (в единицах измерения ингредиента):").grid(row=5, column=0, sticky="w", padx=10, pady=5)
    amount_var = tk.StringVar(value="0.100")
    tk.Entry(win, textvariable=amount_var, width=15).grid(row=5, column=1, sticky="w", padx=10, pady=5)

    recipe_items = {}  

    def add_ingredient_to_recipe():
        selected = ing_list.curselection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите ингредиент")
            return
        try:
            amount = float(amount_var.get())
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Количество должно быть положительным числом")
            return

        for idx in selected:
            ing_id = ingredients[idx][0]
            ing_name = ingredients[idx][1]
            recipe_items[ing_id] = amount
            messagebox.showinfo("Добавлено", f"Добавлено: {ing_name} — {amount}")
            break 

    tk.Button(win, text="Добавить в рецепт", command=add_ingredient_to_recipe).grid(row=5, column=1, sticky="e", padx=10)

    tk.Label(win, text="Рецепт (ингредиенты):").grid(row=6, column=0, sticky="w", padx=10, pady=5)
    recipe_box = tk.Text(win, height=6, width=60, state="disabled")
    recipe_box.grid(row=7, column=0, columnspan=2, padx=10, pady=5)

    def update_recipe_display():
        recipe_box.config(state="normal")
        recipe_box.delete("1.0", tk.END)
        for ing_id, qty in recipe_items.items():
            name = next(ing[1] for ing in ingredients if ing[0] == ing_id)
            recipe_box.insert(tk.END, f"{name}: {qty}\n")
        recipe_box.config(state="disabled")

    def save_dish():
        name = name_var.get().strip()
        ed = ed_var.get().strip()
        markup_str = markup_var.get().strip()

        if not name:
            messagebox.showerror("Ошибка", "Введите название блюда")
            return
        if not recipe_items:
            messagebox.showerror("Ошибка", "Добавьте хотя бы один ингредиент в рецепт")
            return
        try:
            markup = float(markup_str)
            if markup <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Наценка должна быть > 0")
            return

        try:
            query("""
                INSERT INTO Dish (name_dish, ed_izmer, markup, calk_cost, price)
                VALUES (%s, %s, %s, 0, 0)
            """, (name, ed, markup))

            res = query("SELECT id_dish FROM Dish WHERE name_dish = %s", (name,), fetch=True)
            if not res:
                raise Exception("Не удалось получить ID нового блюда")
            dish_id = res[0][0]

            for ing_id, amount in recipe_items.items():
                query("""
                    INSERT INTO Recipe (id_dish, id_ingredient, amount)
                    VALUES (%s, %s, %s)
                """, (dish_id, ing_id, amount))

            query("SELECT dish_cost(%s)", (dish_id,))

            messagebox.showinfo("Успех", f"Блюдо «{name}» создано с рецептом!")
            win.destroy()

        except Exception as e:
            messagebox.showerror("Ошибка БД", str(e))

    btn_frame = tk.Frame(win)
    btn_frame.grid(row=8, column=0, columnspan=2, pady=15)
    tk.Button(btn_frame, text="Создать блюдо", command=save_dish, bg="green", fg="white", width=20).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Отмена", command=win.destroy, width=15).pack(side="left", padx=5)

    def on_add_click():
        add_ingredient_to_recipe()
        update_recipe_display()
    tk.Button(win, text="Добавить в рецепт", command=on_add_click).grid(row=5, column=1, sticky="e", padx=10)