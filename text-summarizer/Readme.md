# 📝 Text Summarizer App

A **mobile-first Text Summarizer application** built using **Flask (Python)**, **HTML**, **CSS**, and **JavaScript**.  
It allows users to **summarize text using an AI model**, then **copy, download, save, and manage summaries**.

---

## 📱 Mobile-First UI
- Designed primarily for **mobile screens**
- Clean, minimal interface
- Touch-friendly buttons and controls
- Smooth user interactions with skeleton loaders and snackbars

---

## ✨ Features
- ✨ **AI Text Summarization** (Hugging Face – T5 model)
- ♻️ **Copy Summary** to clipboard
- 📥 **Download Summary** as a `.txt` file
- 💾 **Save Summary** to library
- 🗑️ **Delete Saved Summaries**
- ⚡ **Caching** to avoid repeated API calls
- ⏳ **Skeleton loader** while summarizing
- 🔢 **Live character counter** with limit validation

---

## 📂 Project Structure
📦 Text summarizer App  
┣ 📜 app.py            # Flask backend <br>
┣ 📜 .env              # Hugging Face API token <br>
┣ 📜 templates/ <br>
┃ ┣ 📜 base.html       # Base html layout <br>
┃ ┣ 📜 index.html      # Home page <br>
┃ ┗ 📜 library.html    # Saved summaries page <br>
┣ 📜 static/ <br>
┃ ┣ 📜 style.css       # Shared styles <br>
┃ ┣ 📜 index-style.css # Home page styles <br>
┃ ┣ 📜 library-style.css # Library page styles <br>
┃ ┣ 📜 utility.js      # Common utility functions <br>
┃ ┣ 📜 index-script.js # Home page logic <br>
┃ ┗ 📜 library-script.js # Library page logic <br>
┣ 📜 instance/ <br>
┃ ┗ 📜 summaries.json  # Stored summaries (JSON) <br>
┣ 📜 .gitignore <br>
┗ 📜 README.md

---

## 🔌 Getting a Hugging Face Token

1. Visit: https://huggingface.co  
2. Log in to your account  
3. Open **Settings → Access Tokens**
4. Click **Create new token**
5. Choose **Write** access
6. Name the token and create it
7. Copy the generated token

---

## 🚀 How to Run the App

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install flask python-dotenv requests
   ```
3. Create a .env file and add:
   ```.env
   HF_TOKEN=your_huggingface_token_here
   ```
4. Run the Flask app:
   ```bash
   python app.py
   ```
5. Open the app in your browser at:
   ```
   http://127.0.0.1:5000/
   ```

---

## 🛠️ Technologies Used

- Python (Flask)
- HTML5
- CSS3 (Flexbox, mobile-first design)
- JavaScript (Vanilla JS)
- Hugging Face Inference API
- JSON (for local storage)

---

## 📖 Notes

- Designed mainly for learning and experimentation
- Uses JSON instead of a database for simplicity
- Summaries are cached to reduce API calls
- Easy to extend with:
  - Authentication
  - Database (SQLite/PostgreSQL)
  - Desktop UI
  - Multiple models

---

## 👨‍💻 Author

Developed by Yogesh Jaiswal as a learning project for Flask, frontend development, and AI integration.

---
