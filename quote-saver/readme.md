# Quote Saver App  

A simple **Quote Saver App** built with **Flask (Python), HTML, CSS, and JavaScript**.  
It allows users to add, view, and manage quotes with authors.  

---

## 📱 Mobile UI Focus  
- The UI has been designed and styled specifically for **mobile phone screen sizes**.  
- Uses **flexbox layouts**, responsive widths, and simple mobile-friendly design.  
- Buttons and input boxes are optimized for easy touch interaction.  

---

## ✨ Features  
- **Add Quotes**: Enter author name and quote text.  
- **View Quotes**: Saved quotes are displayed in a structured list/table.  
- **Delete Quotes**: Remove unwanted quotes.  
- **Persistent Storage**: Quotes are stored in an **SQLite database** (`quotes.db`).  

---

## 📂 Project Structure
📦 Quote Saver App  
┣ 📜 app.py            # Flask backend  
┣ 📜 quotes.db         # SQLite database for storage  
┣ 📜 templates/  
┃ ┣ 📜 index.html      # Home page  
┃ ┣ 📜 add.html        # Add quotes page  
┃ ┗ 📜 data.html       # View quotes page  
┣ 📜 static/  
┃ ┣ 📜 home.css        # Styles for home page  
┃ ┣ 📜 add.css         # Styles for add quotes page  
┃ ┗ 📜 data.css        # Styles for view quotes page  
┗ 📜 README.md         # Project documentation  

---

## 🚀 How to Run  

1. Clone or download this project.  
2. Install Flask if not already installed:  
   ```bash
   pip install flask
3. Run the Flask app:
   ```bash
   python app.py


4. Open the app in your browser at:
   ```
   http://127.0.0.1:5000/
   ```




---

##🛠️ Technologies Used

- Python (Flask)
- SQLite (Database)
- HTML5
- CSS3 (Flexbox for mobile UI)
- JavaScript (Vanilla JS)



---

##📖 Notes

- Designed primarily for mobile phone usage.
- Can be extended later for tablet or desktop UI.
- Works locally with Flask + SQLite, no internet required.



---

👨‍💻 Author

Developed by Yogesh Jaiswal as a small project for learning and practicing Flask + front-end development.

---
