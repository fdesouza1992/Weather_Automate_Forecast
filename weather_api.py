# Resources: https://www.geeksforgeeks.org/python-find-current-weather-of-any-city-using-openweathermap-api/
# https://openweathermap.org/current
# https://www.programiz.com/python-programming/json
# https://www.geeksforgeeks.org/python-convert-json-to-dictionary/
# https://www.geeksforgeeks.org/python-convert-dictionary-to-json/

# import required modules
import requests
import json
import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv
import os

# Load API key from .env file
def configure():
    load_dotenv()

# Call the configure function
configure()

# Function to fetch weather data
def get_weather():
    api_key = os.getenv("API_KEY")
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    
    city_name = city_entry.get()
    
    if not city_name.strip():
        messagebox.showwarning("Input Error", "Please enter a city name.")
        return

    complete_url = f"{base_url}appid={api_key}&q={city_name}"
    
    try:
        response = requests.get(complete_url)
        x = response.json()
        
        if x["cod"] != "404":
            y = x["main"]
            temp_kelvin = y["temp"]
            temp_celsius = round(temp_kelvin - 273.15, 2)                       # Convert to Celsius
            temp_fahrenheit = round((temp_kelvin - 273.15) * 9/5 + 32, 2)       # Convert to Fahrenheit
            
            pressure = y["pressure"]
            humidity = y["humidity"]
            weather_desc = x["weather"][0]["description"]

            # Display results in GUI
            result_text.set(f"Temperature: {temp_celsius}°C / {temp_fahrenheit}°F\n"
                            f"Pressure: {pressure} hPa\n"
                            f"Humidity: {humidity}%\n"
                            f"Description: {weather_desc.capitalize()}")
        else:
            messagebox.showerror("Error", "City Not Found. Please enter a valid city name.")

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to retrieve data:\n{e}")

# Create a GUI window
root = tk.Tk()
root.title("Weather App")
root.geometry("500x300")
root.resizable(False, False)

# Create a label and entry widget
city_label = tk.Label(root, text="Enter City Name:")
city_entry = tk.Entry(root, width=30)
city_label.pack(pady=10)
city_entry.pack(pady=10)

# Create a button to fetch weather data
get_weather_button = tk.Button(root, text="Get Weather", command=get_weather)
get_weather_button.pack(pady=10)

# Create a label to display the result
result_text = tk.StringVar()
result_label = tk.Label(root, textvariable=result_text)
result_label.pack(pady=10)

# Run the main loop
root.mainloop()