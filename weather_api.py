# Description: An enhanced weather app that fetches and exports weather data
import requests
import json
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from dotenv import load_dotenv
import os
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageTk
from datetime import datetime, date, timezone, timedelta
from settings import (
    IMAGE_WIDTH, IMAGE_HEIGHT, BACKGROUND_COLOR, FONTS, 
    LINE_SPACING, TEXT_COLOR, BUTTON_COLOR, EXPORT_FORMATS,
    TEMPLATES, TEMPLATE_PATHS, DEFAULT_FONT, TEXT_COLOR_DARK,
    BUTTON_STYLE
)
from io import BytesIO
import urllib.request

# Global variables
current_weather_data = []  # Now stores multiple locations
location_entries = []
input_elements = []
root = None
main_frame = None
result_frame = None
preview_frame = None
preview_canvas = None
preview_label = None
header_frame = None
description_label = None
button_frame = None

# Loads environment variables and verifies required template images exist
def configure():
    load_dotenv()
    
    # Verify API key exists
    if not os.getenv("API_KEY"):
        messagebox.showerror("Configuration Error", "OpenWeatherMap API key not found in .env file")
        return False
    
    # Verify template images exist
    for template_name, path in TEMPLATE_PATHS.items():
        if not os.path.exists(path):
            messagebox.showwarning("Template Missing", 
                                 f"{template_name} template image not found: {path}")
     
    return True

# Fetch weather data from OpenWeatherMap API with robust error handling
def fetch_weather_data(city_name, state_code, country_code="US"):
    api_key = os.getenv("API_KEY")
    if not api_key:
        messagebox.showerror("API Error", "OpenWeatherMap API key not configured")
        return None
    
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    query = f"{city_name},{state_code},{country_code}"
    complete_url = f"{base_url}appid={api_key}&q={query}&units=metric"
    
    try:
        response = requests.get(complete_url, timeout=15)
        
        if response.status_code == 401:
            return None, "Invalid API key - please check your configuration"
        elif response.status_code == 404:
            return None, f"We couldn't find: {city_name}, {state_code}"
        elif response.status_code == 429:
            return None, "API rate limit exceeded - try again later"
        elif response.status_code != 200:
            return None, f"API error (Code: {response.status_code})"
        
        data = response.json()
        
        if not data or 'cod' not in data:
            return None, "Invalid API response format"
            
        if data['cod'] != 200:
            return None, data.get('message', 'Unknown API error')
            
        return data, None
        
    except requests.exceptions.Timeout:
        return None, "Request timed out - server took too long to respond"
    except requests.exceptions.ConnectionError:
        return None, "Network connection failed - check your internet"
    except json.JSONDecodeError:
        return None, "Invalid response format - could not decode JSON"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

# Process the raw API data into a more usable format
def process_weather_data(data):
    if data.get("cod") != 200:
        return None
        
    main = data["main"]
    weather = data["weather"][0]
    wind = data.get("wind", {})
    sys = data.get("sys", {})
    tz_offset = data.get("timezone", 0)  # in seconds
    
    # Convert timestamps to local time
    sunrise_utc = datetime.fromtimestamp(sys["sunrise"], timezone.utc)
    sunset_utc = datetime.fromtimestamp(sys["sunset"], timezone.utc)
    
    # Apply timezone offset
    sunrise_local = sunrise_utc + timedelta(seconds=tz_offset)
    sunset_local = sunset_utc + timedelta(seconds=tz_offset)

    return {
        #Temperature Data
        "temp_celsius": round(main["temp"], 1),
        "temp_fahrenheit": round(main["temp"] * 9/5 + 32, 1),
        "feels_like_celsius": round(main["feels_like"], 1),
        "feels_like_fahrenheit": round(main["feels_like"] * 9/5 + 32, 1),
        "temp_min_celsius": round(main["temp_min"], 1),
        "temp_min_fahrenheit": round(main["temp_min"] * 9/5 + 32, 1),
        "temp_max_celsius": round(main["temp_max"], 1),
        "temp_max_fahrenheit": round(main["temp_max"] * 9/5 + 32, 1),

        #Atmospheric Data
        "pressure": main["pressure"],
        "humidity": main["humidity"],
        "sea_level": main.get("sea_level", 0),

        #Weather Conditions
        "condition": weather["main"],
        "description": weather["description"].capitalize(),
        "icon": weather["icon"],

        #Wind Data
        "wind_speed": round(wind.get("speed", 0), 1),

        #Sunrise/Sunset Data
        "sunrise": sunrise_local.strftime('%H:%M:%S'),
        "sunset": sunset_local.strftime('%H:%M:%S'),

        #Location Data
        "timezone": tz_offset
    }

