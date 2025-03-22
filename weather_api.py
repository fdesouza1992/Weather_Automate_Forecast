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
            save_weather_image(city_name, 
                               temp_celsius, 
                               temp_fahrenheit, 
                               pressure, 
                               humidity, 
                               weather_desc)
        else:
            messagebox.showerror("Error", "City Not Found. Please enter a valid city name.")

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to retrieve data:\n{e}")

# Function to save weather data as an image
def save_weather_image(city, temp_c, temp_f, pressure, humidity, description):
    # Image size & background
    width, height = 600, 350
    img = Image.new('RGB', (width, height), color='#add8e6')
    draw = ImageDraw.Draw(img)

    # Load fonts
    try:
        font_title = ImageFont.truetype("Helvetica", 28)
        font_bold = ImageFont.truetype("Helvetica", 22)
        font_regular = ImageFont.truetype("Helvetica", 22)
    except IOError:
        font_title = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        font_regular = ImageFont.load_default()

    # Title
    title = f"Weather for {city}"
    title_width = draw.textlength(title, font=font_title)
    draw.text(((width - title_width) / 2, 30), title, fill="black", font=font_title)

    # Data lines with bold label + regular value
    y_start = 100
    spacing = 40

    def draw_label_value(label, value, y):
        label_width = draw.textlength(label, font=font_bold)
        value_width = draw.textlength(value, font=font_regular)
        total_width = label_width + value_width
        x_start = (width - total_width) / 2

        draw.text((x_start, y), label, fill="black", font=font_bold)
        draw.text((x_start + label_width, y), value, fill="black", font=font_regular)

    draw_label_value("Temperature: ", f"{temp_c}°C / {temp_f}°F", y_start)
    draw_label_value("Pressure: ", f"{pressure} hPa", y_start + spacing)
    draw_label_value("Humidity: ", f"{humidity}%", y_start + spacing * 2)
    draw_label_value("Description: ", description, y_start + spacing * 3)

    # Save image
    filename = f"weather_{city}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(filename)
    print(f"Weather image saved as: {filename}")

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