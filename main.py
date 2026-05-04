from fastapi import FastAPI
from pydantic import BaseModel
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from astral import LocationInfo
from astral.sun import sun
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

app = FastAPI(
    title="Energy Color API",
    version="1.0.0",
    description="Calculates past energy color using a custom 10-planet expanded planetary-hour system."
)

PLANET_ORDER = [
    "Pluto", "Mars", "Venus", "Sun", "Jupiter",
    "Mercury", "Moon", "Uranus", "Neptune", "Saturn"
]

# Python weekday: Monday=0, Tuesday=1, ... Sunday=6
WEEKDAY_START = {
    6: "Sun",
    0: "Moon",
    1: "Mars",
    2: "Mercury",
    3: "Jupiter",
    4: "Venus",
    5: "Saturn",
}

PLANET_TO_COLOR = {
    "Pluto": ("검정", "🌑"),
    "Mars": ("빨강", "🔴"),
    "Venus": ("주황", "🟠"),
    "Sun": ("노랑", "🟡"),
    "Jupiter": ("초록", "🟢"),
    "Mercury": ("파랑", "🔵"),
    "Moon": ("남색", "🔷"),
    "Uranus": ("보라", "🟣"),
    "Neptune": ("흰색", "⚪"),
    "Saturn": ("골드", "🟡✨"),
}

class BirthRequest(BaseModel):
    birth_date: str   # YYYY-MM-DD
    birth_time: str   # HH:mm, 24-hour time
    birth_place: str  # Example: Seoul, South Korea

def get_planet_from_sequence(start_planet: str, offset: int) -> str:
    start_index = PLANET_ORDER.index(start_planet)
    return PLANET_ORDER[(start_index + offset) % len(PLANET_ORDER)]

@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "Energy Color API is running."
    }

@app.post("/calculate-past-energy-color")
def calculate_past_energy_color(req: BirthRequest):
    try:
        geolocator = Nominatim(user_agent="energy_color_api")
        location = geolocator.geocode(req.birth_place, timeout=10)

        if not location:
            return {
                "success": False,
                "error": "LOCATION_NOT_FOUND",
                "message": "Birth place could not be found."
            }

        lat = location.latitude
        lon = location.longitude

        tf = TimezoneFinder()
        timezone_name = tf.timezone_at(lat=lat, lng=lon)

        if not timezone_name:
            return {
                "success": False,
                "error": "TIMEZONE_NOT_FOUND",
                "message": "Timezone could not be determined."
            }

        tz = ZoneInfo(timezone_name)

        birth_date = datetime.strptime(req.birth_date, "%Y-%m-%d").date()
        birth_time = datetime.strptime(req.birth_time, "%H:%M").time()
        birth_dt = datetime.combine(birth_date, birth_time).replace(tzinfo=tz)

        city = LocationInfo(
            name=req.birth_place,
            region="",
            timezone=timezone_name,
            latitude=lat,
            longitude=lon
        )

        today_sun = sun(city.observer, date=birth_date, tzinfo=tz)
        sunrise = today_sun["sunrise"]
        sunset = today_sun["sunset"]

        # Day period: sunrise to sunset
        if sunrise <= birth_dt < sunset:
            period_start = sunrise
            period_end = sunset
            period_type = "day"
            weekday_for_start = birth_date.weekday()

        # Night period after sunset: today's sunset to tomorrow's sunrise
        elif birth_dt >= sunset:
            next_day = birth_date + timedelta(days=1)
            next_sun = sun(city.observer, date=next_day, tzinfo=tz)
            period_start = sunset
            period_end = next_sun["sunrise"]
            period_type = "night"
            weekday_for_start = birth_date.weekday()

        # Night period before sunrise: yesterday's sunset to today's sunrise
        else:
            prev_day = birth_date - timedelta(days=1)
            prev_sun = sun(city.observer, date=prev_day, tzinfo=tz)
            period_start = prev_sun["sunset"]
            period_end = sunrise
            period_type = "night"
            weekday_for_start = prev_day.weekday()

        period_seconds = (period_end - period_start).total_seconds()
        segment_seconds = period_seconds / 12
        elapsed_seconds = (birth_dt - period_start).total_seconds()

        segment_in_period = int(elapsed_seconds // segment_seconds)
        segment_in_period = max(0, min(segment_in_period, 11))

        # 1~12 for day, 13~24 for night
        segment_index = segment_in_period + 1 if period_type == "day" else segment_in_period + 13

        start_planet = WEEKDAY_START[weekday_for_start]
        planet = get_planet_from_sequence(start_planet, segment_in_period)
        color, emoji = PLANET_TO_COLOR[planet]

        return {
            "success": True,
            "color": color,
            "emoji": emoji,
            "planet": planet,
            "internal": {
                "period_type": period_type,
                "segment_index": segment_index,
                "timezone": timezone_name,
                "latitude": lat,
                "longitude": lon
            },
            "internal_note": "Only color and emoji should be shown to the user. Do not reveal planet or calculation details."
        }

    except Exception as e:
        return {
            "success": False,
            "error": "CALCULATION_FAILED",
            "message": str(e)
        }
