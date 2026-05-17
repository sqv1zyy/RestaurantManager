from tkinter import  ttk, filedialog, messagebox
import tkinter as tk
from PIL import Image, ImageTk
import io
from db import query

def open_photo(parent):
    win = tk.Toplevel(parent)
    win.title("Фото сотрудников")
    win.geometry("400x400")

    emps = query("SELECT id_employee, ful_name FROM Employee WHERE status = 'Активен'", fetch=True)
    if not emps:
        tk.Label(win, text="Нет активных сотрудников").pack()
        return

    emp_dict = {name: eid for eid, name in emps}
    combo = ttk.Combobox(win, values=list(emp_dict.keys()), state="readonly")
    combo.pack(pady=10)

    photo_label = tk.Label(win)
    photo_label.pack()

    current_emp_id = None

    def on_select(e=None):
        nonlocal current_emp_id
        name = combo.get()
        current_emp_id = emp_dict.get(name)
        if not current_emp_id:
            return
        img_data = query("SELECT photo FROM Employee_Photo WHERE id_employee = %s", (current_emp_id,), fetch=True)
        photo_label.config(image="", text="")
        if img_data and img_data[0][0]:
            img = Image.open(io.BytesIO(img_data[0][0]))
            img = img.resize((150, 150))
            photo = ImageTk.PhotoImage(img)
            photo_label.image = photo
            photo_label.config(image=photo)
        else:
            photo_label.config(text="Фото отсутствует")

    combo.bind("<<ComboboxSelected>>", on_select)

    def upload():
        if not current_emp_id:
            return
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png")])
        if not path:
            return
        with open(path, "rb") as f:
            data = f.read()
        query("""
            CREATE TABLE IF NOT EXISTS Employee_Photo (id_employee INT PRIMARY KEY, photo BYTEA);
            INSERT INTO Employee_Photo (id_employee, photo)
            VALUES (%s, %s)
            ON CONFLICT (id_employee) DO UPDATE SET photo = EXCLUDED.photo;
        """, (current_emp_id, data))
        on_select()
        messagebox.showinfo("Успех", "Фото сохранено")

    def delete():
        if current_emp_id:
            query("DELETE FROM Employee_Photo WHERE id_employee = %s", (current_emp_id,))
            photo_label.config(image="", text="Фото удалено")

    tk.Button(win, text="Загрузить фото", command=upload).pack(pady=5)
    tk.Button(win, text="Удалить фото", command=delete).pack(pady=5)