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
from settings import IMAGE_WIDTH, IMAGE_HEIGHT, BACKGROUND_COLOR, FONTS, LINE_SPACING, TEXT_COLOR, BUTTON_COLOR, EXPORT_FORMATS

current_weather = {}

# Function to add hover effect to buttons
def add_hover_effect(button, hover_bg="#cce7ff", default_bg="white", hover_fg="black", default_fg="black"):
    def on_enter(e):
        button.configure(background=hover_bg, foreground=hover_fg)
    def on_leave(e):
        button.configure(background=default_bg, foreground=default_fg)

    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)

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

        # Create export buttons
        export_button_frame.pack(pady=5)

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

            # Track current weather data for export buttons
            global current_weather
            current_weather = {
               "city": city_name,
                "temp_c": weather_info['temp_celsius'],
                "temp_f": weather_info['temp_fahrenheit'],
                "pressure": weather_info['pressure'],
                "humidity": weather_info['humidity'],
                "description": weather_info['description']
            }
        else:
            messagebox.showerror("Error", "City Not Found. Please enter a valid city name.")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to retrieve data:\n{e}")

# Function for GUI initialization
def init_gui():
    # Initialize global variables
    global root, state_entry, city_entry, result_box, export_story_button, export_post_button, export_button_frame

    # Create a GUI window
    root = tk.Tk()
    root.title("Weather App")
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
                                    bg="white",
                                    fg="black",
                                    activebackground="white",
                                    activeforeground="black",
                                    relief=tk.GROOVE,
                                    highlightthickness=0,
                                    bd=2,
                                    padx=10,
                                    pady=5,
                                    command=get_weather)
    
    # Add hover effect to the button
    add_hover_effect(get_weather_button, hover_bg="#c8a2c8", hover_fg="#4b0082")
    
    # Frame to hold export buttons side-by-side
    export_button_frame = tk.Frame(root, bg="#add8e6")

    # Create a button to export weather data
    export_story_button = tk.Button(export_button_frame,
                                text="Export as Story",
                                font=("helvetica", 12, "bold"),
                                bg="white",
                                fg="black",
                                activebackground="white",
                                activeforeground="black",
                                relief=tk.GROOVE,
                                highlightthickness=0,
                                bd=2,
                                padx=10,
                                pady=5,
                                command=lambda: export_current_weather("story"))
    
    # Add hover effect to the button
    add_hover_effect(export_story_button, hover_bg="#c8a2c8", hover_fg="#4b0082")

    # Create a button to export weather data
    export_post_button = tk.Button(export_button_frame,
                               text="Export as Post",
                               font=("helvetica", 12, "bold"),
                               bg="white",
                               fg="black",
                               activebackground="white",
                               activeforeground="black",
                               relief=tk.RAISED,
                               highlightthickness=0,
                               bd=2,
                               padx=10,
                               pady=5,
                               command=lambda: export_current_weather("post"))
    
    # Add hover effect to the button
    add_hover_effect(export_post_button, hover_bg="#c8a2c8", hover_fg="#4b0082")

    # Side-by-side layout inside the frame
    export_story_button.pack(side=tk.LEFT, padx=10)
    export_post_button.pack(side=tk.RIGHT, padx=10)

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

    # Center the window on the screen
    window_width = 500
    window_height = 350

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))

    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    return root

# Function to save the result as an image
def save_weather_image(city, temp_c, temp_f, pressure, humidity, description):
    img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color=BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)

    # Load fonts
    def load_font(size_tuple):
        try:
            return ImageFont.truetype("Helvetica", size_tuple[1])
        except IOError:
            return ImageFont.load_default()

    font_title = load_font(FONTS["title"])
    font_bold = load_font(FONTS["bold"])
    font_regular = load_font(FONTS["regular"])

    # Title
    title = f"Weather for {city.title()}"
    title_width = draw.textlength(title, font=font_title)
    draw.text(((IMAGE_WIDTH - title_width) / 2, 30), title, fill=TEXT_COLOR, font=font_title)

    # Data lines
    y_start = 100

    def draw_label_value(label, value, y):
        label_width = draw.textlength(label, font=font_bold)
        value_width = draw.textlength(value, font=font_regular)
        total_width = label_width + value_width
        x_start = (IMAGE_WIDTH - total_width) / 2

        draw.text((x_start, y), label, fill=TEXT_COLOR, font=font_bold)
        draw.text((x_start + label_width, y), value, fill=TEXT_COLOR, font=font_regular)

    draw_label_value("Temperature: ", f"{temp_c}°C / {temp_f}°F", y_start)
    draw_label_value("Pressure: ", f"{pressure} hPa", y_start + LINE_SPACING)
    draw_label_value("Humidity: ", f"{humidity}%", y_start + LINE_SPACING * 2)
    draw_label_value("Description: ", description, y_start + LINE_SPACING * 3)

    # Save image
    filename = f"{city}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, filename)
    img.save(full_path)
    print(f"Weather image saved as: {full_path}")

# Function to handle the export button
def export_weather_image(format_type, city, temp_c, temp_f, pressure, humidity, description):
    fmt = EXPORT_FORMATS[format_type]
    width = fmt["width"]
    height = fmt["height"]
    suffix = fmt["filename_suffix"]

    img = Image.new('RGB', (width, height), color=BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)

    # Load fonts
    def load_font(size_tuple):
        try:
            return ImageFont.truetype("Helvetica", size_tuple[1])
        except IOError:
            return ImageFont.load_default()

    font_title = load_font(FONTS["title"])
    font_bold = load_font(FONTS["bold"])
    font_regular = load_font(FONTS["regular"])

    # Title
    title = f"Weather for {city.title()}"
    title_width = draw.textlength(title, font=font_title)
    draw.text(((width - title_width) / 2, 60), title, fill=TEXT_COLOR, font=font_title)

    # Weather Details
    y_start = 200
    spacing = 80  # More spacing for tall formats

    def draw_label_value(label, value, y):
        label_width = draw.textlength(label, font=font_bold)
        value_width = draw.textlength(value, font=font_regular)
        total_width = label_width + value_width
        x_start = (width - total_width) / 2

        draw.text((x_start, y), label, fill=TEXT_COLOR, font=font_bold)
        draw.text((x_start + label_width, y), value, fill=TEXT_COLOR, font=font_regular)

    draw_label_value("Temperature: ", f"{temp_c}°C / {temp_f}°F", y_start)
    draw_label_value("Pressure: ", f"{pressure} hPa", y_start + spacing)
    draw_label_value("Humidity: ", f"{humidity}%", y_start + spacing * 2)
    draw_label_value("Description: ", description, y_start + spacing * 3)

    filename = f"{city}{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, filename)
    img.save(full_path)
    print(f"{format_type.capitalize()} image saved as: {full_path}")
    messagebox.showinfo("Export Success", f"{format_type.capitalize()} image saved successfully.")

# Helper function to handle the export button clicks
def export_current_weather(format_type):
    if not current_weather:
        messagebox.showerror("Export Error", "No weather data available. Fetch weather first.")
        return
    export_weather_image(format_type,
                    current_weather["city"],
                    current_weather["temp_c"],
                    current_weather["temp_f"],
                    current_weather["pressure"],
                    current_weather["humidity"],
                    current_weather["description"])

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

