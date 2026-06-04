import sqlite3
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


DB_PATH = Path(__file__).with_name("bmi_data.db")


class BMICalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BMI Calculator")
        self.geometry("980x680")
        self.minsize(820, 560)

        self.last_result = None
        self.selected_record_id = None

        self._configure_style()
        self._initialize_database()
        self._build_ui()
        self.bind("<Return>", lambda _event: self.calculate_bmi())

    def _configure_style(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")

        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10))
        style.configure("Result.TLabel", font=("Segoe UI", 24, "bold"))
        style.configure("Action.TButton", padding=(14, 8))
        style.configure("Treeview", rowheight=28)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _initialize_database(self):
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS bmi_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        weight REAL NOT NULL,
                        height_cm REAL NOT NULL,
                        bmi REAL NOT NULL,
                        category TEXT NOT NULL,
                        measured_at TEXT NOT NULL
                    )
                    """
                )
        except sqlite3.Error as exc:
            messagebox.showerror(
                "Database Error",
                f"Could not prepare the local database.\n\n{exc}",
            )

    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)

        self.calculator_tab = ttk.Frame(notebook, padding=20)
        self.history_tab = ttk.Frame(notebook, padding=20)
        notebook.add(self.calculator_tab, text="Calculator")
        notebook.add(self.history_tab, text="History & Graph")

        self._build_calculator_tab()
        self._build_history_tab()

    def _build_calculator_tab(self):
        self.calculator_tab.columnconfigure(0, weight=1)
        self.calculator_tab.columnconfigure(1, weight=1)
        self.calculator_tab.rowconfigure(1, weight=1)

        header = ttk.Frame(self.calculator_tab)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="BMI Calculator", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text="Enter your details, calculate BMI, then save the result locally.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        form = ttk.LabelFrame(self.calculator_tab, text="Input Form", padding=18)
        form.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Name").grid(row=0, column=0, sticky="w", pady=8)
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var).grid(
            row=0, column=1, sticky="ew", pady=8
        )

        ttk.Label(form, text="Weight (kg)").grid(row=1, column=0, sticky="w", pady=8)
        self.weight_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.weight_var).grid(
            row=1, column=1, sticky="ew", pady=8
        )

        ttk.Label(form, text="Height").grid(row=2, column=0, sticky="w", pady=8)
        height_row = ttk.Frame(form)
        height_row.grid(row=2, column=1, sticky="ew", pady=8)
        height_row.columnconfigure(0, weight=1)

        self.height_var = tk.StringVar()
        ttk.Entry(height_row, textvariable=self.height_var).grid(
            row=0, column=0, sticky="ew"
        )
        self.height_unit_var = tk.StringVar(value="cm")
        ttk.Radiobutton(
            height_row, text="cm", value="cm", variable=self.height_unit_var
        ).grid(row=0, column=1, padx=(10, 0))
        ttk.Radiobutton(
            height_row, text="m", value="m", variable=self.height_unit_var
        ).grid(row=0, column=2, padx=(8, 0))

        actions = ttk.Frame(form)
        actions.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(18, 0))
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)

        ttk.Button(
            actions,
            text="Calculate",
            style="Action.TButton",
            command=self.calculate_bmi,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(
            actions,
            text="Save",
            style="Action.TButton",
            command=self.save_record,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        result = ttk.LabelFrame(self.calculator_tab, text="BMI Result", padding=18)
        result.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        result.columnconfigure(0, weight=1)

        self.bmi_value_var = tk.StringVar(value="--")
        ttk.Label(result, textvariable=self.bmi_value_var, style="Result.TLabel").grid(
            row=0, column=0, sticky="w", pady=(2, 18)
        )

        self.category_var = tk.StringVar(value="No result yet")
        self.category_label = ttk.Label(
            result, textvariable=self.category_var, font=("Segoe UI", 16, "bold")
        )
        self.category_label.grid(row=1, column=0, sticky="w")

        ttk.Label(
            result,
            text="Categories: Underweight <18.5, Normal 18.5-24.9, Overweight 25-29.9, Obese >=30",
            wraplength=360,
        ).grid(row=2, column=0, sticky="w", pady=(22, 0))

    def _build_history_tab(self):
        self.history_tab.columnconfigure(0, weight=1)
        self.history_tab.rowconfigure(2, weight=3)
        self.history_tab.rowconfigure(3, weight=4)

        controls = ttk.Frame(self.history_tab)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        controls.columnconfigure(1, weight=1)

        ttk.Label(controls, text="User").grid(row=0, column=0, sticky="w")
        self.user_filter_var = tk.StringVar()
        self.user_combo = ttk.Combobox(
            controls, textvariable=self.user_filter_var, state="readonly"
        )
        self.user_combo.grid(row=0, column=1, sticky="ew", padx=10)
        self.user_combo.bind("<<ComboboxSelected>>", lambda _event: self.load_history())

        ttk.Button(controls, text="Refresh", command=self.refresh_users).grid(
            row=0, column=2, padx=(0, 8)
        )
        ttk.Button(
            controls, text="Delete Record", command=self.delete_selected_record
        ).grid(row=0, column=3)

        columns = ("id", "name", "weight", "height", "bmi", "category", "date")
        self.history_tree = ttk.Treeview(
            self.history_tab,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        self.history_tree.grid(row=2, column=0, sticky="nsew")
        self.history_tree.bind("<<TreeviewSelect>>", self.on_record_selected)

        headings = {
            "id": "ID",
            "name": "Name",
            "weight": "Weight kg",
            "height": "Height cm",
            "bmi": "BMI",
            "category": "Category",
            "date": "Date/Time",
        }
        widths = {
            "id": 55,
            "name": 160,
            "weight": 95,
            "height": 95,
            "bmi": 80,
            "category": 120,
            "date": 190,
        }

        for column in columns:
            self.history_tree.heading(column, text=headings[column])
            self.history_tree.column(column, width=widths[column], minwidth=60, anchor="center")

        scrollbar = ttk.Scrollbar(
            self.history_tab, orient="vertical", command=self.history_tree.yview
        )
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        graph_frame = ttk.LabelFrame(self.history_tab, text="BMI Trend", padding=10)
        graph_frame.grid(row=3, column=0, sticky="nsew", pady=(16, 0))
        graph_frame.columnconfigure(0, weight=1)
        graph_frame.rowconfigure(0, weight=1)

        self.figure = Figure(figsize=(7, 3.4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        self.refresh_users()

    def _parse_inputs(self):
        name = self.name_var.get().strip()
        if not name:
            raise ValueError("Please enter a name.")

        try:
            weight = float(self.weight_var.get().strip())
        except ValueError as exc:
            raise ValueError("Weight must be a numeric value.") from exc

        try:
            height = float(self.height_var.get().strip())
        except ValueError as exc:
            raise ValueError("Height must be a numeric value.") from exc

        if not 1 <= weight <= 500:
            raise ValueError("Weight must be between 1 and 500 kg.")

        height_cm = height if self.height_unit_var.get() == "cm" else height * 100
        if not 50 <= height_cm <= 300:
            raise ValueError("Height must be between 50 and 300 cm.")

        return name, weight, height_cm

    def calculate_bmi(self):
        try:
            name, weight, height_cm = self._parse_inputs()
        except ValueError as exc:
            messagebox.showerror("Invalid Input", str(exc))
            return None

        height_m = height_cm / 100
        bmi = round(weight / (height_m * height_m), 2)
        category = self._classify_bmi(bmi)

        self.last_result = {
            "name": name,
            "weight": weight,
            "height_cm": height_cm,
            "bmi": bmi,
            "category": category,
        }
        self.bmi_value_var.set(f"{bmi:.2f}")
        self.category_var.set(category)
        self.category_label.configure(foreground=self._category_color(category))
        return self.last_result

    def save_record(self):
        result = self.calculate_bmi()
        if result is None:
            return

        measured_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.execute(
                    """
                    INSERT INTO bmi_records
                    (name, weight, height_cm, bmi, category, measured_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        result["name"],
                        result["weight"],
                        result["height_cm"],
                        result["bmi"],
                        result["category"],
                        measured_at,
                    ),
                )
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", f"Could not save this record.\n\n{exc}")
            return

        messagebox.showinfo("Saved", "BMI record saved successfully.")
        self.refresh_users(select_user=result["name"])

    def refresh_users(self, select_user=None):
        try:
            with sqlite3.connect(DB_PATH) as connection:
                rows = connection.execute(
                    "SELECT DISTINCT name FROM bmi_records ORDER BY name COLLATE NOCASE"
                ).fetchall()
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", f"Could not load users.\n\n{exc}")
            return

        users = [row[0] for row in rows]
        self.user_combo["values"] = users

        if select_user in users:
            self.user_filter_var.set(select_user)
        elif users and self.user_filter_var.get() not in users:
            self.user_filter_var.set(users[0])
        elif not users:
            self.user_filter_var.set("")

        self.load_history()

    def load_history(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        self.selected_record_id = None

        user = self.user_filter_var.get()
        if not user:
            self._draw_graph([])
            return

        try:
            with sqlite3.connect(DB_PATH) as connection:
                rows = connection.execute(
                    """
                    SELECT id, name, weight, height_cm, bmi, category, measured_at
                    FROM bmi_records
                    WHERE name = ?
                    ORDER BY measured_at ASC, id ASC
                    """,
                    (user,),
                ).fetchall()
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", f"Could not load history.\n\n{exc}")
            return

        for row in rows:
            record_id, name, weight, height_cm, bmi, category, measured_at = row
            self.history_tree.insert(
                "",
                "end",
                iid=str(record_id),
                values=(
                    record_id,
                    name,
                    f"{weight:.2f}",
                    f"{height_cm:.2f}",
                    f"{bmi:.2f}",
                    category,
                    measured_at,
                ),
            )

        self._draw_graph(rows)

    def on_record_selected(self, _event):
        selected = self.history_tree.selection()
        self.selected_record_id = selected[0] if selected else None

    def delete_selected_record(self):
        if not self.selected_record_id:
            messagebox.showwarning("No Selection", "Please select a record to delete.")
            return

        confirm = messagebox.askyesno(
            "Delete Record",
            "Delete the selected BMI record?",
        )
        if not confirm:
            return

        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.execute(
                    "DELETE FROM bmi_records WHERE id = ?",
                    (self.selected_record_id,),
                )
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", f"Could not delete this record.\n\n{exc}")
            return

        self.selected_record_id = None
        self.refresh_users()

    def _draw_graph(self, rows):
        self.ax.clear()
        self.ax.set_ylabel("BMI")
        self.ax.set_xlabel("Date of measurement")
        self.ax.grid(True, linestyle="--", alpha=0.35)

        for boundary, label, color in (
            (18.5, "Underweight", "#5b8def"),
            (25, "Normal", "#2e9d57"),
            (30, "Overweight", "#e0932d"),
        ):
            self.ax.axhline(boundary, color=color, linestyle="--", linewidth=1)
            self.ax.text(
                0.01,
                boundary,
                f" {label} boundary",
                color=color,
                va="bottom",
                transform=self.ax.get_yaxis_transform(),
                fontsize=8,
            )

        if rows:
            dates = [datetime.strptime(row[6], "%Y-%m-%d %H:%M:%S") for row in rows]
            bmi_values = [row[4] for row in rows]
            self.ax.plot(dates, bmi_values, marker="o", color="#1f6f8b", linewidth=2)
            self.ax.set_title(f"BMI trend for {rows[0][1]}")
            self.figure.autofmt_xdate(rotation=25)
        else:
            self.ax.set_title("No saved BMI records")
            self.ax.text(
                0.5,
                0.5,
                "Save records to see BMI trends here.",
                ha="center",
                va="center",
                transform=self.ax.transAxes,
            )

        self.figure.tight_layout()
        self.canvas.draw_idle()

    @staticmethod
    def _classify_bmi(bmi):
        if bmi < 18.5:
            return "Underweight"
        if bmi < 25:
            return "Normal"
        if bmi < 30:
            return "Overweight"
        return "Obese"

    @staticmethod
    def _category_color(category):
        return {
            "Underweight": "#2b6cb0",
            "Normal": "#16803c",
            "Overweight": "#b56a00",
            "Obese": "#c62828",
        }.get(category, "#222222")


if __name__ == "__main__":
    app = BMICalculatorApp()
    app.mainloop()
