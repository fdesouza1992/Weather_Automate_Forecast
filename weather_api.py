# Description: A simple weather app that fetches weather data using the OpenWeatherMap API.
# import required modules
import requests
import json
import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv
import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# Load API key from .env file
def configure():
    load_dotenv()

# Fetch weather data from OpenWeatherMap API
def fetch_weather_data(city_name, state_code):
    api_key = os.getenv("API_KEY")
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    query = f"{city_name}, {state_code}, US"
    complete_url = f"{base_url}appid={api_key}&q={query}"

    response = requests.get(complete_url)
    return response.json()

#Function to process weather data and format it for display
def process_weather_data(data):
    if data["cod"] != "404":
        main = data["main"]
        weather_desc = data["weather"][0]["description"].capitalize()
        temp_kelvin = main["temp"]
        temp_celsius = round(temp_kelvin - 273.15, 2)                       # Convert to Celsius
        temp_fahrenheit = round((temp_kelvin - 273.15) * 9/5 + 32, 2)       # Convert to Fahrenheit
        pressure = main["pressure"]
        humidity = main["humidity"]

        return {
            "temp_celsius": temp_celsius,
            "temp_fahrenheit": temp_fahrenheit,
            "pressure": pressure,
            "humidity": humidity,
            "description": weather_desc
        }
    else:
        return None

# Function to update the GUI with weather data
def display_weather(weather_info, city_name, state_code):
    if weather_info:
        # Resize the window to fit content better
        root.geometry("500x550") 
        
        result_box.pack(pady=10)
        # Clear previous text
        result_box.delete("1.0", tk.END)

        #Format city name to uppercase first letter of each word
        formatted_city_name = city_name.title()
        #Format state code to uppercase
        formatted_state_code = state_entry.get().strip().upper()

        # Insert styled text
        result_box.insert(tk.END, f"\nWeather for {formatted_city_name}, {formatted_state_code}:\n\n", "heading")
        result_box.insert(tk.END, f"Temperature: ", "bold")
        result_box.insert(tk.END, f"{weather_info['temp_celsius']}°C / {weather_info['temp_fahrenheit']}°F\n")
        result_box.insert(tk.END, f"Pressure: ", "bold")
        result_box.insert(tk.END, f"{weather_info['pressure']} hPa\n")
        result_box.insert(tk.END, f"Humidity: ", "bold")
        result_box.insert(tk.END, f"{weather_info['humidity']}%\n")
        result_box.insert(tk.END, f"Weather Description: ", "bold")
        result_box.insert(tk.END, f"{weather_info['description']}\n")
    else:
        messagebox.showerror("Error", "City Not Found. Please enter a valid city name.")

# Function trigged by "Get Weather" button
def get_weather():
    city_name = city_entry.get().strip()
    state_code = state_entry.get().strip().upper()

    if not city_name or not state_code:
        messagebox.showerror("Input Error", "Please enter a valid city name and state code.")
        return
        
    try:
        data = fetch_weather_data(city_name, state_code)
        weather_info = process_weather_data(data)
        if weather_info:
            display_weather(weather_info, city_name, state_code)
        else:
            messagebox.showerror("Error", "City Not Found. Please enter a valid city name.")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to retrieve data:\n{e}")

# Function for GUI initialization
def init_gui():
    # Initialize global variables
    global root, state_entry, city_entry, result_box

    # Create a GUI window
    root = tk.Tk()
    root.title("Weather App")
    root.geometry("500x350")
    root.configure(bg="#add8e6")
    root.resizable(False, False)

    # Create a label and entry widget
    city_label = tk.Label(root,
                            text="Enter City Name (e.g. Boston):",
                            anchor=tk.CENTER,
                            font=("helvetica", 22, "bold"),
                            bg="#add8e6")

    city_entry = tk.Entry(root,
                            width=35,
                            font=("helvetica", 14))

    state_label = tk.Label(root,
                            text="Enter State Code (e.g., CA, NY):",
                            anchor=tk.CENTER,
                            font=("helvetica", 22, "bold"),
                            bg="#add8e6")
    state_entry = tk.Entry(root,
                            width=35,
                            font=("helvetica", 14))

    # Create a button to fetch weather data
    get_weather_button = tk.Button(root,
                                    text="Get Weather",
                                    font=("helvetica", 14, "bold"),
                                    bg="#008CBA",
                                    fg="#000000",
                                    padx=10,
                                    pady=5,
                                    relief=tk.RAISED,
                                    command=get_weather)
    
    # Create a text widget to display the result
    result_box = tk.Text(root,
                            font=("helvetica", 14),
                            bg="#add8e6",
                            height=10,
                            width=50,
                            wrap=tk.WORD,
                            relief=tk.FLAT,
                            bd=0)
    result_box.tag_configure("bold",
                            font=("helvetica", 14, "bold"),
                            justify=tk.CENTER)
    result_box.tag_configure("heading",
                            font=("helvetica", 20, "bold"),
                            justify=tk.CENTER)

    # Organize Layout
    city_label.pack(pady=10)
    city_entry.pack(pady=5, ipady=5)
    state_label.pack(pady=10)
    state_entry.pack(pady=5, ipady=5)
    get_weather_button.pack(pady=10, ipadx=10, ipady=5)
    
    return root

# Main() Function Entry Point
def main():
    # Call the configure function
    configure()

    # Initialize GUI
    root = init_gui()
    
    # Run the main loop
    root.mainloop()

# Ensure main() runs only when this script is executed directly
if __name__ == "__main__":
    main()

