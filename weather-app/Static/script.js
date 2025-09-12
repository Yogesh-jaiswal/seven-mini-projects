// Grab input and button elements
let searchBox = document.querySelector(".bar");
let searchBtn = document.querySelector(".icon");

// Grab weather output elements
let heading = document.querySelector("#header");
let temperature = document.querySelector("#temperature #value");
let condition = document.querySelector("#condition #value");
let humidity = document.querySelector("#humidity #value");
let wind = document.querySelector("#wind #value");

// HTML template for showing error messages
let error_html = `
    <h1 id="err-heading"></h1>
    <img 
        src="https://cdn-icons-gif.flaticon.com/17102/17102956.gif"
        alt="error-image"
        id="err-img"
    />
    <p id="err-msg"></p>
`;

// Fetch weather data from Flask backend
async function getData(cityName) {
    try {
        let response = await fetch(`/weather/${cityName}`);
        let data = await response.json();
        return data;
    } catch (e) {
        // Fallback in case the server itself is unreachable
        return { error: "Unable to reach server", status: 503 };
    }
}

// Update weather UI when valid data is received
function setData(data) {
    let iconEl = document.querySelector("#weather-icon");

    iconEl.src = `https://openweathermap.org/img/wn/${data["icon"]}@2x.png`;
    document.querySelector("#city-name").innerText = data["city"];
    temperature.innerText = data["temperature"];
    condition.innerText = data["condition"];
    humidity.innerText = data["humidity"];
    wind.innerText = data["wind_speed"];
}

// Handle search button click
searchBtn.addEventListener("click", async () => {
    let result = await getData(searchBox.value);

    // If Flask returned an error (wrong city or server issue)
    if (result.error) {
        let mainContent = document.querySelector("main"); 
        mainContent.innerHTML = error_html;

        // Show fixed "Error 404: page not found" for invalid city names
        document.querySelector("#err-heading").innerText = "Error :" + result.status;
        document.querySelector("#err-msg").innerText = result.error;

        return;
    }

    // Otherwise, show weather data
    setData(result);
});