# Display weather information in the GUI
def display_weather(weather_info, city_name, state_code):
    if not weather_info:
        messagebox.showerror("Error", "City Not Found. Please enter a valid city name.")
        return
        
    formatted_city = f"{city_name.title()}, {state_code.upper()}"
    
    result_box.insert(tk.END, f"\nWeather for {formatted_city}:\n\n", "heading")
    #result_box.insert(tk.END, "Weather Icon: ", "bold")
    icon_url = f"http://openweathermap.org/img/wn/{weather_info['icon']}@2x.png"

    try:
        # Fetch the image data
        with urllib.request.urlopen(icon_url) as u:
            raw_data = u.read()
        
        # Convert to a format Tkinter can use
        im = Image.open(BytesIO(raw_data))
        
        new_size = (50, 50)  # Smaller size
        im = im.resize(new_size)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(im)
        
        # Create a label to display the image
        icon_label = tk.Label(
            result_box, 
            image=photo, 
            bg='white', 
            bd=0)
        icon_label.image = photo  # Keep a reference!
        
        # Insert the image into the text widget
        result_box.window_create(tk.END, window=icon_label)
        result_box.insert(tk.END, "  ")
        
    except Exception as e:
        result_box.insert(tk.END, f"[Icon not available] - {str(e)}\n")

    result_box.insert(tk.END, f"{weather_info['temp_celsius']}°C / {weather_info['temp_fahrenheit']}°F\n")
    result_box.insert(tk.END, "Conditions: ", "bold")
    result_box.insert(tk.END, f"{weather_info['condition']}\n")
    result_box.insert(tk.END, "Feels Like: ", "bold")
    result_box.insert(tk.END, f"{weather_info['feels_like_celsius']}°C / {weather_info['feels_like_fahrenheit']}°F\n")
    result_box.insert(tk.END, "Min/Max (in °C): ", "bold")
    result_box.insert(tk.END, f"{weather_info['temp_min_celsius']}°C / {weather_info['temp_max_celsius']}°C\n")
    result_box.insert(tk.END, "Min/Max (in °F): ", "bold")
    result_box.insert(tk.END, f"{weather_info['temp_min_fahrenheit']}°F / {weather_info['temp_max_fahrenheit']}°F\n")
    result_box.insert(tk.END, "Description: ", "bold")
    result_box.insert(tk.END, f"{weather_info['description']}\n")
    result_box.insert(tk.END, "Wind Speed: ", "bold")
    result_box.insert(tk.END, f"{weather_info['wind_speed']} m/s\n")
    result_box.insert(tk.END, "Sea Level: ", "bold")
    result_box.insert(tk.END, f"{weather_info['sea_level']} hPa\n")
    result_box.insert(tk.END, "Pressure: ", "bold")
    result_box.insert(tk.END, f"{weather_info['pressure']} hPa\n")
    result_box.insert(tk.END, "Humidity: ", "bold")
    result_box.insert(tk.END, f"{weather_info['humidity']}%\n")
    result_box.insert(tk.END, "Sunrise: ", "bold")
    result_box.insert(tk.END, f"{weather_info['sunrise']}\n")
    result_box.insert(tk.END, "Sunset: ", "bold")
    result_box.insert(tk.END, f"{weather_info['sunset']}\n")

    tz_hours = weather_info['timezone'] // 3600
    tz_sign = '-' if tz_hours < 0 else '+'
    tz_display = f"UTC/GMT {tz_sign}{abs(tz_hours)} hours"

    result_box.insert(tk.END, "Timezone: ", "bold")
    result_box.insert(tk.END, f"{tz_display}\n")
    result_box.insert(tk.END, "\n----------------------------------------\n")

