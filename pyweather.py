#!/usr/bin/env python3
import argparse
import datetime
import os
import sys
import requests
from tabulate import tabulate
from wcwidth import wcswidth

def pad_string(s, width):
    """Pad string `s` so it visually aligns to `width` columns in terminal."""
    visual_len = wcswidth(s)
    padding = max(0, width - visual_len)
    return s + " " * padding


def parse_dates(date_str):
    try:
        if ":" in date_str:
            start_str, end_str = date_str.split(":")
            start_date = datetime.datetime.strptime(start_str, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(end_str, "%Y-%m-%d").date()
        else:
            start_date = end_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

        if start_date > end_date:
            raise ValueError("Start date must be before or equal to end date.")
        return start_date, end_date
    except Exception as e:
        print(f"Error parsing date(s): {e}")
        sys.exit(1)

def fetch_weather(nation, city, start_date, end_date, api_key):
    location = f"{city},{nation}"
    url = (
        f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"
        f"{location}/{start_date}/{end_date}?unitGroup=metric&key={api_key}&include=days"
    )
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error fetching weather data: {response.status_code} - {response.text}")
            sys.exit(1)
        return response.json()
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        sys.exit(1)

def get_weather_emoji(condition):
    condition = condition.lower()
    if "clear" in condition or "sun" in condition:
        return "☀️"
    elif "partly" in condition or "cloud" in condition:
        return "⛅"
    elif "rain" in condition:
        return "🌧️"
    elif "snow" in condition:
        return "❄️"
    elif "storm" in condition or "thunder" in condition:
        return "⛈️"
    elif "fog" in condition:
        return "🌫️"
    else:
        return "🌈"

def main():
    parser = argparse.ArgumentParser(
        description="Display weather forecast for a given location and date interval."
    )
    parser.add_argument("-n", "--nation", required=True, help="Nation or country code (e.g., US, UK)")
    parser.add_argument("-c", "--city", required=True, help="City name")
    parser.add_argument(
        "-d", "--date", required=True,
        help="Date or date range. For a single day use YYYY-MM-DD, or for a range use YYYY-MM-DD:YYYY-MM-DD"
    )
    args = parser.parse_args()

    start_date, end_date = parse_dates(args.date)

    api_key = os.environ.get("VISUAL_CROSSING_API_KEY")
    if not api_key:
        print("Please set the VISUAL_CROSSING_API_KEY environment variable with your API key.")
        sys.exit(1)

    data = fetch_weather(args.nation, args.city, start_date, end_date, api_key)

    print(f"\n📍 {args.city.title()} ({args.nation.upper()}) — {start_date} to {end_date}\n")

    days = data.get("days", [])
    if not days:
        print("No weather data available for the specified period.")
        sys.exit(0)

    table = []
    headers = ["Date", "Weather", "🌡️ Max/Min (°C)", "💧 Rain %", "💨 Wind (km/h)"]

    for day in days:
        date = day.get("datetime")
        tempmax = day.get("tempmax", "N/A")
        tempmin = day.get("tempmin", "N/A")
        precip = day.get("precipprob", "N/A")
        wind = day.get("windspeed", "N/A")
        condition = day.get("conditions", "Unknown")
        emoji = get_weather_emoji(condition)

        table.append([
            pad_string(date, 10),
            pad_string(f"{emoji} {condition}", 20),
            pad_string(f"{tempmax}° / {tempmin}°", 15),
            pad_string(f"{precip}%", 8),
            pad_string(f"{wind} km/h", 12)
        ])

    print(tabulate(table, headers=headers, tablefmt="fancy_grid"))

if __name__ == "__main__":
    main()
