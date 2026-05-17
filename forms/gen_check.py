import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from decimal import Decimal

from reportlab.lib.pagesizes import A5
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


try:
    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
    FONT_NAME = 'Arial'
except:
    try:
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        FONT_NAME = 'DejaVuSans'
    except:

        FONT_NAME = 'Helvetica'


from db import query


def generate_check_pdf(order_id: int, output_dir: str = "checks") -> str:
    order_info = query("""
        SELECT o.order_created, t.table_number, w.ful_name AS waiter_name
        FROM Orderr o
        JOIN TableInfo t ON o.id_table = t.id_table
        JOIN Employee w ON o.id_waiter = w.id_employee
        WHERE o.id_order = %s AND o.status = 'Готов'
    """, (order_id,), fetch=True)

    if not order_info:
        raise ValueError("Заказ не найден или не завершён")

    order_created, table_number, waiter = order_info[0]

    items = query("SELECT * FROM gen_check(%s)", (order_id,), fetch=True)
    if not items:
        raise ValueError("В заказе нет позиций")

    total = sum(row[3] for row in items) 

    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"check_order_{order_id}.pdf")

    doc = SimpleDocTemplate(filename, pagesize=A5, topMargin=0.4*inch, bottomMargin=0.3*inch)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=1,
        spaceAfter=10,
        fontName=FONT_NAME
    )
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10
    )

    story = []
    story.append(Paragraph("РЕСТОРАН «Y123»", title_style))
    story.append(Paragraph("Кассовый чек", normal_style))
    story.append(Spacer(1, 10))

    info_text = f"""
    Столик: №{table_number}<br/>
    Официант: {waiter}<br/>
    Дата и время: {order_created.strftime('%d.%m.%Y %H:%M')}
    """
    story.append(Paragraph(info_text, normal_style))
    story.append(Spacer(1, 12))

    table_data = [["Блюдо", "Кол-во", "Цена", "Сумма"]]
    for dish, qty, price, total_line in items:
        table_data.append([dish, str(qty), f"{price:.2f}", f"{total_line:.2f}"])
    table_data.append(["", "", "ИТОГО:", f"{total:.2f}"])

    table = Table(table_data, colWidths=[2.2*inch, 0.6*inch, 0.8*inch, 0.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(table)

    story.append(Spacer(1, 20))
    story.append(Paragraph("Спасибо за визит!", normal_style))
    story.append(Paragraph("_________________", normal_style))

    doc.build(story)
    return filename


def open_check_view(parent, order_id: int):
    win = tk.Toplevel(parent)
    win.title(f"Чек — заказ №{order_id}")
    win.geometry("600x400")
    win.grab_set()
    tk.Label(win, text=f"Чек по заказу №{order_id}", font=("Arial", 14, "bold")).pack(pady=10)

    cols = ("Блюдо", "Кол-во", "Цена", "Сумма")
    tree = ttk.Treeview(win, columns=cols, show="headings")
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=120 if col == "Блюдо" else 80)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    items = query("SELECT * FROM gen_check(%s)", (order_id,), fetch=True)
    total = Decimal('0')
    for row in items:
        tree.insert("", "end", values=row)
        total += row[3]

    tk.Label(win, text=f"ИТОГО: {total:.2f} руб.", font=("Arial", 12, "bold")).pack(pady=5)

    def save_pdf():
        try:
            pdf_path = generate_check_pdf(order_id)
            messagebox.showinfo("Успех", f"Чек сохранён:\n{pdf_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать PDF:\n{e}")

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Сохранить в PDF", command=save_pdf, width=18).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Закрыть", command=win.destroy, width=10).pack(side="right", padx=5)