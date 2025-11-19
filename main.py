import tkinter as tk
from tkinter import messagebox
from db import query
from forms.top_dishes import open_top_dishes
from forms.dish_cost import open_dish_cost
from forms.salary import open_salary
from forms.photo import open_photo
from forms.report import open_report
from forms.cook_orders import open_cook_orders
from forms.waiter_new_order import open_new_order
from forms.new_dish import open_new_dish
from forms.employee_management import open_employee_management
from forms.reserve_table import open_reserve_table
from forms.shift_assignment import open_shift_assignment
from forms.create_shift import open_create_shift
from forms.cook_ingredients import open_cook_ingredients 
from forms.dish_recipe_view import open_dish_recipe_view
from forms.ingredients_admin import open_ingredients
from forms.all_orders import open_all_orders
from forms.dish_for_waiter import open_menu_view
from forms.selles_analyze import open_selles_analyze
from forms.ingridients_analyze import open_ingridients_analyze

current_user = None


def get_role_by_position(position_title: str) -> str:
    admin_positions = {"Менеджер зала", "Администратор"}
    cook_positions = {"Шеф-повар", "Повар", "Су-шеф", "Помощник повара"}
    if position_title in admin_positions:
        return "admin"
    elif position_title in cook_positions:
        return "cook"
    elif position_title == "Официант":
        return "waiter"
    


def login_window():
    root = tk.Tk()
    root.title("Вход в систему")
    root.geometry("280x160")
    root.resizable(False, False)

    tk.Label(root, text="Логин:").pack(pady=(10, 0))
    login_ent = tk.Entry(root)
    login_ent.pack()

    tk.Label(root, text="Пароль:").pack()
    pass_ent = tk.Entry(root, show="*")
    pass_ent.pack()

    def login():
        global current_user
        login_val = login_ent.get().strip()
        pass_val = pass_ent.get()

        if not login_val or not pass_val:
            messagebox.showwarning("Внимание", "Заполните оба поля")
            return

        user_data = query("""
            SELECT e.id_employee, e.ful_name, e.login, p.title
            FROM Employee e
            JOIN Post p ON e.id_pos = p.id_pos
            WHERE e.login = %s AND e.pass = %s AND e.status = 'Активен'
        """, (login_val, pass_val), fetch=True)

        if user_data:
            emp_id, full_name, login, position_title = user_data[0]
            role = get_role_by_position(position_title)

            current_user = {
                "id": emp_id,
                "login": login,
                "name": full_name,
                "role": role,
                "position": position_title
            }
            root.destroy()
            main_app()
        else:
            messagebox.showerror("Ошибка входа", "Неверный телефон/пароль\nили сотрудник не активен")

    tk.Button(root, text="Войти", command=login, width=15).pack(pady=12)
    root.mainloop()


def main_app():
    global current_user
    role_labels = {
        "admin": "Менеджер",
        "cook": "Повар",
        "waiter": "Официант"
    }
    role_name = role_labels.get(current_user["role"], "Гость")

    root = tk.Tk()
    root.title(f"Ресторан — {role_name}")
    root.geometry("480x480")
    root.resizable(False, False)

    role = current_user["role"]
    buttons = []


    if role in ("cook", "admin"):
        buttons.append(("Заказы на приготовление", lambda: open_cook_orders(root)))
        buttons.append(("Новое блюдо", lambda: open_new_dish(root)))
        buttons.append(("Рецепты", lambda: open_dish_recipe_view(root)))
        

    if role == "admin":
        buttons.append(("Зарплата", lambda: open_salary(root)))
        buttons.append(("Фото сотрудников", lambda: open_photo(root)))
        buttons.append(("Отчёт по столам", lambda: open_report(root)))
        buttons.append(("Себестоимость", lambda: open_dish_cost(root)))
        buttons.append(("Сотрудники", lambda: open_employee_management(root)))
        buttons.append(("Бронирование", lambda: open_reserve_table(root)))
        buttons.append(("Назначение смен", lambda: open_shift_assignment(root)))
        buttons.append(("Создать смену", lambda: open_create_shift(root)))
        buttons.append(("Ингредиенты", lambda: open_ingredients(root)))
        buttons.append(("Заказы", lambda: open_all_orders(root)))
        buttons.append(("Меню", lambda: open_menu_view(root)))
        buttons.append(("Топ блюд", lambda: open_top_dishes(root)))
        buttons.append(("Анализ продаж", lambda: open_selles_analyze(root)))
        buttons.append(("Анализ ингредиентов", lambda: open_ingridients_analyze(root)))

    if role == "waiter":
        buttons.append(("Новый заказ", lambda: open_new_order(root, current_user)))
        buttons.append(("Меню", lambda: open_menu_view(root)))


    if role == 'cook':
        buttons.append(("Ингредиенты", lambda: open_cook_ingredients(root)))
    

    for i, (text, cmd) in enumerate(buttons):
        row = i // 3
        col = i % 3
        tk.Button(
            root, text=text, width=18, height=2, command=cmd
        ).grid(row=row, column=col, padx=8, pady=12, sticky="nsew")

    for col in range(3):
        root.grid_columnconfigure(col, weight=1)

    root.mainloop()


if __name__ == "__main__":
    login_window()