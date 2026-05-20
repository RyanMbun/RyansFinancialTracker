# Import Flask tools: Flask runs the web server, the rest handle requests and responses
from flask import Flask, request, jsonify, render_template
# csv lets us read and write .csv files (our simple database)
import csv
# os lets us check if files exist on the computer
import os
# Import the Expense class from the expense.py file we made
from expense import Expense
# datetime lets me get today's date automatically
from datetime import datetime

# Create the Flask app... this is the engine that runs everything
app = Flask(__name__)

# The name of the file where all expenses are saved
FILE = "expenses.csv"
# The list of categories users can pick from
CATEGORIES = ["🍔 Food", "🏡 Home", "🏢 Work", "🎉 Fun", "📃 Misc"]
# The default monthly budget, later ill make it so this can be changed by the user in the Settings tab
BUDGET = 2000.0



# Opens the CSV file and returns all expenses as a list of dictionaries
def read_expenses():
    # Start with an empty list
    expenses = []
    # If the file doesn't exist yet, return the empty list (nothing saved yet)
    if not os.path.exists(FILE):
        return expenses
    # Open the file in read mode
    with open(FILE, "r") as f:
        # DictReader turns each row into a dictionary like {"name": "Coffee", "amount": "4.50", ...}
        reader = csv.DictReader(f)
        # Loop through every row and add it to our list
        for row in reader:
            expenses.append(row)
    # Return the full list of expenses
    return expenses


# Saves a single expense to the CSV file
def write_expense(expense, date):
    # Check if the file already exists before opening it
    file_exists = os.path.exists(FILE)
    # Open the file in append mode ("a") so we add to it instead of overwriting
    with open(FILE, "a", newline="") as f:
        # DictWriter lets us write dictionaries as rows, with these column names
        writer = csv.DictWriter(f, fieldnames=["name", "category", "amount", "date"])
        # If the file is brand new, write the header row first (name, category, amount, date)
        if not file_exists:
            writer.writeheader()
        # Write the expense as a new row in the file
        writer.writerow({
            "name": expense.name,
            "category": expense.category,
            "amount": expense.amount,
            "date": date
        })


# Removes one expense from the file by its position number (index)
def delete_expense_by_index(index):
    # Load all expenses into memory
    expenses = read_expenses()
    # Make sure the index is valid (not out of bounds)
    if 0 <= index < len(expenses):
        # Remove the expense at that position
        expenses.pop(index)
        # Rewrite the entire file with the expense removed
        with open(FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "category", "amount", "date"])
            # Write the header row
            writer.writeheader()
            # Write all remaining expenses back to the file
            writer.writerows(expenses)
        # Return True to signal it worked
        return True
    # Return False if the index was invalid
    return False


# Routes are URLs the browser can visit. Each one runs a function.

# When the user visits the homepage (http://127.0.0.1:5000), send them the HTML page
@app.route("/")
def index():
    # render_template finds index.html inside the templates/ folder and sends it
    return render_template("index.html", categories=CATEGORIES)


# When the frontend asks for all expenses (GET request), return them as JSON
@app.route("/api/expenses", methods=["GET"])
def get_expenses():
    # jsonify converts our Python list into JSON that the browser can read
    return jsonify(read_expenses())


# When the frontend submits a new expense (POST request), save it
@app.route("/api/expenses", methods=["POST"])
def add_expense():
    # request.json grabs the data sent from the browser
    data = request.json
    # Create an Expense object using the data sent from the form
    exp = Expense(data["name"], data["category"], float(data["amount"]))
    # Use the date the user picked, or fall back to today's date if none was sent
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    # Save the expense to the CSV file
    write_expense(exp, date)
    # Send back a success message
    return jsonify({"status": "ok"})


# When the frontend wants to delete an expense, this route handles it
# <int:index> means Flask pulls the number out of the URL automatically
@app.route("/api/expenses/<int:index>", methods=["DELETE"])
def delete_expense(index):
    # Try to delete it and store whether it worked
    success = delete_expense_by_index(index)
    # Send back "ok" if it worked, "error" if not
    return jsonify({"status": "ok" if success else "error"})


# When the Summary tab loads, this calculates totals and sends them back
@app.route("/api/summary", methods=["GET"])
def get_summary():
    # Load all expenses
    expenses = read_expenses()
    # Add up all the amounts to get the total spent
    total = sum(float(e["amount"]) for e in expenses)
    # Build a dictionary of spending per category
    by_category = {}
    for e in expenses:
        # Get the category name for this expense
        cat = e["category"]
        # Add this expense's amount to that category's running total
        # .get(cat, 0) returns 0 if the category hasn't been seen yet
        by_category[cat] = by_category.get(cat, 0) + float(e["amount"])
    # Send back all the summary data as JSON
    return jsonify({
        "total": total,
        "budget": BUDGET,
        # How much money the user has left this month
        "remaining": BUDGET - total,
        "by_category": by_category
    })


# When the user saves a new budget in Settings, this updates it
@app.route("/api/budget", methods=["POST"])
def set_budget():
    # global means we're updating the BUDGET variable defined at the top of the file
    global BUDGET
    # Read the new budget value sent from the browser and save it
    BUDGET = float(request.json["budget"])
    # Send back confirmation with the new budget
    return jsonify({"status": "ok", "budget": BUDGET})


# Only start the server if we run this file directly (not if it's imported)
if __name__ == "__main__":
    # debug=True means Flask auto-reloads when you save changes
    app.run(debug=True)
