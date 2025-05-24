import requests
import json
import tkinter as tk
from tkinter import StringVar, messagebox, filedialog, ttk
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
from firebase_config import db
from login_screen import LoginScreen
import ttkbootstrap as ttkb

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
description_label_frame = None
notebook = None
meter_widgets = []  # To keep references to meter widgets

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

def display_weather(weather_info, city_name, state_name, country_code):
    if not weather_info:
        messagebox.showerror("Error", "City Not Found. Please enter a valid city name.")
        return

    # Create a new tab for this city
    city_tab = ttk.Frame(notebook, padding=10)
    notebook.add(city_tab, text=f"{city_name.title()}, {state_name.title()}, {country_code.upper()}")
    
    # Create header frame with city name and weather icon
    header_frame = ttk.Frame(city_tab)
    header_frame.pack(fill=tk.X, pady=5)
    
    # Add weather icon
    try:
        icon_url = f"http://openweathermap.org/img/wn/{weather_info['icon']}@2x.png"
        with urllib.request.urlopen(icon_url) as u:
            raw_data = u.read()
        im = Image.open(BytesIO(raw_data))
        im = im.resize((50, 50))
        photo = ImageTk.PhotoImage(im)
        icon_label = ttk.Label(header_frame, image=photo)
        icon_label.image = photo  # Keep reference
        icon_label.pack(side=tk.LEFT, padx=10)
    except Exception as e:
        print(f"Couldn't load weather icon: {e}")
    
    # Add city name and condition
    title_frame = ttk.Frame(header_frame)
    title_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    city_name_label = ttk.Label(
        title_frame,
        text=f"{city_name.title()}, {state_name.title()}, {country_code.upper()}",
        font=("Helvetica", 18, "bold"),
        bootstyle="primary"
    )
    city_name_label.pack(anchor=tk.W)
    
    weather_condition_label = ttk.Label(
        title_frame,
        text=f"{weather_info['condition']} ({weather_info['description']})",
        font=("Helvetica", 14),
        bootstyle="secondary"
    )
    weather_condition_label.pack(anchor=tk.W)
    
    # Create meter grid
    meter_frame = ttk.Frame(city_tab)
    meter_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    # Define meter configurations
    meter_configs = [
        # (title, value, max_value, unit, style)
        ("Temperature", weather_info['temp_celsius'], 50, "°C", "danger"),
        ("Feels Like", weather_info['feels_like_celsius'], 50, "°C", "warning"),
        ("Humidity", weather_info['humidity'], 100, "%", "info"),
        ("Pressure", weather_info['pressure'], 1100, "hPa", "success"),
        ("UV Index", weather_info['uv_index'], 11, "", "danger"),
        ("Cloudiness", weather_info['clouds'], 100, "%", "secondary"),
        ("Wind Speed", weather_info['wind_speed'], 20, "m/s", "primary"),
        ("Wind Gust", weather_info['wind_gust'], 30, "m/s", "primary")
    ]
    
    # Create 2x4 grid of meters
    for i, (title, value, max_val, unit, style) in enumerate(meter_configs):
        row = i // 5
        col = i % 5
        
        meter = ttkb.Meter(
            meter_frame,
            metersize=140,
            amountused=value,
            amounttotal=max_val,
            metertype="semi",
            stripethickness=10,
            subtext=title,
            textright=unit,
            interactive=False,
            bootstyle=style
        )
        meter.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        meter_widgets.append(meter)  # Keep reference
        
        # Configure grid weights
        meter_frame.grid_rowconfigure(row, weight=1)
        meter_frame.grid_columnconfigure(col, weight=1)
    
    # Additional info frame
    info_frame = ttk.Labelframe(
        city_tab,
        text="Additional Information",
        bootstyle="info"
    )
    info_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    # Create two columns for additional info
    left_col = ttk.Frame(info_frame)
    left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    right_col = ttk.Frame(info_frame)
    right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    # Add info labels
    infos = [
        ("Sunrise:", weather_info['sunrise']),
        ("Sunset:", weather_info['sunset']),
        ("Dew Point:", f"{weather_info['dew_point']}°C"),
        ("Visibility:", f"{weather_info['visibility']/1000:.1f} km" if weather_info['visibility'] else "N/A"),
        ("Timezone:", weather_info['timezone_name']),
        ("Current Time:", f"{weather_info['current_time']} ({weather_info['current_date']})")
    ]
    
    for i, (label, value) in enumerate(infos):
        col = left_col if i % 2 == 0 else right_col
        info_row = ttk.Frame(col)
        info_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(
            info_row,
            text=label,
            bootstyle="primary",
            font=("Helvetica", 10, "bold")
        ).pack(side=tk.LEFT)
        
        ttk.Label(
            info_row,
            text=value,
            bootstyle="secondary"
        ).pack(side=tk.LEFT, padx=5)

