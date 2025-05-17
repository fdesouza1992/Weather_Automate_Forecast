import requests
import json
import tkinter as tk
from tkinter import messagebox, filedialog
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
from ttkbootstrap import Window, Style
from ttkbootstrap.constants import *
from tkinter import ttk

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

# Image references to prevent garbage collection
image_references = {}

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
def fetch_weather_data(city_name, state_code, country_code):
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

    #Current time calculation
    current_time_utc = datetime.now(timezone.utc)
    current_time_local = current_time_utc + timedelta(seconds=tz_offset)

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
        "timezone": tz_offset,
        "current_time": current_time_local.strftime('%H:%M:%S'),
        "current_date": current_time_local.strftime('%Y-%m-%d')
    }

# Display weather information in the GUI
def display_weather(weather_info, city_name, state_code, country_code):
    if not weather_info:
        messagebox.showerror("Error", "City Not Found. Please enter a valid city name.")
        return
        
    formatted_city = f"{city_name.title()}, {state_code.upper()}, {country_code.upper()}"
    
    result_box.insert(tk.END, f"\nWeather for {formatted_city}:\n\n", "heading")
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
        icon_label = ttk.Label(
            result_box, 
            image=photo)
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
    result_box.insert(tk.END, "Current Time (24hrs format): ", "bold")
    result_box.insert(tk.END, f"{weather_info['current_time']} ({weather_info['current_date']})\n")
    result_box.insert(tk.END, "\n------------------------------------------------------------------------------\n")

