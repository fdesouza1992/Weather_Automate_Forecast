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
from firebase_config import db
from login_screen import LoginScreen

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
logout_button = None
description_frame = None

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
def fetch_weather_data(city_name, state_name, country_code):
    api_key = os.getenv("API_KEY")
    if not api_key:
        messagebox.showerror("API Error", "OpenWeatherMap API key not configured")
        return None
    
    # Step 1: Get coordinates for the city using the Direct Geocoding API
    if country_code == "US":
        # For US, use state abbreviation
        geocode_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name},{state_name},{country_code}&limit=5&appid={api_key}"
    else:
        geocode_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name},{country_code}&limit=5&appid={api_key}"

    try:
        # Get location coordinates
        geo_response = requests.get(geocode_url, timeout=15)
        if geo_response.status_code != 200:
            return None, f"Geocoding API error (Code: {geo_response.status_code})"
        
        geo_data = geo_response.json()
        if not geo_data:
            return None, f"Geocoding API returned no results for {city_name}, {state_name if country_code == 'US' else ''}, {country_code}"
        
        # Extract latitude and longitude
        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']

    # Step 2: Use the coordinates to get weather data
        weather_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely&units=metric&appid={api_key}"
        weather_response = requests.get(weather_url, timeout=15)

        if weather_response.status_code != 200:
            return None, f"Weather API error (Code: {weather_response.status_code})"
        
        weather_data = weather_response.json()
        return weather_data, None
    
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
    if not data:
        return None

    current = data.get("current", {})
    daily = data.get("daily", [{}])[0]  # Get today's weather
    tz_offset = data.get("timezone_offset", 0)  # in seconds
    timezone_name = data.get("timezone", "")

    def timestamp_to_local(ts):
        utc_time = datetime.fromtimestamp(ts, timezone.utc)
        return utc_time + timedelta(seconds=tz_offset)

    # Convert timestamps to local time
    sunrise_local = timestamp_to_local(current.get("sunrise", 0))
    sunset_local = timestamp_to_local(current.get("sunset", 0))

    # Current time calculation
    current_time_local = datetime.now(timezone.utc) + timedelta(seconds=tz_offset)

    # Temperature data (using daily forecast for min/max)
    temp = current.get("temp", 0)
    feels_like = current.get("feels_like", 0)
    temp_min = daily.get("temp", {}).get("min", temp)
    temp_max = daily.get("temp", {}).get("max", temp)
    humidity = current.get("humidity", 0)
    pressure = current.get("pressure", 0)
    dew_point = current.get("dew_point", 0)
    uv_index = current.get("uvi", 0)
    clouds = current.get("clouds", 0)
    sea_level = current.get("sea_level", 0)
    visibility = current.get("visibility", 0)

    # Weather conditions
    weather = current.get("weather", [{}])[0]  
    condition = weather.get("main", "")
    description = weather.get("description", "").capitalize()
    icon = weather.get("icon", "")

    # Wind data
    wind_speed = current.get("wind_speed", 0)
    wind_deg = current.get("wind_deg", 0)
    wind_gust = current.get("wind_gust", 0)

    return {
        #Temperature Data
        "temp_celsius": round(temp, 1),
        "temp_fahrenheit": round(temp * 9/5 + 32, 1),
        "feels_like_celsius": round(feels_like, 1),
        "feels_like_fahrenheit": round(feels_like * 9/5 + 32, 1),
        "temp_min_celsius": round(temp_min, 1),
        "temp_min_fahrenheit": round(temp_min * 9/5 + 32, 1),
        "temp_max_celsius": round(temp_max, 1),
        "temp_max_fahrenheit": round(temp_max * 9/5 + 32, 1),

        #Atmospheric Data
        "pressure": pressure,
        "humidity": humidity,
        "dew_point": dew_point,
        "uv_index": round(uv_index,1),
        "clouds": clouds,
        "visibility": visibility,
        "sea_level": sea_level,

        #Weather Conditions
        "condition": condition,
        "description": description,
        "icon": icon,

        #Wind Data
        "wind_speed": round(wind_speed, 1),
        "wind_deg": wind_deg,
        "wind_gust": round(wind_gust, 1),

        #Sunrise/Sunset Data
        "sunrise": sunrise_local.strftime('%H:%M:%S'),
        "sunset": sunset_local.strftime('%H:%M:%S'),

        #Location Data
        "timezone": tz_offset,
        "timezone_name": timezone_name,
        "current_time": current_time_local.strftime('%H:%M:%S'),
        "current_date": current_time_local.strftime('%Y-%m-%d')
    }