# Fetch and display weather for all locations
def get_weather():
    global current_weather_data, notebook
    
    if not location_entries:
        messagebox.showerror("Error", "Please add at least one location")
        return

    current_weather_data = []
    any_failures = False
    
    for city_entry, state_entry, country_entry in location_entries:
        city = city_entry.get().strip()
        state = state_entry.get().strip()
        country = country_entry.get().strip().upper()

        if not city or not country:
            messagebox.showerror("Error", "Please fill all city/country fields")
            return
        
        if country == 'US' and not state:
            messagebox.showerror("Error", "Please fill state field for US locations")
            return
        
        # Fetch weather data with error handling
        weather_data, error_msg = fetch_weather_data(city, state, country)
        
        if error_msg:
            print(f"Error for {city}, {country}: {error_msg}")  # Debug output
            messagebox.showerror("Weather Error", 
                               f"Failed to get weather for {city}, {country}:\n{error_msg}")
            any_failures = True
            continue
            
        if not weather_data:
            print(f"No weather data for {city}, {country}")  # Debug output
            any_failures = True
            continue
            
        # Process the weather data
        weather = process_weather_data(weather_data)
        if weather:
            current_weather_data.append({
                "city": city,
                "state": state,
                "country": country,
                **weather  # Merge the weather data
            })
        else:
            any_failures = True
    
    # Display results if we have data
    if current_weather_data:
        toggle_input_visibility(show=False)
        toggle_results_visibility(show=True)
        
        # Clear existing tabs
        if notebook:
            for tab_id in notebook.tabs():
                notebook.forget(tab_id)
        
        # Display weather for each location
        for weather in current_weather_data:
            display_weather(weather, weather['city'], weather['state'], weather['country'])
        
        export_button_frame.pack(pady=10)
        root.geometry("900x1000")
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
        bootstyle="info", 
        font=("Helvetica", 14)).grid(row=0, column=0, sticky="w")

    city_entry = ttk.Entry(
        row_frame,
        font=("Helvetica", 14),
        bootstyle="info", 
        width=18)
    
    city_entry.grid(row=1, column=0, padx=5)
    
    # State input
    ttk.Label(
        row_frame, 
        text="State/Region:",
        bootstyle="info", 
        font=("Helvetica", 14)).grid(row=0, column=1, sticky="w")
    
    state_entry = ttk.Entry(
        row_frame,
        font=("Helvetica", 14),
        bootstyle="info", 
        width=18)
    
    state_entry.grid(row=1, column=1, padx=10)

    # Country Input
    ttk.Label(
        row_frame, 
        text="Country Code:",
        bootstyle="info", 
        font=("Helvetica", 14)).grid(row=0, column=2, sticky="w")
    
    country_entry = ttk.Combobox(
        row_frame,
        font=("Helvetica", 14), 
        width=8,
        bootstyle="info",
        values=list(fetch_country_codes().keys()),
        state="readonly")
    
    country_entry.set("US")  # Default to US
    country_entry.bind("<<ComboboxSelected>>", lambda e: country_entry.set(country_entry.get().upper()))

    country_entry.grid(row=1, column=2, padx=10)
    
    # Remove button
    remove_button = ttk.Button(
            row_frame,
            text="Remove",
            command=lambda: [
                row_frame.destroy(),
                location_entries.remove((city_entry, state_entry, country_entry)),
                input_elements.remove((city_entry, state_entry, country_entry)),
            ],
            bootstyle="danger")
    remove_button.grid(row=1, column=3, padx=10)        
    
    if len(location_entries) > 0:
        remove_button.config(state="normal")
    else:
        remove_button.config(state="disabled")

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
    global root, location_frame, export_button_frame, main_frame, header_frame
    global description_label_frame, description_label, button_frame
    global image_references, logout_button, actions_menubar
    
    root = existing_root
    root.title("Weather Forecast Automator")

    # Set window size and center it
    window_width = 900
    window_height = 1000
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.resizable(False, False) 

    # Create Menu Frame
    menu_frame = ttk.Frame(main_frame, bootstyle="primary")
    menu_frame.pack(side=tk.TOP, fill=tk.X)

    # Create Menubuttons
    help_menubutton = ttkb.Menubutton(menu_frame, text="Help", bootstyle="light")
    help_menubutton.pack(side=tk.RIGHT, pady=5)
    color_mode_menubutton = ttkb.Menubutton(menu_frame, text="Theme", bootstyle="light")
    color_mode_menubutton.pack(side=tk.RIGHT, pady=5)
    profile_menubutton = ttkb.Menubutton(menu_frame, text="Profile", bootstyle="light")
    profile_menubutton.pack(side=tk.RIGHT, pady=5)
    actions_menubutton = ttkb.Menubutton(menu_frame, text="Actions", bootstyle="light")
    actions_menubutton.pack(side=tk.RIGHT, pady=5)

     # Create Menu Bar
    actions_menubar = ttkb.Menu(root)
    profile_menubar = ttkb.Menu(root)
    color_mode_menubar = ttkb.Menu(root)
    help_menubar = ttkb.Menu(root)
    light_themes_menu = ttkb.Menu(color_mode_menubar, tearoff=0)
    dark_themes_menu = ttkb.Menu(color_mode_menubar, tearoff=0)
    
    # Associate the inside menu with the menubutton
    actions_menubutton['menu'] = actions_menubar
    profile_menubutton['menu'] = profile_menubar
    color_mode_menubutton['menu'] = color_mode_menubar
    help_menubutton['menu'] = help_menubar

    # File menu
    actions_menubar.add_command(label="Add Location", command=lambda: add_location_input(location_frame))
    actions_menubar.add_command(label="Get Weather", command=get_weather)
    actions_menubar.add_separator()
    actions_menubar.add_command(label="Export as Post", command=lambda: create_weather_image("post"))
    actions_menubar.add_command(label="Export as Story", command=lambda: create_weather_image("story"))
    actions_menubar.add_separator()
    actions_menubar.add_command(label="Reset", command=lambda: [
        reset_input_view(),
        toggle_results_visibility(show=False),
        toggle_input_visibility(show=True)
    ])
    actions_menubar.add_separator()
    actions_menubar.add_command(label="Exit", command=root.destroy)

    # Profile Menu
    profile_menubar.add_command(label="View Profile", command=view_profile)
    profile_menubar.add_command(label="Edit Profile", command=edit_profile)
    profile_menubar.add_separator()
    profile_menubar.add_command(label="Logout", command=logout_user)

    # Help menu 
    help_menubar.add_command(label="About", command=lambda: messagebox.showinfo("About", "Weather Forecast Automator\n\nVersion 3.1\n\nCreated by Felipe de Souza"))

    # Dark/Light Mode Cascades
    color_mode_menubar.add_cascade(label="Light Themes", menu=light_themes_menu)
    color_mode_menubar.add_cascade(label="Dark Themes", menu=dark_themes_menu)

    # Theme Menu
    item_var = StringVar()

    # Light themes
    light_themes = ['pulse', 'minty', 'lumen', 'sandstone', 'simplex', 'cerculean']
    for theme in light_themes:
        light_themes_menu.add_radiobutton(
            label=theme.capitalize(), 
            variable=item_var,
            value=theme,
            command=lambda t=theme: update_bootstyle_theme(t)
        )

    # Dark themes
    dark_themes = ['darkly', 'solar', 'superhero']
    for theme in dark_themes:
        dark_themes_menu.add_radiobutton(
            label=theme.capitalize(), 
            variable=item_var,
            value=theme,
            command=lambda t=theme: update_bootstyle_theme(t)
        )

    # Load and set window icon
    try:
        icon_path = "Images/FelipeWeatherAppLogo.png"
        if os.path.exists(icon_path):
            img = Image.open(icon_path)
            img = img.resize((75, 75), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            image_references['icon'] = photo  
            root.iconphoto(True, photo)
    except Exception as e:
        print(f"Could not load window icon: {e}")

    # App Header
    header_frame = ttk.Frame(main_frame, bootstyle="primary")
    header_frame.pack(fill=tk.X, pady=(5, 0))

    # Load logo image
    try:
        logo_path = "Images/FelipeWeatherAppLogo.png"
        if os.path.exists(logo_path):
            img = Image.open(logo_path).resize((125, 125), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            image_references['logo'] = photo 

    except Exception as e:
        print(f"Could not load logo image: {e}") 

    # Title label
    logo_text = ttk.Label(
        header_frame,
        text="    Weather Forecast Generator",
        font=("Helvetica", 58, "bold"),
        bootstyle="inverse-primary",
        wraplength=775,  
        justify="center",
        image=photo,
        compound=LEFT,
        padding=(30,0),
    )
    logo_text.pack(side=tk.LEFT, pady=30, padx=50)

    # Description Frame
    description_frame = ttk.Frame(main_frame)
    description_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 10))

    # Description label frame with wrapped text
    description_label_frame = ttkb.Labelframe(
        description_frame,
        text="Instructions",  # This is the frame's title
        bootstyle="primary"
    )

    # Create a label inside the frame for the wrapped text
    description_label = ttk.Label(
        description_label_frame,
        text=(
            "Easily generate and share weather forecasts for up to five locations at once. "
            "Simply enter a city name along with its ISO country code (e.g., Florence, IT).\n\n"
            "For locations within the United States, be sure to include the full state name (e.g., Canton, Ohio, US). " 
            "Once you're ready, click 'Get Weather' to retrieve the latest forecast details.\n\n" 
            "Tip: Use official two-letter ISO country codes for accurate results (e.g., US, BR, IT)"),
        wraplength=575,  # Adjust this based on your window size
        justify="left",
        font=("Helvetica", 13),
        bootstyle="primary"  
    )

    # Pack the label inside the frame with padding
    description_label.pack(padx=10, pady=10)

    # Pack the frame in the header
    description_label_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

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
    
    # Back to input button
    back_to_input_button=ttk.Button(
        export_button_frame,
        text="← Back to Input",
        command=lambda: [
            toggle_results_visibility(show=False),
            toggle_input_visibility(show=True),
            reset_input_view()
        ],
        bootstyle="warning"
    )
    back_to_input_button.pack(side=tk.LEFT, padx=10)

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
    
    # Logout button
    logout_button=ttk.Button(
        export_button_frame,
        text="Logout",
        command=logout_user,
        bootstyle="danger"
    )
    logout_button.pack(side=tk.LEFT, padx=10)
    
    # Ensure export buttons are hidden initially
    export_button_frame.pack_forget()

    return root