# Fetch and display weather for all locations
def get_weather():
    global current_weather_data
    
    if not location_entries:
        messagebox.showerror("Error", "Please add at least one location")
        return

    # Clear previous results
    current_weather_data = []
    any_failures = False
    
    for city_entry, state_entry, _ in location_entries:
        city = city_entry.get().strip()
        state = state_entry.get().strip()
        
        if not city or not state:
            messagebox.showerror("Error", "Please fill all city/state fields")
            return
            
        weather_data, error_msg = fetch_weather_data(city, state)
        if error_msg:
            messagebox.showerror("Weather Error", error_msg)
            any_failures = True
            continue
            
        weather = process_weather_data(weather_data)
        if weather:
            current_weather_data.append({
                "city": city,
                "state": state,
                **weather
            })
        else:
            any_failures = True
    
    # Only show results if we have successful data
    if current_weather_data:
        toggle_input_visibility(show=False)
        toggle_results_visibility(show=True)
        result_box.delete("1.0", tk.END)
        for weather in current_weather_data:
            display_weather(weather, weather['city'], weather['state'])
        export_button_frame.pack(pady=10)
        root.geometry("800x900")
    elif not any_failures:
        messagebox.showinfo("Info", "No weather data to display")

# Add a new location input row
def add_location_input(parent_frame=None):  
    if len(location_entries) >= 5:
        messagebox.showinfo("Limit Reached", "Maximum of 5 locations allowed")
        return
        
    frame = parent_frame if parent_frame else location_frame
    row_frame = tk.Frame(frame, bg="#f0f8ff")
    row_frame.pack(pady=5)
    
    # City input
    tk.Label(
        row_frame, 
        text="City:", 
        bg="#f0f8ff",
        fg = TEXT_COLOR_DARK, 
        font=("Helvetica", 14)).grid(row=0, column=0, sticky="w")

    city_entry = tk.Entry(
        row_frame, 
        font=("Helvetica", 14), 
        width=20)
    
    city_entry.grid(row=1, column=0, padx=5)
    
    # State input
    tk.Label(
        row_frame, 
        text="State:", 
        bg="#f0f8ff", 
        fg = TEXT_COLOR_DARK,
        font=("Helvetica", 14)).grid(row=0, column=1, sticky="w")
    
    state_entry = tk.Entry(
        row_frame, 
        font=("Helvetica", 14), 
        width=5)
    
    state_entry.grid(row=1, column=1, padx=5)
    
   # Store references for clearing later
    input_elements.append((city_entry, state_entry)) 
    location_entries.append((city_entry, state_entry, None))

