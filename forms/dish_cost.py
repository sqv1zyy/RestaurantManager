import tkinter as tk
from tkinter import ttk, messagebox
from db import query


def open_dish_cost(parent):
    win = tk.Toplevel(parent)
    win.title("Себестоимость блюда")
    win.geometry("500x250")
    win.resizable(False, False)

    tk.Label(win, text="Выберите блюдо:", font=("Arial", 10)).pack(pady=(15, 5))

    dishes = query("SELECT id_dish, name_dish FROM Dish ORDER BY name_dish", fetch=True)
    
    if not dishes:
        messagebox.showwarning("Внимание", "В базе нет блюд!")
        win.destroy()
        return

    dish_names = [name for _, name in dishes]
    dish_id_by_name = {name: did for did, name in dishes}

    combo = ttk.Combobox(win, values=dish_names, state="readonly", width=40)
    combo.pack(pady=5)
    combo.set("— Выберите блюдо —")

    result_label = tk.Label(win, text="", font=("Arial", 9), fg="blue", wraplength=380, justify="left")
    result_label.pack(pady=(10, 0))

    def calc():
        selected = combo.get()
        if selected == "— Выберите блюдо —" or selected not in dish_id_by_name:
            messagebox.showwarning("Внимание", "Пожалуйста, выберите блюдо из списка")
            return

        did = dish_id_by_name[selected]

        try:
            query("SELECT dish_cost(%s)", (did,))

            res = query(
                "SELECT name_dish, calk_cost, price, markup FROM Dish WHERE id_dish = %s",
                (did,),
                fetch=True
            )
            if res:
                name, cost, price, markup = res[0]
                msg = (
                    f"Блюдо: {name}\n"
                    f"Себестоимость: {cost:.2f} ₽\n"
                    f"Наценка: {markup:.2f} ({markup * 100:.0f}%)\n"
                    f"Цена: {price:.2f} ₽"
                )
                result_label.config(text=msg)
            else:
                result_label.config(text="Ошибка: данные не найдены")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось рассчитать себестоимость:\n{str(e)}")

    tk.Button(win, text="Показать себестоимость", command=calc, width=25).pack(pady=15)