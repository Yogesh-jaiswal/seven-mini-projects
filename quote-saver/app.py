from flask import Flask, render_template, request, redirect
import sqlite3
import random

app = Flask(__name__)

# --- Default quotes and authors (seed data for first run) ---
default_quotes = [
    "Be the change that you wish to see in the world.",
    "Arise, awake and stop not until the goal is reached.",
    "The weak can never forgive. Forgiveness is the attribute of the strong.",
    "Dream, dream, dream. Dreams transform into thoughts and thoughts result in action.",
    "I don’t believe in taking right decisions. I take decisions and then make them right."
]

default_authors = [
    "Mahatma Gandhi",
    "Swami Vivekananda",
    "Mahatma Gandhi",
    "A. P. J. Abdul Kalam",
    "Ratan Tata"
]

# --- Database setup ---
def init_db():
    """Create database and insert default quotes if empty"""
    conn = sqlite3.connect("quotes.db")
    c = conn.cursor()

    # Create table (if not already exists)
    c.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote TEXT NOT NULL,
            author TEXT
        )
    """)

    # Check how many rows already exist
    c.execute("SELECT COUNT(*) FROM quotes")
    total_quotes = c.fetchone()[0]

    # Insert default quotes only if table is empty
    if total_quotes == 0:
        for quote, author in zip(default_quotes, default_authors):
            c.execute("INSERT INTO quotes(quote, author) VALUES (?, ?)", (quote, author))

    conn.commit()
    conn.close()

def run_query(query, do_fetch_one=False, elements=None, do_commit=False):
    """Helper function to run queries safely"""
    conn = sqlite3.connect("quotes.db")
    c = conn.cursor()

    # Execute query with/without elements
    if elements:
        c.execute(query, elements)
    else:
        c.execute(query)

    # Fetch result if required
    if do_fetch_one:
        results = c.fetchone()
    else:
        results = c.fetchall()

    # Commit changes if needed (for INSERT, UPDATE, DELETE)
    if do_commit:
        conn.commit()

    conn.close()
    return results

# Initialize DB at app start
init_db()

# --- Routes ---

@app.route("/")
def index():
    """Show a random quote on home page"""
    # Get all IDs
    query = "SELECT id FROM quotes"
    total_id = run_query(query)

    if not total_id:  # If DB is empty, show no result
        return render_template("index.html", result=None)

    # Pick random ID from available IDs
    random_id = random.choice(total_id)[0]

    # Fetch that quote + author
    query = "SELECT quote, author FROM quotes WHERE id = ?"
    result = run_query(query, do_fetch_one=True, elements=(random_id,))

    return render_template("index.html", result=result)

@app.route("/show_data")
def show_data():
    """Display all quotes in a table"""
    query = "SELECT * FROM quotes"
    results = run_query(query)

    return render_template("data.html", results=results)

@app.route("/add_data", methods=["GET", "POST"])
def add_data():
    """Form to add a new quote"""
    if request.method == "POST":
        # Get input values from form
        quote = request.form.get("quote", None)
        author = request.form.get("author", None)

        # Validation: Both fields must be filled
        if not quote:
            return "<h1>Error 404: No quote found!</h1>"
        elif not author:
            return "<h1>Error 404: No author found!</h1>"

        # Insert new quote into DB
        query = "INSERT INTO quotes(quote, author) VALUES (?, ?)"
        run_query(query, elements=(quote, author), do_commit=True)

        # Redirect to home page
        return redirect("/")

    # If GET request → Show add.html form
    return render_template("add.html")

@app.route("/delete_data/<int:id>")
def delete_data(id):
    """Delete a quote by its ID"""
    query = "DELETE FROM quotes WHERE id = ?"
    run_query(query, elements=(id,), do_commit=True)

    return redirect("/show_data")

# --- Run the Flask app ---
if __name__ == "__main__":
    app.run(debug=True)