# Fetch and display weather for all locations
def get_weather():
    global current_weather_data
    
    if not location_entries:
        messagebox.showerror("Error", "Please add at least one location")
        return

    # Clear previous results
    current_weather_data = []
    any_failures = False
    
    for city_entry, state_entry, country_entry in location_entries:
        city = city_entry.get().strip()
        state = state_entry.get().strip()
        country = country_entry.get().strip().upper() or "US"  # Default to US if empty
        
        if not city or not state:
            messagebox.showerror("Error", "Please fill all city/state fields")
            return
            
        weather_data, error_msg = fetch_weather_data(city, state, country)
        if error_msg:
            messagebox.showerror("Weather Error", error_msg)
            any_failures = True
            continue
            
        weather = process_weather_data(weather_data)
        if weather:
            current_weather_data.append({
                "city": city,
                "state": state,
                "country": country,
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
            display_weather(weather, weather['city'], weather['state'], weather['country'])
        export_button_frame.pack(pady=10)
        root.geometry("675x675")
    elif not any_failures:
        messagebox.showinfo("Info", "No weather data to display")

# Add a new location input row
def add_location_input(parent_frame=None):  
    if len(location_entries) >= 5:
        messagebox.showinfo("Limit Reached", "Maximum of 5 locations allowed")
        return
        
    frame = parent_frame if parent_frame else location_frame
    row_frame = ttk.Frame(frame)
    row_frame.pack(pady=5)
    
    # City input
    ttk.Label(
        row_frame, 
        text="City:", 
        font=("Helvetica", 14)).grid(row=0, column=0, sticky="w")

    city_entry = ttk.Entry(
        row_frame,
        font=("Helvetica", 14), 
        width=18)
    
    city_entry.grid(row=1, column=0, padx=5)
    
    # State input
    ttk.Label(
        row_frame, 
        text="State/Region:", 
        font=("Helvetica", 14)).grid(row=0, column=1, sticky="w")
    
    state_entry = ttk.Entry(
        row_frame,
        font=("Helvetica", 14), 
        width=8)
    
    state_entry.grid(row=1, column=1, padx=10)

    # Country Input
    ttk.Label(
        row_frame, 
        text="Country Code:", 
        font=("Helvetica", 14)).grid(row=0, column=2, sticky="w")
    
    country_entry = ttk.Entry(
        row_frame,
        font=("Helvetica", 14), 
        width=8)
    
    country_entry.insert(0, "US")                   # Default to US
    country_entry.grid(row=1, column=2, padx=10)
    
   # Store references for clearing later
    input_elements.append((city_entry, state_entry, country_entry)) 
    location_entries.append((city_entry, state_entry, country_entry))

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
            font_title = ImageFont.truetype(DEFAULT_FONT, TEMPLATES[template_type]["font_sizes"]["title"])
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_title = ImageFont.load_default()
        
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

            # App Title
            title_text = "Weather Forecast Generator"
            title_pos = TEMPLATES[template_type]["title_position"]
            draw.text(
                title_pos,
                title_text,
                fill=TEXT_COLOR,
                font=font_title,
                align="center"
            )

            # City name
            city_text = f"{weather['city'].title()}, {weather['state'].upper()}, {weather['country'].upper()}"
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
                font=font_large
            )
            
            # Humidity (optional)
            if "humidity_position" in TEMPLATES[template_type]:
                hum_text = f"{weather['humidity']}%"
                hum_pos = TEMPLATES[template_type]["humidity_position"][i]
                draw.text(
                    hum_pos,
                    hum_text,
                    fill=TEXT_COLOR,
                    font=font_large
                )
        
        # Save the image
        save_dir = filedialog.askdirectory(title="Select Save Location")
        if save_dir:
            filename = f"weather_{template_type}_{date.today().strftime('%Y%m%d_%H%M%S')}.png"
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
    global root, location_frame, export_button_frame, main_frame, header_frame, description_label, button_frame, image_references
    
    root = Window(themename="pulse")
    root.title("Weather Forecast Automator")
    
    # Set window size and center it
    window_width = 650
    window_height = 650
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.resizable(False, False) 
    
    # Load and set window icon
    try:
        icon_path = "Images/FelipeWeatherAppLogo.png"
        if os.path.exists(icon_path):
            img = Image.open(icon_path)
            img = img.resize((32, 32), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            image_references['icon'] = photo  # Keep reference
            root.iconphoto(True, photo)
    except Exception as e:
        print(f"Could not load window icon: {e}")
    
    # App Header
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill=tk.X, pady=(10, 20))

    # Load logo image
    try:
        logo_path = "Images/FelipeWeatherAppLogo.png"
        if os.path.exists(logo_path):
            img = Image.open(logo_path).resize((150, 150), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            image_references['logo'] = photo  # Keep reference
            logo_label = ttk.Label(header_frame, image=photo)
            logo_label.pack(side=tk.LEFT, pady=10, padx=10)
    except Exception as e:
        print(f"Could not load logo image: {e}")

    ttk.Label(
        header_frame,
        text="Weather Forecast Post Generator",
        font=("Helvetica", 28, "bold")
    ).pack(side=tk.TOP, pady=10)
    
    description_label = ttk.Label(
        header_frame,
        text="Forecast up to 5 locations and export weather posts instantly.\n\n"+
        "Enter city, state/region, and ISO country code (e.g., Boston, MA, US), \n"+
        "then click 'Get Weather' to retrieve the latest data.\n\n"+
        "Note: Country codes must follow the ISO format (e.g., US, BR, IT).",
        font=("Helvetica", 14))
    description_label.pack(side=tk.TOP)
    
    # Location input frame
    location_frame = ttk.Frame(main_frame)
    location_frame.pack(fill=tk.X)
    
    # Add initial location input
    add_location_input(location_frame)
    
    # Buttons frame
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=10)
    
    # Add location button
    add_button = ttk.Button(
        button_frame,
        text="+ Add Location",
        command=lambda: add_location_input(),
        bootstyle="primary")
    add_button.pack(side=tk.LEFT, padx=5)
    
    # Get weather button
    weather_button = ttk.Button(
        button_frame,
        text="Get Weather",
        command=get_weather,
        bootstyle="success")
    weather_button.pack(side=tk.LEFT, padx=5)
    
    # Export buttons frame
    export_button_frame = ttk.Frame(main_frame)
    
    # Export buttons
    export_post = ttk.Button(
        export_button_frame,
        text="Export as Post",
        command=lambda: create_weather_image("post"),
        bootstyle="info")
    export_post.pack(side=tk.LEFT, padx=5)
    
    export_story = ttk.Button(
        export_button_frame,
        text="Export as Story",
        command=lambda: create_weather_image("story"),
        bootstyle="warning")
    export_story.pack(side=tk.LEFT, padx=5)
    
    # Ensure export buttons are hidden initially
    export_button_frame.pack_forget()

    return root

# Show or hide the results and preview sections
def toggle_results_visibility(show=True):
    global result_frame, result_box
    
    if show and not hasattr(toggle_results_visibility, "results_created"):
        # Create frame if it doesn't exist
        result_frame = ttk.Frame(main_frame)
        result_frame.pack(fill=tk.BOTH, pady=10, padx=10, expand=True)

        # Text results - using tk.Text for better formatting
        result_box = tk.Text(
            result_frame,
            wrap=tk.WORD,
            font=("Helvetica", 14),
            height=10,
            width=60,
            relief=tk.SUNKEN,
            bg='white',
            fg=TEXT_COLOR_DARK,
            bd=2,
            padx=10,
            pady=10
        )
        result_box.pack(fill=tk.BOTH, expand=True)

        # Configure tags for styled text
        result_box.tag_configure("heading", font=("Helvetica", 18, "bold"))        
        result_box.tag_configure("bold", font=("Helvetica", 14, "bold"))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(result_frame, command=result_box.yview)
        result_box.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        result_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Back button at the bottom
        back_button = ttk.Button(
            result_frame,
            text="←Back to Input",
            command=lambda: [
                toggle_results_visibility(show=False),
                toggle_input_visibility(show=True),
                reset_input_view()
            ],
            bootstyle="danger"
        )
        back_button.pack(pady=10, padx=5)

        toggle_results_visibility.results_created = True
    elif not show and hasattr(toggle_results_visibility, "results_created"):
        result_frame.pack_forget()

# Show or hide the input elements (description, location inputs, buttons)
def toggle_input_visibility(show=True):
    if show:
        header_frame.pack(fill=tk.X, pady=(0, 20))
        description_label.pack(side=tk.TOP)
        location_frame.pack(fill=tk.X)
        button_frame.pack(pady=10)
    else:
        #header_frame.pack_forget()
        #description_label.pack_forget()
        location_frame.pack_forget()
        button_frame.pack_forget()

# Reset the input view to its initial state
def reset_input_view():
    global current_weather_data, location_entries, input_elements
    
    # Destroy all widgets in the location_frame to completely reset the input area
    for widget in location_frame.winfo_children():
        widget.destroy()
    
    # Clear all stored references
    location_entries.clear()
    input_elements.clear()
    current_weather_data = []
    
    # Hide export buttons
    export_button_frame.pack_forget()

    # Clear the result box flag so toggle_results_visibility can recreate it later
    if hasattr(toggle_results_visibility, "results_created"):
        del toggle_results_visibility.results_created
    
    # Re-add the initial location input
    add_location_input(location_frame)
    
    # Reset window size
    root.geometry("650x650")

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
# Date: 2025-05-11
# Version: 2.1