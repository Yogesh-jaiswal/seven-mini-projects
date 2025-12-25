# 🎥 YouTube Playlist Fetcher  

A simple **YouTube Playlist Fetcher App** built using **Flask (Python)**, **HTML**, **CSS**, and **JavaScript**.  
It allows users to **fetch**, **manage**, and **view playlists and videos** easily.

---

## 📱 Mobile-First UI  
- Interface optimized for **mobile screens**.  
- Uses **flexbox**, responsive layouts, and touch-friendly components.  
- Smooth navigation with clean buttons, icons, and spacing.

---

## ✨ Features  
- 🔗 **Fetch Playlist:** Fetch playlists using a YouTube share link.  
- ♻️ **Refresh Playlist:** Update playlist videos anytime.  
- 🗑️ **Delete Playlist:** Remove a playlist from the list.  
- 🎬 **View Videos:** Open videos in a minimal player page.

---

## 📂 Project Structure
📦 File uploader App  
┣ 📜 app.py            # Flask backend <br>
┣ 📜 youtube.db        # SQLlite DB for metadata <br>
┣ 📜 templates/ <br>
┃ ┣ 📜 base.html       # Base html layout <br>
┃ ┣ 📜 index.html      # Home page <br>
┃ ┣ 📜 playlist.html   # Playlist content page <br>
┃ ┗ 📜 video.html      # Video content page <br>
┃ ┗ 📜 error.html      # Error handler page <br>
┣ 📜 static/ <br>
┃ ┣ 📜 style.css       # Styles for base html <br>
┃ ┣ 📜 index-style.css # Styles for home page <br>
┃ ┣ 📜 playlist-style.css # Styles for playlist content page <br>
┗ 📜 README.md         # Project documentation

---

## 🔌 How to Get a YouTube API Key

1. Open:  
   `https://console.cloud.google.com`
2. Sign in with your Google account.  
3. Create a **new project**.  
4. Open the project.  
5. Search for **YouTube Data API v3**.  
6. Open it → **Enable** it.  
7. Go to **Credentials** → **Create Credentials**.  
8. Choose **API Key** (public data).  
9. Copy your API key.

---

## 🚀 How to Run  

1. Clone or download this project.  
2. Install dependencies:  
   ```bash
   pip install flask
   ```
3. Paste your **Youtube API key** in app.py.
   
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
- CSS3 (Flexbox for mobile UI)
- JavaScript (Vanilla JS)
- Youtube Data API

---

## 📖 Notes

- Designed primarily for mobile phone usage.
- Can be extended later for tablet or desktop UI.
- Works locally with Flask + SQLite, no internet required.

---

## 👨‍💻 Author

Developed by Yogesh Jaiswal as a small project for learning and practicing Flask, front-end development and youtube API integration.

---