# Create weather image using template
def create_weather_image(template_type="post"):
    if not current_weather_data:
        messagebox.showerror("Error", "No weather data to export")
        return
        
    try:
        template_path = TEMPLATE_PATHS.get(template_type, TEMPLATE_PATHS["post"])
        image = Image.open(template_path)
        draw = ImageDraw.Draw(image)
        
        # Try to load custom font, fallback to default
        try:
            font_large = ImageFont.truetype(DEFAULT_FONT, TEMPLATES[template_type]["font_sizes"]["large"])
            font_medium = ImageFont.truetype(DEFAULT_FONT, TEMPLATES[template_type]["font_sizes"]["medium"])
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
        
        # Add date
        today = date.today().strftime("%A - %B %d, %Y")
        draw.text(
            TEMPLATES[template_type]["date_position"], 
            today, 
            fill=TEXT_COLOR, 
            font=font_medium
        )
        
        # Add weather for each location
        for i, weather in enumerate(current_weather_data):
            if i >= len(TEMPLATES[template_type]["city_position"]):
                break
                
            # City name
            city_text = f"{weather['city'].title()}, {weather['state'].upper()}"
            city_pos = TEMPLATES[template_type]["city_position"][i]
            draw.text(
                city_pos,  # Slightly above temp position
                city_text,
                fill=TEXT_COLOR_DARK,
                font=font_large
            )
            
            # Temperature
            temp_text = f"{weather['temp_celsius']}°C"
            temp_pos = TEMPLATES[template_type]["temp_position"][i]
            draw.text(
                temp_pos,
                temp_text,
                fill=TEXT_COLOR,
                font=font_medium
            )
            
            # Humidity (optional)
            if "humidity_position" in TEMPLATES[template_type]:
                hum_text = f"{weather['humidity']}%"
                hum_pos = TEMPLATES[template_type]["humidity_position"][i]
                draw.text(
                    hum_pos,
                    hum_text,
                    fill=TEXT_COLOR,
                    font=font_medium
                )
        
        # Save the image
        save_dir = filedialog.askdirectory(title="Select Save Location")
        if save_dir:
            filename = f"weather_{template_type}_{date.today().strftime('%Y%m%d')}.png"
            save_path = os.path.join(save_dir, filename)
            image.save(save_path)
            
            # Optionally save as PDF
            pdf_path = os.path.join(save_dir, filename.replace(".png", ".pdf"))
            image.convert("RGB").save(pdf_path)
            
            messagebox.showinfo("Success", f"Exported to:\n{save_path}\n{pdf_path}")
            
    except Exception as e:
        messagebox.showerror("Export Error", f"Failed to create image: {str(e)}")

# Initialize the GUI with enhanced styling
def init_gui():
    global root, location_frame, export_button_frame, main_frame, header_frame, description_label, button_frame
    
    root = tk.Tk()
    root.title("Weather Forecast Automator")
    root.configure(bg="#f0f8ff")  
    
    # Set window size and center it
    window_width = 800
    window_height = 700
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Main container with padding
    main_frame = tk.Frame(root, bg="#f0f8ff", padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # App Header
    header_frame = tk.Frame(main_frame, bg="#f0f8ff")
    header_frame.pack(fill=tk.X, pady=(0, 20))
    
    tk.Label(
        header_frame,
        text="Weather Forecast Post Generator",
        font=("Helvetica", 28, "bold"),
        bg="#f0f8ff",
        fg="#2c3e50"
    ).pack(side=tk.TOP, pady=10)
    
    description_label = tk.Label(
        header_frame,
        text="Get weather forecasts for up to 5 locations and export as social media posts\n"
             "Enter city and state codes (e.g. 'Boston, MA') then click 'Get Weather' in order to fetch the data.",
        font=("Helvetica", 14),
        bg="#f0f8ff",
        fg="#7f8c8d"
    )
    description_label.pack(side=tk.TOP)
    
    # Location input frame
    location_frame = tk.Frame(main_frame, bg="#f0f8ff")
    location_frame.pack(fill=tk.X)
    
    # Add initial location input
    add_location_input(location_frame)
    
    # Buttons frame
    button_frame = tk.Frame(main_frame, bg="#f0f8ff")
    button_frame.pack(pady=10)
    
    # Add location button
    add_button = tk.Button(
        button_frame,
        text="+ Add Location",
        command=lambda: add_location_input(),
        **BUTTON_STYLE
    )
    add_button.pack(side=tk.LEFT, padx=5)
    add_hover_effect(add_button)
    
    # Get weather button
    weather_button = tk.Button(
        button_frame,
        text="Get Weather",
        command=get_weather,
        **BUTTON_STYLE
    )
    weather_button.pack(side=tk.LEFT, padx=5)
    add_hover_effect(weather_button)
    
    # Export buttons frame
    export_button_frame = tk.Frame(main_frame, bg="#f0f8ff")
    
    # Export buttons
    export_post = tk.Button(
        export_button_frame,
        text="Export as Post",
        command=lambda: create_weather_image("post"),
        **BUTTON_STYLE
    )
    export_post.pack(side=tk.LEFT, padx=5)
    add_hover_effect(export_post)
    
    export_story = tk.Button(
        export_button_frame,
        text="Export as Story",
        command=lambda: create_weather_image("story"),
        **BUTTON_STYLE
    )
    export_story.pack(side=tk.LEFT, padx=5)
    add_hover_effect(export_story)
    
    # Ensure export buttons are hidden initially
    export_button_frame.pack_forget()

    return root

# Show or hide the results and preview sections
def toggle_results_visibility(show=True):
    global result_frame, preview_frame, preview_canvas, preview_label, result_box
    
    if show and not hasattr(toggle_results_visibility, "results_created"):
        # Create frame if it doesn't exist
        result_frame = tk.Frame(main_frame, bg="#f0f8ff")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Text results
        result_box = tk.Text(
            result_frame,
            wrap=tk.WORD,
            font=("Helvetica", 14),
            height=10,
            width=60,
            relief=tk.SUNKEN,
            bd=2
        )

        result_label = tk.Label(
            result_frame,
            text="Results Preview Window: ", 
            font=("Helvetica", 18, "bold"),
            bg="#f0f8ff",
            justify="left"
        )

        result_label.pack(fill=tk.X)
        result_label.config(fg=TEXT_COLOR_DARK)

        result_box.pack(fill=tk.BOTH, expand=True)
        result_box.tag_configure("heading", font=("Helvetica", 18, "bold"))
        result_box.tag_configure("bold", font=("Helvetica", 14, "bold"))
        result_box.insert(tk.END, "Weather Results:\n", "heading")
        result_box.insert(tk.END, "                                    \n")
        
        # Scrollbar
        scrollbar = tk.Scrollbar(result_frame, command=result_box.yview)
        result_box.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        result_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Back button at the bottom
        back_button = tk.Button(
            result_frame,
            text="← Back to Input",
            command=lambda: [
                toggle_results_visibility(show=False),
                toggle_input_visibility(show=True),
                reset_input_view()  
            ],
            **BUTTON_STYLE
        )
        back_button.pack(pady=10)
        add_hover_effect(back_button)

        toggle_results_visibility.results_created = True
    elif not show and hasattr(toggle_results_visibility, "results_created"):
        result_frame.pack_forget()

# Add hover effect to buttons
def add_hover_effect(button, hover_color="#c8a2c8", default_color="white"):
    def on_enter(e):
        button.config(background=hover_color)
    def on_leave(e):
        button.config(background=default_color)
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)