# Display weather information in the GUI
def display_weather(weather_info, city_name, state_name, country_code):
    if not weather_info:
        messagebox.showerror("Error", "City Not Found. Please enter a valid city name.")
        return
        
    formatted_city = f"{weather_info['city'].title()}, {weather_info['state'].upper()}, {weather_info['country'].upper()}"
    
    result_box.insert(tk.END, f"Weather for {formatted_city}:\n", "heading")
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
    result_box.insert(tk.END, "UV Index: ", "bold")
    result_box.insert(tk.END, f"{weather_info['uv_index']}\n")
    result_box.insert(tk.END, "Description: ", "bold")
    result_box.insert(tk.END, f"{weather_info['description']}\n")
    result_box.insert(tk.END, "Wind Speed: ", "bold")
    result_box.insert(tk.END, f"{weather_info['wind_speed']} m/s\n")
    result_box.insert(tk.END, "Wind Gust: ", "bold")
    result_box.insert(tk.END, f"{weather_info['wind_gust']} m/s\n")
    result_box.insert(tk.END, "Sea Level: ", "bold")
    result_box.insert(tk.END, f"{weather_info['sea_level']} hPa\n")
    result_box.insert(tk.END, "Pressure: ", "bold")
    result_box.insert(tk.END, f"{weather_info['pressure']} hPa\n")
    result_box.insert(tk.END, "Humidity: ", "bold")
    result_box.insert(tk.END, f"{weather_info['humidity']}%\n")
    result_box.insert(tk.END, "Dew Point: ", "bold")
    result_box.insert(tk.END, f"{weather_info['dew_point']}°C\n")
    result_box.insert(tk.END, "Sunrise: ", "bold")
    result_box.insert(tk.END, f"{weather_info['sunrise']}\n")
    result_box.insert(tk.END, "Sunset: ", "bold")
    result_box.insert(tk.END, f"{weather_info['sunset']}\n")

    tz_hours = weather_info['timezone'] // 3600
    tz_sign = '-' if tz_hours < 0 else '+'
    tz_display = f"UTC/GMT {tz_sign}{abs(tz_hours)} hours"

    result_box.insert(tk.END, "Timezone Name: ", "bold")
    result_box.insert(tk.END, f"{weather_info['timezone_name']}\n")
    result_box.insert(tk.END, "Timezone Offset: ", "bold")
    result_box.insert(tk.END, f"{tz_display}\n")
    result_box.insert(tk.END, "Current Time (24hrs format): ", "bold")
    result_box.insert(tk.END, f"{weather_info['current_time']} ({weather_info['current_date']})\n")
    result_box.insert(tk.END, "\n------------------------------------------------------------------------------\n\n")

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

        # Handle Combobox and Entry compatibility
        if isinstance(country_entry, ttk.Combobox):
            country = country_entry.get().strip().upper()
        else:
            country = country_entry.get().strip().upper()

        if not city or not country:
            messagebox.showerror("Error", "Please fill all city/country fields")
            return
        
        if country == 'US' and not state:
            messagebox.showerror("Error", "Please fill state field for US locations")
            return
        
        weather_data, error_msg = fetch_weather_data(city, state, country)
        if error_msg:
            messagebox.showerror("Weather Error", error_msg)
            any_failures = True
            continue
            
        weather = process_weather_data(weather_data)
        if weather:
            location_info = {
                "city": city,
                "state": state,
                "country": country,
            }
            current_weather_data.append({**location_info, **weather})
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
        root.geometry("675x775")
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
        width=18)
    
    state_entry.grid(row=1, column=1, padx=10)

    # Country Input
    ttk.Label(
        row_frame, 
        text="Country Code:", 
        font=("Helvetica", 14)).grid(row=0, column=2, sticky="w")
    
    country_entry = ttk.Combobox(
        row_frame,
        font=("Helvetica", 14), 
        width=8,
        values=list(fetch_country_codes().keys()),
        state="readonly")
    
    country_entry.set("US")  # Default to US
    country_entry.bind("<<ComboboxSelected>>", lambda e: country_entry.set(country_entry.get().upper()))

    # Uncomment the following lines if you want to use a regular entry instead of a combobox
    # country_entry = ttk.Entry(
    #     row_frame,
    #     font=("Helvetica", 14), 
    #     width=8)
    
    #country_entry.insert(0, "US")                   # Default to US

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
        
        country_codes = fetch_country_codes()

        # Add weather for each location
        for i, weather in enumerate(current_weather_data):
            if i >= len(TEMPLATES[template_type]["city_position"]):
                break

            #Get the country name from the dictionary
            country_code = weather['country'].upper()

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
            city_text = f"{weather['city'].title()}, {country_code}"
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
            filename = f"Weather_{template_type}_{today}.png"
            save_path = os.path.join(save_dir, filename)
            image.save(save_path)
            
            # Optionally save as PDF
            pdf_path = os.path.join(save_dir, filename.replace(".png", ".pdf"))
            image.convert("RGB").save(pdf_path)
            
            messagebox.showinfo("Success", f"Exported to:\n{save_path}\n{pdf_path}")
            
    except Exception as e:
        messagebox.showerror("Export Error", f"Failed to create image: {str(e)}")

