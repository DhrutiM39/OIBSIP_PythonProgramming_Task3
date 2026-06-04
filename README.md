# OIBSIP_PythonProgramming_Task3

A graphical BMI Calculator built with Python Tkinter, featuring BMI calculation, category classification, SQLite record storage, user history management, delete functionality, and Matplotlib-based BMI trend visualization.

## Objective

The objective of this project is to build a graphical BMI Calculator application using Python. The application allows users to enter their name, weight, and height, calculate their BMI, view the health category, save records locally, and track BMI history with a graph.

## Steps Performed

1. Created a Tkinter-based graphical user interface with two tabs: Calculator and History & Graph.
2. Added input fields for name, weight, and height with a unit toggle for centimeters or meters.
3. Implemented input validation for empty, non-numeric, and out-of-range values.
4. Added BMI calculation logic and health category classification.
5. Used SQLite to store user records locally in `bmi_data.db`.
6. Added a history table to view saved records for a selected user.
7. Added delete functionality for removing selected records.
8. Embedded a Matplotlib chart to display BMI trends over time.
9. Added error handling with user-friendly popup messages.
10. Added keyboard support so pressing Enter triggers BMI calculation.

## Tools Used

- Python 3.x
- Tkinter
- tkinter.ttk
- SQLite3
- Matplotlib

## How to Run

Install Matplotlib if it is not already available:

```bash
python -m pip install matplotlib
```

Run the application:

```bash
python bmi_calculator.py
```

## Outcome

The final application is a single runnable Python file, `bmi_calculator.py`, that provides a complete BMI calculator with data storage, history management, graph visualization, validation, and error handling.
