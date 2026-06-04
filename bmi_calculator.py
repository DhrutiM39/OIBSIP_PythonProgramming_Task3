import csv
import math
import sqlite3
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import mplcursors
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


DB_PATH = Path(__file__).with_name("bmi_data.db")

COLORS = {
    "app_bg": "#eef6ff",
    "panel": "#ffffff",
    "panel_alt": "#f7fbff",
    "ink": "#172033",
    "muted": "#5c6f82",
    "blue": "#4f86d7",
    "green": "#28a745",
    "amber": "#f0a82f",
    "red": "#e5484d",
    "teal": "#00a6a6",
    "violet": "#7c3aed",
    "line": "#d6e4f0",
}


class BMICalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BMI Calculator")
        self.geometry("980x680")
        self.minsize(820, 560)

        self.last_result = None
        self.selected_record_id = None
        self.graph_cursor = None

        self._configure_style()
        self._initialize_database()
        self._build_ui()
        self.bind("<Return>", lambda _event: self.calculate_bmi())
        self.after(100, self._draw_gauge)

    def _configure_style(self):
        self.configure(background=COLORS["app_bg"])
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("Color.TNotebook", background=COLORS["app_bg"], borderwidth=0)
        style.configure(
            "Color.TNotebook.Tab",
            padding=(18, 10),
            font=("Segoe UI", 10, "bold"),
            background="#dbeafe",
            foreground=COLORS["ink"],
        )
        style.map(
            "Color.TNotebook.Tab",
            background=[("selected", COLORS["violet"])],
            foreground=[("selected", "#ffffff")],
        )
        style.configure("Surface.TFrame", background=COLORS["app_bg"])
        style.configure("Panel.TFrame", background=COLORS["panel"])
        style.configure("Inline.TFrame", background=COLORS["panel"])
        style.configure("Title.TLabel", background=COLORS["app_bg"], foreground=COLORS["ink"], font=("Segoe UI", 22, "bold"))
        style.configure("Subtitle.TLabel", background=COLORS["app_bg"], foreground=COLORS["muted"], font=("Segoe UI", 10))
        style.configure("Field.TLabel", background=COLORS["panel"], foreground=COLORS["ink"], font=("Segoe UI", 10, "bold"))
        style.configure("Toolbar.TLabel", background=COLORS["app_bg"], foreground=COLORS["ink"], font=("Segoe UI", 11, "bold"))
        style.configure("Hint.TLabel", background=COLORS["panel"], foreground=COLORS["muted"], font=("Segoe UI", 9))
        style.configure("Result.TLabel", background=COLORS["panel"], foreground=COLORS["violet"], font=("Segoe UI", 34, "bold"))
        style.configure("Category.TLabel", background=COLORS["panel"], font=("Segoe UI", 18, "bold"))
        style.configure("Color.TEntry", fieldbackground="#f8fbff", bordercolor="#b9d4f0", lightcolor="#b9d4f0", padding=7)
        style.configure("Color.TRadiobutton", background=COLORS["panel"], foreground=COLORS["ink"], font=("Segoe UI", 9, "bold"))
        style.map("Color.TRadiobutton", background=[("active", COLORS["panel"])])
        style.configure(
            "Color.TLabelframe",
            background=COLORS["panel"],
            bordercolor="#b9d4f0",
            relief="solid",
        )
        style.configure(
            "Color.TLabelframe.Label",
            background=COLORS["panel"],
            foreground=COLORS["violet"],
            font=("Segoe UI", 11, "bold"),
        )
        self._configure_button_style(style, "Primary.TButton", COLORS["violet"], "#6d28d9")
        self._configure_button_style(style, "Success.TButton", COLORS["green"], "#20833a")
        self._configure_button_style(style, "Ghost.TButton", COLORS["teal"], "#008c8c")
        self._configure_button_style(style, "Danger.TButton", COLORS["red"], "#c9363b")
        self._configure_button_style(style, "Export.TButton", COLORS["amber"], "#cf8421")
        style.configure(
            "Treeview",
            background="#f8fbff",
            fieldbackground="#f8fbff",
            foreground=COLORS["ink"],
            rowheight=30,
            bordercolor=COLORS["line"],
        )
        style.configure(
            "Treeview.Heading",
            background=COLORS["violet"],
            foreground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map("Treeview", background=[("selected", "#bde6ff")], foreground=[("selected", COLORS["ink"])])

    @staticmethod
    def _configure_button_style(style, name, color, active_color):
        style.configure(
            name,
            background=color,
            foreground="#ffffff",
            bordercolor=color,
            focusthickness=0,
            focuscolor=color,
            padding=(14, 9),
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            name,
            background=[("active", active_color), ("pressed", active_color)],
            foreground=[("disabled", "#e5e7eb"), ("active", "#ffffff")],
        )

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
        notebook = ttk.Notebook(self, style="Color.TNotebook")
        notebook.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)

        self.calculator_tab = ttk.Frame(notebook, padding=20, style="Surface.TFrame")
        self.history_tab = ttk.Frame(notebook, padding=20, style="Surface.TFrame")
        notebook.add(self.calculator_tab, text="Calculator")
        notebook.add(self.history_tab, text="History & Graph")

        self._build_calculator_tab()
        self._build_history_tab()

    def _draw_calculator_header(self, event=None):
        canvas = self.calculator_header
        width = canvas.winfo_width() if event is None else event.width
        height = canvas.winfo_height() if event is None else event.height
        canvas.delete("all")

        stripes = (
            "#7c3aed",
            "#6d5dfc",
            "#3b82f6",
            "#00a6a6",
            "#22c55e",
            "#f0a82f",
        )
        stripe_width = max(1, width // len(stripes))
        for index, color in enumerate(stripes):
            x1 = index * stripe_width
            x2 = width if index == len(stripes) - 1 else (index + 1) * stripe_width
            canvas.create_rectangle(x1, 0, x2, height, fill=color, outline=color)

        canvas.create_polygon(0, height, width * 0.42, 0, width * 0.72, 0, width * 0.28, height, fill="#ffffff", stipple="gray50", outline="")
        canvas.create_polygon(width - 230, 0, width - 42, 0, width - 128, height, width - 316, height, fill="#ffffff", stipple="gray25", outline="")
        canvas.create_polygon(0, 0, 124, 0, 56, height, 0, height, fill="#ffffff", stipple="gray25", outline="")
        canvas.create_text(
            30,
            33,
            text="BMI Wellness Studio",
            anchor="w",
            fill="#ffffff",
            font=("Segoe UI", 25, "bold"),
        )
        canvas.create_text(
            32,
            71,
            text="Calculate, save, visualize, and export health records in one vibrant dashboard.",
            anchor="w",
            fill="#eef6ff",
            font=("Segoe UI", 10, "bold"),
        )
        canvas.create_text(
            width - 34,
            height - 28,
            text="HEALTH TRACKER",
            anchor="e",
            fill="#ffffff",
            font=("Segoe UI", 10, "bold"),
        )

    def _build_calculator_tab(self):
        self.calculator_tab.columnconfigure(0, weight=1)
        self.calculator_tab.columnconfigure(1, weight=1)
        self.calculator_tab.rowconfigure(1, weight=1)

        self.calculator_header = tk.Canvas(
            self.calculator_tab,
            height=116,
            highlightthickness=0,
            background=COLORS["app_bg"],
        )
        self.calculator_header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        self.calculator_header.bind("<Configure>", self._draw_calculator_header)

        form = ttk.LabelFrame(
            self.calculator_tab,
            text="Input Form",
            padding=20,
            style="Color.TLabelframe",
        )
        form.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Name", style="Field.TLabel").grid(row=0, column=0, sticky="w", pady=9)
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var, style="Color.TEntry").grid(
            row=0, column=1, sticky="ew", pady=9
        )

        ttk.Label(form, text="Weight (kg)", style="Field.TLabel").grid(row=1, column=0, sticky="w", pady=9)
        self.weight_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.weight_var, style="Color.TEntry").grid(
            row=1, column=1, sticky="ew", pady=9
        )

        ttk.Label(form, text="Height", style="Field.TLabel").grid(row=2, column=0, sticky="w", pady=9)
        height_row = ttk.Frame(form, style="Inline.TFrame")
        height_row.grid(row=2, column=1, sticky="ew", pady=9)
        height_row.columnconfigure(0, weight=1)

        self.height_var = tk.StringVar()
        ttk.Entry(height_row, textvariable=self.height_var, style="Color.TEntry").grid(
            row=0, column=0, sticky="ew"
        )
        self.height_unit_var = tk.StringVar(value="cm")
        ttk.Radiobutton(
            height_row, text="cm", value="cm", variable=self.height_unit_var, style="Color.TRadiobutton"
        ).grid(row=0, column=1, padx=(10, 0))
        ttk.Radiobutton(
            height_row, text="m", value="m", variable=self.height_unit_var, style="Color.TRadiobutton"
        ).grid(row=0, column=2, padx=(8, 0))

        actions = ttk.Frame(form, style="Inline.TFrame")
        actions.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(22, 0))
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)
        actions.columnconfigure(2, weight=1)

        ttk.Button(
            actions,
            text="Calculate",
            style="Primary.TButton",
            command=self.calculate_bmi,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(
            actions,
            text="Save",
            style="Success.TButton",
            command=self.save_record,
        ).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(
            actions,
            text="Clear",
            style="Ghost.TButton",
            command=self.clear_form,
        ).grid(row=0, column=2, sticky="ew", padx=(6, 0))

        result = ttk.LabelFrame(
            self.calculator_tab,
            text="BMI Result",
            padding=20,
            style="Color.TLabelframe",
        )
        result.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        result.columnconfigure(0, weight=1)

        self.bmi_value_var = tk.StringVar(value="--")
        self.bmi_value_label = ttk.Label(result, textvariable=self.bmi_value_var, style="Result.TLabel")
        self.bmi_value_label.grid(
            row=0, column=0, sticky="w", pady=(2, 18)
        )

        self.category_var = tk.StringVar(value="No result yet")
        self.category_label = ttk.Label(
            result, textvariable=self.category_var, style="Category.TLabel"
        )
        self.category_label.grid(row=1, column=0, sticky="w")

        ttk.Label(
            result,
            text="Categories: Underweight <18.5, Normal 18.5-24.9, Overweight 25-29.9, Obese >=30",
            style="Hint.TLabel",
            wraplength=360,
        ).grid(row=2, column=0, sticky="w", pady=(22, 0))

        self.gauge_canvas = tk.Canvas(
            result,
            height=230,
            background=COLORS["panel"],
            highlightthickness=0,
        )
        self.gauge_canvas.grid(row=3, column=0, sticky="ew", pady=(24, 0))
        self.gauge_canvas.bind("<Configure>", lambda _event: self._draw_gauge())

    def _build_history_tab(self):
        self.history_tab.columnconfigure(0, weight=1)
        self.history_tab.rowconfigure(2, weight=3)
        self.history_tab.rowconfigure(3, weight=4)

        controls = ttk.Frame(self.history_tab, style="Surface.TFrame")
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        controls.columnconfigure(1, weight=1)

        ttk.Label(controls, text="User", style="Toolbar.TLabel").grid(row=0, column=0, sticky="w")
        self.user_filter_var = tk.StringVar()
        self.user_combo = ttk.Combobox(
            controls, textvariable=self.user_filter_var, state="readonly"
        )
        self.user_combo.grid(row=0, column=1, sticky="ew", padx=10)
        self.user_combo.bind("<<ComboboxSelected>>", lambda _event: self.load_history())

        ttk.Button(controls, text="Refresh", style="Ghost.TButton", command=self.refresh_users).grid(
            row=0, column=2, padx=(0, 8)
        )
        ttk.Button(
            controls, text="Delete Record", style="Danger.TButton", command=self.delete_selected_record
        ).grid(row=0, column=3)
        ttk.Button(controls, text="Export CSV", style="Export.TButton", command=self.export_csv).grid(
            row=0, column=4, padx=(8, 0)
        )

        columns = ("id", "name", "weight", "height", "bmi", "category", "date")
        self.history_tree = ttk.Treeview(
            self.history_tab,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        self.history_tree.grid(row=2, column=0, sticky="nsew")
        self.history_tree.bind("<<TreeviewSelect>>", self.on_record_selected)
        self.history_tree.tag_configure("odd", background="#ffffff")
        self.history_tree.tag_configure("even", background="#eef7ff")
        self.history_tree.tag_configure("Underweight", foreground=COLORS["blue"])
        self.history_tree.tag_configure("Normal", foreground=COLORS["green"])
        self.history_tree.tag_configure("Overweight", foreground="#b96b00")
        self.history_tree.tag_configure("Obese", foreground=COLORS["red"])

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

        graph_frame = ttk.LabelFrame(
            self.history_tab,
            text="BMI Trend",
            padding=10,
            style="Color.TLabelframe",
        )
        graph_frame.grid(row=3, column=0, sticky="nsew", pady=(16, 0))
        graph_frame.columnconfigure(0, weight=1)
        graph_frame.rowconfigure(0, weight=1)

        self.figure = Figure(figsize=(7, 3.4), dpi=100, facecolor=COLORS["panel"])
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

        return self._normalize_name(name), weight, height_cm

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
        self.bmi_value_label.configure(foreground=self._category_color(category))
        self._draw_gauge(bmi)
        return self.last_result

    def clear_form(self):
        self.name_var.set("")
        self.weight_var.set("")
        self.height_var.set("")
        self.bmi_value_var.set("--")
        self.category_var.set("No result yet")
        self.category_label.configure(foreground=COLORS["muted"])
        self.bmi_value_label.configure(foreground=COLORS["violet"])
        self.last_result = None
        self._draw_gauge()

    def save_record(self):
        result = self.calculate_bmi()
        if result is None:
            return

        measured_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with sqlite3.connect(DB_PATH) as connection:
                existing_name = connection.execute(
                    "SELECT name FROM bmi_records WHERE LOWER(name) = LOWER(?) ORDER BY id LIMIT 1",
                    (result["name"],),
                ).fetchone()
                saved_name = existing_name[0] if existing_name else result["name"]
                connection.execute(
                    """
                    INSERT INTO bmi_records
                    (name, weight, height_cm, bmi, category, measured_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        saved_name,
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
        self.refresh_users(select_user=saved_name)

    def refresh_users(self, select_user=None):
        try:
            with sqlite3.connect(DB_PATH) as connection:
                rows = connection.execute(
                    """
                    SELECT MIN(name)
                    FROM bmi_records
                    GROUP BY LOWER(name)
                    ORDER BY LOWER(name)
                    """
                ).fetchall()
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", f"Could not load users.\n\n{exc}")
            return

        users = [row[0] for row in rows]
        self.user_combo["values"] = users

        if select_user in users:
            self.user_filter_var.set(select_user)
        elif select_user:
            matching_user = next(
                (user for user in users if user.lower() == select_user.lower()),
                None,
            )
            if matching_user:
                self.user_filter_var.set(matching_user)
            elif users and self.user_filter_var.get() not in users:
                self.user_filter_var.set(users[0])
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
                    WHERE LOWER(name) = LOWER(?)
                    ORDER BY measured_at ASC, id ASC
                    """,
                    (user,),
                ).fetchall()
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", f"Could not load history.\n\n{exc}")
            return

        for index, row in enumerate(rows):
            record_id, name, weight, height_cm, bmi, category, measured_at = row
            self.history_tree.insert(
                "",
                "end",
                iid=str(record_id),
                tags=("even" if index % 2 == 0 else "odd", category),
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

    def export_csv(self):
        records = [
            self.history_tree.item(item_id, "values")
            for item_id in self.history_tree.get_children()
        ]
        if not records:
            messagebox.showwarning("No Records", "There are no visible records to export.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Export BMI History",
            defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
            initialfile="bmi_history.csv",
        )
        if not file_path:
            return

        headers = [
            self.history_tree.heading(column, "text")
            for column in self.history_tree["columns"]
        ]
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(headers)
                writer.writerows(records)
        except OSError as exc:
            messagebox.showerror("Export Error", f"Could not export CSV file.\n\n{exc}")
            return

        messagebox.showinfo("Export Complete", "Visible history records were exported successfully.")

    def _draw_graph(self, rows):
        if self.graph_cursor is not None:
            self.graph_cursor.remove()
            self.graph_cursor = None

        self.ax.clear()
        self.ax.set_facecolor("#f8fbff")
        self.ax.set_ylabel("BMI")
        self.ax.set_xlabel("Date of measurement")
        self.ax.tick_params(colors=COLORS["muted"])
        self.ax.yaxis.label.set_color(COLORS["ink"])
        self.ax.xaxis.label.set_color(COLORS["ink"])
        for spine in self.ax.spines.values():
            spine.set_color(COLORS["line"])
        self.ax.grid(True, linestyle="--", color="#bdd7ee", alpha=0.55)

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
            (line,) = self.ax.plot(
                dates,
                bmi_values,
                marker="o",
                color=COLORS["violet"],
                markerfacecolor=COLORS["amber"],
                markeredgecolor="#ffffff",
                markeredgewidth=1.5,
                linewidth=2.8,
            )
            self.ax.set_title(f"BMI trend for {rows[0][1]}")
            self.figure.autofmt_xdate(rotation=25)
            self.graph_cursor = mplcursors.cursor(line, hover=True)
            self.graph_cursor.connect(
                "add",
                lambda selection: self._set_graph_tooltip(selection, rows),
            )
        else:
            self.ax.set_title("No saved BMI records")
            self.ax.text(
                0.5,
                0.5,
                "Save records to see BMI trends here.",
                ha="center",
                va="center",
                transform=self.ax.transAxes,
                color=COLORS["muted"],
            )

        self.ax.title.set_color(COLORS["ink"])

        self.figure.tight_layout()
        self.canvas.draw_idle()

    def _set_graph_tooltip(self, selection, rows):
        index = int(round(selection.index))
        index = max(0, min(index, len(rows) - 1))
        row = rows[index]
        selection.annotation.set_text(
            f"Date: {row[6]}\nBMI: {row[4]:.2f}\nCategory: {row[5]}"
        )

    def _draw_gauge(self, bmi=None):
        if not hasattr(self, "gauge_canvas"):
            return

        canvas = self.gauge_canvas
        canvas.delete("all")

        width = max(canvas.winfo_width(), 340)
        height = max(canvas.winfo_height(), 220)
        margin = 28
        cx = width / 2
        cy = height - 34
        radius = min((width - margin * 2) / 2, height - 70)
        box = (cx - radius, cy - radius, cx + radius, cy + radius)

        canvas.create_rectangle(0, 0, width, height, fill="#f7fbff", outline="")
        canvas.create_polygon(0, 0, width, 0, width, 48, 0, 98, fill="#edf7ff", outline="")
        canvas.create_polygon(0, height, width, height, width, height - 34, 0, height - 8, fill="#f0f9ff", outline="")

        bands = (
            (10, 18.5, COLORS["blue"], "Under"),
            (18.5, 25, COLORS["green"], "Normal"),
            (25, 30, COLORS["amber"], "Over"),
            (30, 40, COLORS["red"], "Obese"),
        )
        for start_value, end_value, color, _label in bands:
            start_angle = self._bmi_to_angle(start_value)
            end_angle = self._bmi_to_angle(end_value)
            canvas.create_arc(
                box,
                start=end_angle,
                extent=start_angle - end_angle,
                style="arc",
                width=30,
                outline=color,
            )

        for value in (10, 18.5, 25, 30, 40):
            angle = math.radians(self._bmi_to_angle(value))
            inner = radius - 20
            outer = radius + 2
            x1 = cx + math.cos(angle) * inner
            y1 = cy - math.sin(angle) * inner
            x2 = cx + math.cos(angle) * outer
            y2 = cy - math.sin(angle) * outer
            canvas.create_line(x1, y1, x2, y2, fill=COLORS["ink"], width=2)
            label_radius = radius - 46
            lx = cx + math.cos(angle) * label_radius
            ly = cy - math.sin(angle) * label_radius
            canvas.create_text(lx, ly, text=str(value), fill=COLORS["ink"], font=("Segoe UI", 8, "bold"))

        canvas.create_text(
            cx,
            cy - radius - 24,
            text="BMI Gauge",
            fill=COLORS["ink"],
            font=("Segoe UI", 11, "bold"),
        )
        for position, (_start, _end, color, label) in enumerate(bands):
            label_x = 56 + position * 82
            if label_x < width - 22:
                canvas.create_rectangle(label_x - 24, height - 28, label_x + 24, height - 18, fill=color, outline="")
                canvas.create_text(label_x, height - 10, text=label, fill=COLORS["muted"], font=("Segoe UI", 7, "bold"))

        needle_value = 10 if bmi is None else max(10, min(bmi, 40))
        needle_angle = math.radians(self._bmi_to_angle(needle_value))
        needle_length = radius - 42
        nx = cx + math.cos(needle_angle) * needle_length
        ny = cy - math.sin(needle_angle) * needle_length
        needle_color = COLORS["ink"] if bmi is None else self._category_color(self._classify_bmi(bmi))
        canvas.create_line(cx, cy, nx, ny, fill=needle_color, width=5, capstyle="round")
        canvas.create_oval(cx - 11, cy - 11, cx + 11, cy + 11, fill="#ffffff", outline=needle_color, width=4)
        canvas.create_text(
            cx,
            cy + 18,
            text="--" if bmi is None else f"{bmi:.2f}",
            fill=needle_color,
            font=("Segoe UI", 13, "bold"),
        )

    @staticmethod
    def _bmi_to_angle(bmi):
        min_bmi = 10
        max_bmi = 40
        value = max(min_bmi, min(bmi, max_bmi))
        return 180 - ((value - min_bmi) / (max_bmi - min_bmi) * 180)

    @staticmethod
    def _normalize_name(name):
        return " ".join(part.capitalize() for part in name.split())

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
