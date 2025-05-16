import tkinter as tk

# Image Settings
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1080
BACKGROUND_COLOR = "#add8e6"
TEXT_COLOR = "#FFFFFF"  # White text for dark templates
TEXT_COLOR_DARK = "#2c3e50"  # Black text for light templates

# Font Settings
DEFAULT_FONT = "Inter.ttf"  # Should be in your project directory
FONTS = {
    "title": ("Helvetica", 28),
    "bold": ("Helvetica", 22),
    "regular": ("Helvetica", 18)
}

# Spacing
LINE_SPACING = 40

# Button Colors
BUTTON_COLOR = "#c9a0dc"

# Button style configuration
BUTTON_STYLE = {
    "bg": "white",
    "fg": "black",
    "font": ("Helvetica", 12),
    "relief": tk.RAISED,
    "bd": 2,
    "padx": 10,
    "pady": 5
}

# Export Formats
EXPORT_FORMATS = {
    "story": {
        "width": 1080,
        "height": 1920,
        "filename_suffix": "_story"
    },
    "post": {
        "width": 1080,
        "height": 1080,
        "filename_suffix": "_post"
    }
}

# Template Configuration
TEMPLATES = {
    "post": {
        "font_sizes": {
            "title": 65,
            "large": 40,
            "medium": 30
        },
        "title_position": (115, 45),
        "date_position": (115, 145),
        "city_position": [
            (145, 300),  # City 1 position (x,y)
            (145, 430),  # City 2
            (145, 555),  # City 3
            (145, 690),  # City 4
            (145, 825)   # City 5
        ],
        "temp_position": [
            (620, 300),
            (620, 430),
            (620, 555),
            (620, 690),
            (620, 825)
        ],
        "humidity_position": [
            (840, 300),
            (840, 430),
            (840, 555),
            (840, 690),
            (840, 825)
        ]
    },
    "story": {
        "font_sizes": {
            "title": 65,
            "large": 40,
            "medium": 30
        },
        "title_position": (100, 165),
        "date_position": (100, 330),
        "city_position": [
            (115, 610),
            (115, 795),
            (115, 990),
            (115, 1165),
            (115, 1365)
        ],
        "temp_position": [
            (635, 610),
            (635, 795),
            (635, 990),
            (635, 1165),
            (635, 1365)
        ],
        "humidity_position": [
            (900, 610),
            (900, 795),
            (900, 990),
            (900, 1165),
            (900, 1365)
        ]
    }
}

# Paths to template images
TEMPLATE_PATHS = {
    "post": "post_template.png",  # Should be 1080x1080
    "story": "story_template.png"  # Should be 1080x1920
}