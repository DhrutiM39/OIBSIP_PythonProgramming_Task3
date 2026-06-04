# OIBSIP_PythonProgramming_Task3

A colorful graphical BMI Calculator built with Python Tkinter, featuring BMI calculation, category classification, a color-banded BMI gauge, SQLite record storage, user history management, CSV export, delete functionality, and Matplotlib-based BMI trend visualization with hover tooltips.

## Objective

The objective of this project is to build a graphical BMI Calculator application using Python. The application allows users to enter their name, weight, and height, calculate their BMI, view the health category, save records locally, export history, and track BMI history with a graph.

## Steps Performed

1. Created a Tkinter-based graphical user interface with two tabs: Calculator and History & Graph.
2. Added input fields for name, weight, and height with a unit toggle for centimeters or meters.
3. Implemented input validation for empty, non-numeric, and out-of-range values.
4. Added BMI calculation logic and health category classification.
5. Added a colorful dashboard-style UI with styled tabs, panels, buttons, table rows, and header artwork.
6. Added a semicircle BMI gauge with color bands and a moving needle.
7. Used SQLite to store user records locally in `bmi_data.db`.
8. Added a history table to view saved records for a selected user.
9. Added case-insensitive user history lookup so names like `Alice` and `alice` are grouped together.
10. Added delete functionality for removing selected records.
11. Added CSV export for visible history records.
12. Embedded a Matplotlib chart to display BMI trends over time.
13. Added hover tooltips for BMI graph points using `mplcursors`.
14. Added error handling with user-friendly popup messages.
15. Added keyboard support so pressing Enter triggers BMI calculation.

## Tools Used

- Python 3.x
- Tkinter
- tkinter.ttk
- SQLite3
- Matplotlib
- mplcursors

## How to Run

Install Matplotlib and mplcursors if they are not already available:

```bash
python -m pip install matplotlib mplcursors
```

Run the application:

```bash
python bmi_calculator.py
```

## Outcome

The final application is a single runnable Python file, `bmi_calculator.py`, that provides a complete colorful BMI calculator with data storage, history management, CSV export, graph visualization, hover tooltips, a BMI gauge, validation, and error handling.
