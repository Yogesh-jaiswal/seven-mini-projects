# 🌤️ Weather App  

A simple **Weather App** built with **Flask (Python), HTML, CSS, and JavaScript**.  
It fetches live weather data using the **OpenWeatherMap API** and displays it in a mobile-friendly UI.  

---

## 📱 Mobile UI Focus  
- The UI has been designed and styled specifically for **mobile phone screen sizes**.  
- Uses **flexbox layouts**, responsive widths, and clean weather card design.  
- Error messages and animations are mobile-optimized for a better user experience.  

---

## ✨ Features  
- **Search Weather by City**: Enter any city name to fetch its current weather.  
- **Weather Details**: Shows temperature, condition, humidity, and wind speed.  
- **Weather Icons**: Dynamically loads OpenWeatherMap weather icons.  
- **Error Handling**: Displays error messages like *"City not found"* or *"Network Error"*.  
- **Mobile-First Design**: Optimized for touch-friendly interactions.  

---

## 📂 Project Structure
📦 Weather App  
┣ 📜 app.py                # Flask backend  
┣ 📜 requirements.txt       # Dependencies (Flask, requests)  
┣ 📜 static/  
┃ ┣ 📜 style.css            # Stylesheet for the app  
┃ ┗ 📜 script.js            # Frontend JavaScript  
┣ 📜 templates/  
┃ ┗ 📜 index.html           # Main UI template  
┗ 📜 README.md              # Project documentation  

---

## 🚀 How to Run  

1. **Clone or download this project**.  

2. **Install dependencies**:  
   ```bash
   pip install flask requests
   ```
   
3. Get an OpenWeatherMap API key:

- Go to OpenWeatherMap

- Sign up for a free account.

- After logging in, go to the API Keys section.

- Copy your generated API key.

4. Set your API key in app.py:

```python
API_KEY = "YOUR_API_KEY_HERE"
```

5. Run the Flask app:

```bash
python app.py
```

6. Open the app in your browser at:

```
http://127.0.0.1:5000/
```

---

## 🛠️ Technologies Used

- Python (Flask + Requests)

- OpenWeatherMap API

- HTML5

- CSS3 (Flexbox + animations)

- JavaScript (Vanilla JS, Fetch API)

---

## 📖 Notes

- Designed primarily for mobile phone usage.

- Error handling is built-in for invalid cities and network issues.

- Can be extended for desktop responsiveness in the future.

---

## 👨‍💻 Author

Developed by Yogesh Jaiswal as a learning project for Flask + API integration + front-end development.

---