# Show or hide the results and preview sections
def toggle_results_visibility(show=True):
    global result_frame, notebook, description_label_frame        

    if show and not hasattr(toggle_results_visibility, "results_created"):
        result_frame = ttk.Frame(main_frame)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)

        # Create Scrollbar for the entire results frame
        #scrollbar = ttk.Scrollbar(result_frame, command=)
        #scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create notebook widget
        notebook = ttkb.Notebook(result_frame, bootstyle="primary")
        notebook.pack(fill=tk.BOTH, expand=True)
        
        toggle_results_visibility.results_created = True
        
    elif not show and hasattr(toggle_results_visibility, "results_created"):
        # Clear all tabs and widgets
        for tab_id in notebook.tabs():
            notebook.forget(tab_id)
        
        # Clear meter widget references
        meter_widgets.clear()
        
        result_frame.pack_forget()

# Show or hide the input elements (description, location inputs, buttons)
def toggle_input_visibility(show=True):
    if show:
        header_frame.pack(fill=tk.X, pady=(0, 20))
        description_label.pack(side=tk.TOP)
        location_frame.pack(fill=tk.X)
        button_frame.pack(pady=10)
    else:
        location_frame.pack_forget()
        button_frame.pack_forget()

# Reset the input view to its initial state
def reset_input_view():
    global current_weather_data, location_entries, input_elements, notebook
    
    # Destroy all widgets in the location_frame
    for widget in location_frame.winfo_children():
        widget.destroy()
    
    # Clear all stored references
    location_entries.clear()
    input_elements.clear()
    current_weather_data = []
    meter_widgets.clear()
    
    # Clear notebook tabs if it exists
    if notebook:
        for tab_id in notebook.tabs():
            notebook.forget(tab_id)
    
    # Hide export buttons
    export_button_frame.pack_forget()

    # Clear the result flag
    if hasattr(toggle_results_visibility, "results_created"):
        del toggle_results_visibility.results_created
    
    # Re-add the initial location input
    add_location_input(location_frame)
    
    # Show description again when resetting
    description_label.pack(side=tk.TOP)

    # Reset window size
    root.geometry("900x1000")

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
    global root, actions_menubar
    
    # Destroy login screen widgets
    for widget in root.winfo_children():
        widget.destroy()
    
    # Resize window for main app
    root.geometry("900x1000")

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

# Update the bootstyle theme to the selected menubutton radio option
def update_bootstyle_theme(theme_name):
    global root
    
    try:
        # Update the root window theme
        root.style.theme_use(theme_name)
        
        # Refresh all widgets to apply the new theme
        for widget in root.winfo_children():
            widget.update()
            
    except Exception as e:
        messagebox.showerror("Theme Error", f"Failed to change theme: {str(e)}")

# Placeholder functions for future implementation
def view_profile():
    pass

def edit_profile():
    pass

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
# Date: 2025-05-19
# Version: 3.1