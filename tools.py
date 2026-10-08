import requests

# Open-Meteo returns weather as a numeric code; this maps it to words
WEATHER_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "fog", 51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain", 71: "light snow",
    73: "snow", 75: "heavy snow", 80: "rain showers", 81: "rain showers",
    82: "violent rain showers", 95: "thunderstorm", 96: "thunderstorm with hail",
    99: "thunderstorm with hail",
}


def get_weather(city: str):
    """Get the current weather for a given city."""
    try:
        # 1. Turn the city name into coordinates
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city.split(",")[0], "count": 1},
            timeout=20,
        ).json()
        if not geo.get("results"):
            return {"error": f"City not found: {city}"}
        place = geo["results"][0]

        # 2. Get the current weather at those coordinates
        w = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,apparent_temperature,"
                           "relative_humidity_2m,wind_speed_10m,weather_code",
            },
            timeout=20,
        ).json()["current"]
    except requests.RequestException as e:
        return {"error": f"Could not get weather for {city}: {e}"}

    temp_c = w["temperature_2m"]
    return {
        "city": f'{place["name"]}, {place.get("country", "")}',
        "condition": WEATHER_CODES.get(w["weather_code"], "unknown"),
        "temperature_c": temp_c,
        "temperature_f": round(temp_c * 9 / 5 + 32, 1),
        "feels_like_c": w["apparent_temperature"],
        "humidity": w["relative_humidity_2m"],
        "wind_speed_kmh": w["wind_speed_10m"],
    }


def reverse_geocode(lat: float, lon: float) -> str:
    """Turn GPS coordinates into 'City, Country' using OpenStreetMap (no key needed)."""
    try:
        data = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json", "accept-language": "en"},
            headers={"User-Agent": "weather-agent-demo"},
            timeout=20,
        ).json()
    except requests.RequestException:
        return ""

    address = data.get("address", {})
    city = (
        address.get("city")
        or address.get("town")
        or address.get("village")
        or address.get("state", "")
    )
    country = address.get("country", "")
    return f"{city}, {country}".strip(", ")