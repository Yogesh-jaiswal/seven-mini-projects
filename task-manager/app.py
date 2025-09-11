from flask import Flask, render_template, request, redirect
import sqlite3

# Initialize Flask app
app = Flask(__name__)

# --- Database setup ---
def init_db():
    """
    Create the database and tasks table if they don't already exist.
    """
    conn = sqlite3.connect("Task.db")   # Connect to SQLite database (creates file if missing)
    c = conn.cursor()
    
    # Create table for storing tasks
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
                id integer PRIMARY KEY AUTOINCREMENT,  -- Unique ID for each task
                task TEXT NOT NULL,                    -- Task title (required)
                description TEXT,                      -- Optional task description
                due_date date                          -- Optional due date
            )
    """)
    
    conn.commit()   # Save changes
    conn.close()    # Close connection
    
# Call function so DB + table are ready when app starts
init_db()

def run_query(query, elements=None, do_commit=False):
    """
    Utility function to run SQL queries.
    - query: SQL command
    - elements: values for placeholders (optional)
    - do_commit: whether to commit changes (for INSERT/UPDATE/DELETE)
    """
    conn = sqlite3.connect("Task.db")
    c = conn.cursor()
    
    # Execute query with or without parameters
    if elements:
        c.execute(query, elements)
    else:
        c.execute(query)
    
    # If it's a modifying query (INSERT/DELETE/UPDATE), commit and exit
    if do_commit:
        conn.commit()
        conn.close()
        return
  
    # Otherwise, fetch results (SELECT queries)
    results = c.fetchall()
    conn.close()
    
    return results

# --- Routes ---

@app.route("/")
def index():
    """
    Homepage: Show all tasks from database.
    """
    query = "SELECT * FROM tasks"
    results = run_query(query)   # Get all tasks
    
    return render_template("index.html", results=results)  # Send tasks to template
    
@app.route("/add", methods=["GET", "POST"])
def add():
    """
    Add a new task (via form).
    - GET: Show form
    - POST: Insert new task into DB
    """
    if request.method == "POST":
        # Get form data
        task = request.form.get("task", None)
        description = request.form.get("description", None)
        date = request.form.get("date", None)
        
        # Task is required field
        if not task:
            return "<h1>Error 404: !No task found</h1>"
        
        # Insert new task
        query = "INSERT INTO tasks(task, description, due_date) VALUES (?, ?, ?)"
        run_query(query, elements=(task, description, date), do_commit=True)
        
        return redirect("/")   # Redirect back to homepage after adding
        
    # If GET request, show add task form
    return render_template("add.html")

@app.route("/delete/<int:id>")
def delete(id):
    """
    Delete a task by ID.
    """
    query = "DELETE FROM tasks WHERE id = ?"
    run_query(query, elements=(id,), do_commit=True)
    
    return redirect("/")   # Redirect to homepage after deletion
    
# --- Main entry point ---
if __name__ == "__main__":
    app.run(debug=True)   # Run in debug mode (auto reload on code change)