# Show or hide the input elements (description, location inputs, buttons)
def toggle_input_visibility(show=True):
    if show:
        header_frame.pack(fill=tk.X, pady=(0, 20))
        description_label.pack(side=tk.TOP)
        location_frame.pack(fill=tk.X)
        button_frame.pack(pady=10)
    else:
        header_frame.pack_forget()
        description_label.pack_forget()
        location_frame.pack_forget()
        button_frame.pack_forget()

# Reset the input view to its initial state
def reset_input_view():
    global current_weather_data, location_entries, input_elements
    
    # Clear all input fields
    for entry_pair in input_elements:
        for entry in entry_pair:
            entry.delete(0, tk.END)
    
    # Clear all location frames except the first one
    for widget in location_frame.winfo_children()[1:]:
        widget.destroy()
    
    # Clear all stored references
    location_entries.clear()
    input_elements.clear()
    current_weather_data = []
    
    # Hide export buttons
    export_button_frame.pack_forget()
    
    # Re-add the initial location input
    add_location_input()
    
    # Reset window size
    root.geometry("800x700")

# Main function to run the application
def main():
    if not configure():
        return  # Exit if configuration fails

    configure()
    root = init_gui()
    root.mainloop()

if __name__ == "__main__":
    main()

# This code is part of a weather application that fetches and displays weather data
# from OpenWeatherMap API. It includes a GUI for user input, error handling, and
# functionality to export the weather data as images or PDFs. The application is
# designed to be user-friendly and visually appealing, with hover effects and
# customizable templates for social media posts.

# Created by Felipe de Souza
# Date: 2025-05-08
# Version: 2.0.0