# Initialize the GUI with enhanced styling
def init_gui(existing_root):
    global root, location_frame, export_button_frame, main_frame, header_frame, description_label, button_frame, image_references, logout_button
    
    root = existing_root
    root.title("Weather Forecast Automator")
    
    # Set window size and center it
    window_width = 675
    window_height = 775
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
            logo_label.pack(side=tk.TOP, pady=10)
    except Exception as e:
        print(f"Could not load logo image: {e}")

    # Title label
    ttk.Label(
        header_frame,
        text="Weather Forecast Post Generator",
        font=("Helvetica", 28, "bold"),
        bootstyle="primary"
    ).pack(side=tk.TOP)

    # Description label frame with wrapped text
    description_frame = ttk.Labelframe(
        header_frame,
        text="Instructions",  # This is the frame's title
        bootstyle="info"
    )

    # Create a label inside the frame for the wrapped text
    description_label = ttk.Label(
        description_frame,
        text=(
            "Easily generate and share weather forecasts for up to five locations at once. "
            "Simply enter a city name along with its ISO country code (e.g., Florence, IT).\n\n"
            "For locations within the United States, be sure to include the full state name (e.g., Canton, Ohio, US). " 
            "Once you're ready, click 'Get Weather' to retrieve the latest forecast details.\n\n" 
            "Tip: Use official two-letter ISO country codes for accurate results (e.g., US, BR, IT)"),
        wraplength=575,  # Adjust this based on your window size
        justify="left",
        font=("Helvetica", 13)  
    )

    # Pack the label inside the frame with padding
    description_label.pack(padx=10, pady=10)

    # Pack the frame in the header
    description_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

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
    add_button.pack(side=tk.LEFT, padx=10)
    
    # Get weather button
    weather_button = ttk.Button(
        button_frame,
        text="Get Weather",
        command=get_weather,
        bootstyle="success")
    weather_button.pack(side=tk.LEFT, padx=10)
    
    # Logout button
    logout_button = ttk.Button(
        button_frame,
        text="Logout",
        command=logout_user,
        bootstyle="danger")
    logout_button.pack(side=tk.LEFT, padx=10)

    # Export buttons frame
    export_button_frame = ttk.Frame(main_frame)
    
    # Export buttons
    export_post = ttk.Button(
        export_button_frame,
        text="Export as Post",
        command=lambda: create_weather_image("post"),
        bootstyle="primary")
    export_post.pack(side=tk.LEFT, padx=10)
    
    export_story = ttk.Button(
        export_button_frame,
        text="Export as Story",
        command=lambda: create_weather_image("story"),
        bootstyle="success")
    export_story.pack(side=tk.LEFT, padx=10)
    
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
        scrollbar = ttk.Scrollbar(result_frame, command=result_box.yview,bootstyle="primary-round")
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
            bootstyle="warning"
        )
        back_button.pack(pady=5, padx=5)

        # Logout button
        logout_button = ttk.Button(
            result_frame,
            text="Logout",
            command=logout_user,
            bootstyle="danger")
        logout_button.pack(pady=5, padx=5)

        toggle_results_visibility.results_created = True
    elif not show and hasattr(toggle_results_visibility, "results_created"):
        result_frame.pack_forget()

# Show or hide the input elements (description, location inputs, buttons)
def toggle_input_visibility(show=True):
    global description_frame, header_frame, location_frame, button_frame
    
    if show:
        header_frame.pack(fill=tk.X, pady=(0, 20))
        if description_frame:  # Only pack if it exists
            description_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        location_frame.pack(fill=tk.X)
        button_frame.pack(pady=10)
    else:
        location_frame.pack_forget()
        button_frame.pack_forget()
        if description_frame:  # Only forget if it exists
            description_frame.pack_forget()

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
    root.geometry("675x775")

# Fetch country codes from Firestore and populate the country entry
def fetch_country_codes():
    try:
        countries_ref = db.collection("countries")
        countries = countries_ref.stream()
        
        country_codes = {doc.id: doc.to_dict()["name"] for doc in countries}
        return country_codes
    except Exception as e:
        print(f"Error fetching country codes: {e}")
        return {}

# Define on_login_success at the module level
def on_login_success(uid, user_data):
    global root
    
    # Destroy login screen widgets
    for widget in root.winfo_children():
        widget.destroy()
    
    # Resize window for main app
    root.geometry("675x775")
    
    # Initialize your existing GUI exactly as before
    init_gui(root)
    
    # Optional: Print login confirmation
    print(f"User logged in: {user_data.get('name', 'User')}")

# Logout user and clear session data
def logout_user():
    global root, current_weather_data, location_entries, input_elements
    
    # Add confirmation dialog
    if not messagebox.askyesno("Logout", "Are you sure you want to logout?"):
        return

    # Clear all data
    current_weather_data = []
    location_entries = []
    input_elements = []
    
    # Destroy all widgets
    for widget in root.winfo_children():
        widget.destroy()
    
    # Reset window size for login screen
    root.geometry("475x625")
    
    # Show login screen again
    from login_screen import LoginScreen
    LoginScreen(root, on_login_success)

# Main function to run the application
def main():
    global root  # Make root available globally
    
    if not configure():
        return  # Exit if configuration fails

    # Create root window
    root = Window(themename="pulse")
    root.title("Weather Forecast Automator")
    
    # Set smaller window size for login screen
    window_width = 475
    window_height = 625
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.resizable(False, False)
    
    # Show login screen first
    LoginScreen(root, on_login_success)
    
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