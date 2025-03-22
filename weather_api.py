# Description: A simple weather app that fetches weather data using the OpenWeatherMap API.
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
    
    city_name = city_entry.get().strip()
    
    if not city_name:
        messagebox.showerror("Input Error", "Please enter a valid city name.")
        return

    complete_url = f"{base_url}appid={api_key}&q={city_name}"
    
    try:
        response = requests.get(complete_url)
        x = response.json()
        
        if x["cod"] != "404":
            result_box.pack(pady=10)
            y = x["main"]
            temp_kelvin = y["temp"]
            temp_celsius = round(temp_kelvin - 273.15, 2)                       # Convert to Celsius
            temp_fahrenheit = round((temp_kelvin - 273.15) * 9/5 + 32, 2)       # Convert to Fahrenheit
            
            pressure = y["pressure"]
            humidity = y["humidity"]
            weather_desc = x["weather"][0]["description"].capitalize()

            #Clear previous text
            result_box.delete("1.0", tk.END)

            #Insert styled text
            result_box.insert(tk.END, f"Temperature: ", "bold")
            result_box.insert(tk.END, f"{temp_celsius}°C / {temp_fahrenheit}°F\n")
            result_box.insert(tk.END, f"Pressure: ", "bold")
            result_box.insert(tk.END, f"{pressure} hPa\n")
            result_box.insert(tk.END, f"Humidity: ", "bold")
            result_box.insert(tk.END, f"{humidity}%\n")
            result_box.insert(tk.END, f"Weather Description: ", "bold")
            result_box.insert(tk.END, f"{weather_desc}\n")
        else:
            messagebox.showerror("Error", "City Not Found. Please enter a valid city name.")

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to retrieve data:\n{e}")

# Create a GUI window
root = tk.Tk()
root.title("Weather App")
root.geometry("500x350")
root.configure(bg="#add8e6")
root.resizable(False, False)

# Create a label and entry widget
city_label = tk.Label(root, 
                      text="Enter City Name:",
                      anchor=tk.CENTER,
                      font=("Helvetica", 22, "bold"),
                      bg="#add8e6")
city_entry = tk.Entry(root, 
                      width=35,
                      font=("Helvetica", 14))

# Create a button to fetch weather data
get_weather_button = tk.Button(root, 
                               text="Get Weather", 
                               font=("Helvetica", 14, "bold"),
                               bg="#008CBA",
                               fg="#000000",
                               padx=10,
                               pady=5,
                               relief=tk.RAISED,
                               command=get_weather)

#Create a text widhet to display the result
result_box = tk.Text(root, 
                     font=("Helvetica", 14),
                     bg="#add8e6",
                     height=10, 
                     width=50,
                     wrap=tk.WORD,
                     relief=tk.FLAT,
                     bd=0)
result_box.tag_configure("bold", 
                         font=("Helvetica", 14, "bold"),
                         justify=tk.CENTER)

# Organize Layout
city_label.pack(pady=10)
city_entry.pack(pady=5, ipady=5)
get_weather_button.pack(pady=10, ipadx=10, ipady=5)

# Run the main loop
root.mainloop()