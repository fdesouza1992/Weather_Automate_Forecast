# Description: A simple weather app that fetches weather data using the OpenWeatherMap API.
# import required modules
import requests
import json
import tkinter as tk
from tkinter import messagebox, filedialog
from dotenv import load_dotenv
import os
from PIL import Image, ImageDraw, ImageFont, ImageOps
from datetime import datetime, date
from settings import (
    IMAGE_WIDTH, IMAGE_HEIGHT, BACKGROUND_COLOR, FONTS, 
    LINE_SPACING, TEXT_COLOR, BUTTON_COLOR, EXPORT_FORMATS,
    TEMPLATES, TEMPLATE_PATHS, DEFAULT_FONT, TEXT_COLOR_DARK,
    BUTTON_STYLE
)

# Global Variables
current_weather_data = {}                       # Holds the most recent weather data for exporting
location_entries = []                           # List to hold city and state entry pairs   
input_elements = []                             # List to hold all input elements
root = None                                     # Main window
main_frame = None                               # Main frame for the GUI
result_frame = None                             # Frame to hold the result text box
preview_frame = None                            # Frame to hold the preview image
preview_canvas = None                           # Canvas for the preview image
preview_label = None                            # Label for the preview image
header_frame = None                             # Frame for the header
description_label = None                        # Label for the description
button_frame = None                             # Frame for the buttons

# Function to add hover effect to buttons
def add_hover_effect(button, hover_color="#c8a2c8", default_color="white"):
    # Add hover effect to buttons
    def on_enter(e):
        button.config(background=hover_color)
    def on_leave(e):
        button.config(background=default_color)
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)

# Loads environment variables and verifies required template images exist
def configure():
    # Load environment variables
    load_dotenv()

    # Verify template images exist
    for template in TEMPLATE_PATHS.values():
        if not os.path.exists(template):
            messagebox.showwarning("Template Missing", 
                                  f"Template image not found: {template}")

# Fetch weather data from OpenWeatherMap API
def fetch_weather_data(city_name, state_code, country_code="US"):
   # Construct API request URL
    api_key = os.getenv("API_KEY")
    if not api_key:
        messagebox.showerror("API Error", "OpenWeatherMap API key not configured")
        return None
    
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    query = f"{city_name},{state_code},{country_code}"
    complete_url = f"{base_url}appid={api_key}&q={query}&units=metric"
    
    # Make the API request
    try:
        response = requests.get(complete_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        messagebox.showerror("API Error", f"Failed to fetch weather data: {str(e)}")
        return None

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
        root.geometry("750x850") 
        
        result_box.pack(pady=10)

        # Create export buttons
        export_button_frame.pack(pady=5)

        #Format city name to uppercase first letter of each word
        formatted_city_name = city_name.title()
        #Format state code to uppercase
        formatted_state_code = state_code.upper()

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

# Function trigged by "Get Weather" button, which fetches and displays weather data for all locations
def get_weather():
    global current_weather_data

    if not location_entries:
        messagebox.showerror("Input Error", "Please add at least one location.")
        return

    toggle_input_visibility(show=False)         # Hide the input elements
    toggle_results_visibility(show=True)        # Show the results area

    # Clear previous results
    if hasattr(toggle_results_visibility, "results_created"):    
        result_box.delete("1.0", tk.END)
        current_weather_data = []

    for city_entry, state_entry, _ in location_entries:
        city_name = city_entry.get().strip()
        state_code = state_entry.get().strip().upper()

        if not city_name or not state_code:
            messagebox.showerror("Input Error", "Please fill in both city and state for all entries.")
            return

        try:
            data = fetch_weather_data(city_name, state_code)
            if data:
                # Process the weather data
                weather_info = process_weather_data(data)
                
                if weather_info:
                    # Accumulate and show multiple weather reports
                    display_weather(weather_info, city_name, state_code)
                    current_weather_data.append({
                    "city": city_name,
                    "state": state_code,
                    **weather_info
                })

                # Save the first valid one for exporting
                if not current_weather:
                    current_weather = {
                        "city": city_name,
                        "temp_c": weather_info['temp_celsius'],
                        "temp_f": weather_info['temp_fahrenheit'],
                        "pressure": weather_info['pressure'],
                        "humidity": weather_info['humidity'],
                        "description": weather_info['description']
                    }
            
        except requests.exceptions.RequestException as e:
            result_box.insert(tk.END, f"\nFailed to retrieve data for {city_name}, {state_code}:\n{e}\n", "bold")
    
    if current_weather_data:
        export_button_frame.pack(pady=10)
        root.geometry("800x900")

# Function to add a new location input row
def add_location_input(parent_frame=None):
    # Add a new location input row
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

# Function to create and export current weather data in the selected template
def create_weather_image(template_type="post"):
    # Create weather image using template
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

# Function to toggle visibility of input elements
def toggle_input_visibility(show=True):
    # Show or hide the input elements (description, location inputs, buttons)
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

# Function to toggle visibility of results
def toggle_results_visibility(show=True):
    # Show or hide the results and preview sections
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

# Function to reset input view to its initial state
def reset_input_view():
    global current_weather_data
    
    # Clear all input fields
    for widget in input_elements:
        if isinstance(widget, tk.Entry):
            widget.delete(0, tk.END)
    
    location_entries.clear()                                # Clear location entries
    current_weather_data = []                               # Clear current weather data        
    export_button_frame.pack_forget()                       # Hide export buttons 
    # add_location_input()                                    # Add a new location input row

# Function to initialize the GUI with enhanced styling
def init_gui():
    global root, location_frame, export_button_frame, main_frame, header_frame, description_label, button_frame
    
    root = tk.Tk()
    root.title("Weather Forecast Automator")
    root.configure(bg="#f0f8ff")  # Lighter background
    
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
    
    # Add initial location input
    add_location_input()

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

