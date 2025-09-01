from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
import random

app = Flask(__name__)

# --- default quotes and their authors ---
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
    conn = sqlite3.connect("Quotes.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
                id integer PRIMARY KEY AUTOINCREMENT,
                qoute TEXT NOT NULL,
                author TEXT
            )
    """)
    c.execute("SELECT COUNT(*) FROM quotes")
    total_quotes = c.fetchone()[0]
    for quote, author in zip(default_quotes, default_authors):
        if total_quotes >= len(default_quotes):
            break
        c.execute("INSERT INTO quotes(quote, author) VALUES (?, ?)", (quote, author))
    conn.commit()
    conn.close()
    
init_db()

# --- Routes ---
@app.route("/")
def index():
    conn = sqlite3.connect("Quotes.db")
    c = conn.cursor()

    # Get total number of quotes
    c.execute("SELECT id FROM quotes")
    total_id = c.fetchall()

    # Pick a random id
    random_id = random.choices(total_id)

    # Fetch the quote
    c.execute("SELECT quote, author FROM quotes WHERE id = ?", (random_id,))
    result = c.fetchone()
    conn.close()

    if result:
        quote, author = result
    else:
        quote, author = "No quote found. please add one", "Unknown"

    return render_template("index.html", result=result)
    
@app.route("/show_data")
def show_data():
    conn = sqlite3.connect("Quotes.db")
    c = conn.cursor()
    
    c.execute("SELECT * FROM quotes")
    results = c.fetchall()
    
    conn.close()
    
    return render_template("data.html", results=results)
    
@app.route("/add_data", methods = ["GET", "POST"])
def add_data():
    if request.method == "POST":
        quote = request.form.get("quote", None)
        author = request.form.get("author", None)
        
        if not quote:
            return "<h1>Error 404: !No quote found</h1>"
            
        elif not author:
            return "<h1>Error 404: !No author found</h1>"
            
        conn = sqlite3.connect("Quotes.db")
        c = conn.cursor()
        
        c.execute("INSERT INTO quotes(quote, author) VALUES (?, ?)", (quote, author))
        
        conn.commit()
        conn.close()
        
        return redirect("/")
        
    return render_template("add.html")

@app.route("/delete_data/<int:id>")
def delete_data(id):
    conn = sqlite3.connect("Quotes.db")
    c = conn.cursor()
    
    c.execute("DELETE FROM quotes WHERE id =?", (id, ))
    
    conn.commit()
    conn.close()
    
    return redirect("/show_data")
    
if __name__ == "__main__":
    app.run(debug=True)
