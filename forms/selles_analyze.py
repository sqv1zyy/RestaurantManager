import tkinter as tk
from tkinter import ttk
from db import query


def open_selles_analyze(parent):
    win = tk.Toplevel(parent)
    win.title("Анализ продаж: сезонность и время")
    win.geometry("850x600")
    win.transient(parent)
    win.grab_set()

    tk.Label(win, text="📊 Анализ продаж по времени", font=("Arial", 14, "bold")).pack(pady=(10, 15))

    frame_top = tk.Frame(win)
    frame_top.pack(pady=(0, 15))

    analysis_type = tk.StringVar(value="day_of_week")

    tk.Radiobutton(frame_top, text="По дням недели", variable=analysis_type, value="day_of_week", font=("Arial", 10)).pack(side="left", padx=10)
    tk.Radiobutton(frame_top, text="По времени суток", variable=analysis_type, value="time_of_day", font=("Arial", 10)).pack(side="left", padx=10)
    tk.Radiobutton(frame_top, text="По месяцам", variable=analysis_type, value="month", font=("Arial", 10)).pack(side="left", padx=10)

    cols = ("label", "orders", "revenue")
    tree = ttk.Treeview(win, columns=cols, show="headings", height=20)
    tree.heading("label", text="Период")
    tree.heading("orders", text="Заказов")
    tree.heading("revenue", text="Выручка (₽)")
    tree.column("label", width=200, anchor="w")
    tree.column("orders", width=120, anchor="center")
    tree.column("revenue", width=150, anchor="e")
    tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def fetch_and_display():
        for item in tree.get_children():
            tree.delete(item)

        typ = analysis_type.get()

        if typ == "day_of_week":
            sql = """
                SELECT
                    CASE EXTRACT(DOW FROM close_datetime)::int
                        WHEN 1 THEN 'Понедельник'
                        WHEN 2 THEN 'Вторник'
                        WHEN 3 THEN 'Среда'
                        WHEN 4 THEN 'Четверг'
                        WHEN 5 THEN 'Пятница'
                        WHEN 6 THEN 'Суббота'
                        ELSE 'Воскресенье'
                    END AS period,
                    COUNT(*) AS orders_count,
                    SUM(total_cost) AS total_revenue
                FROM Orderr
                WHERE status = 'Готов' AND close_datetime IS NOT NULL
                GROUP BY EXTRACT(DOW FROM close_datetime)
                ORDER BY EXTRACT(DOW FROM close_datetime)
            """
        elif typ == "time_of_day":
            sql = """
                SELECT
                    CASE
                        WHEN EXTRACT(HOUR FROM close_datetime) BETWEEN 6 AND 11 THEN 'Утро (6–11)'
                        WHEN EXTRACT(HOUR FROM close_datetime) BETWEEN 12 AND 17 THEN 'День (12–17)'
                        WHEN EXTRACT(HOUR FROM close_datetime) BETWEEN 18 AND 22 THEN 'Вечер (18–22)'
                        ELSE 'Ночь (23–5)'
                    END AS period,
                    COUNT(*) AS orders_count,
                    SUM(total_cost) AS total_revenue
                FROM Orderr
                WHERE status = 'Готов' AND close_datetime IS NOT NULL
                GROUP BY period
                ORDER BY
                    MIN(
                        CASE
                            WHEN EXTRACT(HOUR FROM close_datetime) BETWEEN 6 AND 11 THEN 1
                            WHEN EXTRACT(HOUR FROM close_datetime) BETWEEN 12 AND 17 THEN 2
                            WHEN EXTRACT(HOUR FROM close_datetime) BETWEEN 18 AND 22 THEN 3
                            ELSE 4
                        END
                    )
            """
        elif typ == "month":
            sql = """
                SELECT
                    TO_CHAR(close_datetime, 'Month YYYY') AS period,
                    COUNT(*) AS orders_count,
                    SUM(total_cost) AS total_revenue
                FROM Orderr
                WHERE status = 'Готов' AND close_datetime IS NOT NULL
                GROUP BY EXTRACT(YEAR FROM close_datetime), EXTRACT(MONTH FROM close_datetime), period
                ORDER BY EXTRACT(YEAR FROM close_datetime), EXTRACT(MONTH FROM close_datetime)
            """
        else:
            return

        rows = query(sql, fetch=True)

        for row in rows:
            period = row[0]
            orders = row[1]
            revenue = f"{row[2]:,.2f} ₽" if row[2] is not None else "0.00 ₽"
            tree.insert("", "end", values=(period, orders, revenue))

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=(0, 15))

    tk.Button(btn_frame, text="Обновить анализ", command=fetch_and_display, bg="#4CAF50", fg="white", width=15).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Закрыть", command=win.destroy, width=10).pack(side="right", padx=5)

    fetch_and_display()