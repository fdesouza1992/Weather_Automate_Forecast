import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from urllib.request import urlopen
from firebase_config import db, bucket
from firebase_admin import auth
import session_state
from PIL import Image, ImageTk, ImageOps
import ttkbootstrap as ttkb
import os
import ssl
from io import BytesIO
import random

def load_profile_image_from_url(url):
    try:
        url_with_buster = f"{url}?cache_buster={random.randint(1, 999999)}"
        context = ssl._create_unverified_context()
        with urlopen(url_with_buster, context=context) as response:
            img = Image.open(BytesIO(response.read()))
            img = ImageOps.exif_transpose(img)  # Handle orientation
            img = img.resize((125, 125), Image.LANCZOS)  # Resize to 125x125
            return img
    except Exception as e:
        print("Error loading image from URL:", e)
        img = Image.open("Images/profile_image_placeholder_white.png")
        img = img.resize((125, 125), Image.LANCZOS)  # Resize to 125x125
        return img

def view_profile():
    global main_frame, root

    profile_window = tk.Toplevel()
    profile_window.transient()
    profile_window.grab_set()
    profile_window.focus_set()

    # Fetch user data first 
    user_doc = db.collection("users").document(session_state.current_user_uid).get()
    user_data = user_doc.to_dict()

    if not user_data:
        messagebox.showerror("Error", "User profile could not be loaded.")
        profile_window.destroy()
        return

    title = f"{user_data.get('full_name', {}).get('first_name', '')} {user_data.get('full_name', {}).get('last_name', '')} Profile"
    profile_window.title(title)
    window_width = 550
    window_height = 800
    screen_width = profile_window.winfo_screenwidth()
    screen_height = profile_window.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    profile_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    profile_window.resizable(False, False)

    # Main container with purple background
    main_frame = ttk.Frame(
        profile_window, 
        padding=20, 
        bootstyle="primary")
    
    main_frame.pack(
        fill=tk.BOTH, 
        expand=True)

    # Profile Image
    img = load_profile_image_from_url(user_data.get("profile_image_url"))
    photo = ImageTk.PhotoImage(img)

    logo_label = ttk.Label(
        main_frame, 
        image=photo, 
        bootstyle="inverse-primary")
    
    logo_label.image = photo
    logo_label.pack(pady=10)

    # === Now safe to use user_data ===
    display_name = f"{user_data.get('full_name', {}).get('first_name', '')}'s Profile"
    display_name_label = ttk.Label(
        main_frame,
        text=display_name,
        font=("Helvetica", 24, "bold"),
        bootstyle="inverse-primary"
    )

    display_name_label.pack(pady=(0, 10))

#Separator
    separator = ttk.Separator(
        main_frame, 
        bootstyle="secondary")
    
    separator.pack(
        side=tk.TOP, 
        fill=tk.X, 
        padx=10, 
        pady=15)  

 # Container for grid layout
    grid_frame = ttk.Frame(
        main_frame, 
        bootstyle="primary")
    
    grid_frame.pack(
        side=tk.TOP, 
        fill=tk.BOTH, 
        expand=True, 
        padx=10)

    fields = {
        "First Name": user_data.get("full_name", {}).get("first_name", ""),
        "Last Name": user_data.get("full_name", {}).get("last_name", ""),
        "Email": user_data.get("email", ""),
        "Phone": user_data.get("phone", ""),
        "Street": user_data.get("address", {}).get("street", ""),
        "City": user_data.get("address", {}).get("city", ""),
        "State": user_data.get("address", {}).get("state", ""),
        "Zip Code": user_data.get("address", {}).get("zipCode", ""),
        "Country": user_data.get("address", {}).get("country", "")
    }

    for i, (label, value) in enumerate(fields.items()):
        # Label for field name
        field_name_label= ttk.Label(
            grid_frame, 
            text=f"{label}:", 
            width=15, 
            anchor="w",
            font=("bold"), 
            bootstyle="inverse-primary"
        )

        field_name_label.grid(
            row=i, 
            column=0, 
            sticky="w", 
            padx=(20, 20), 
            pady=10)

        # Label for field value
        field_value_label=ttk.Label(
            grid_frame, 
            text=value, 
            bootstyle="inverse-primary"
        )

        field_value_label.grid(
            row=i, 
            column=1, 
            sticky="w", 
            padx=(0, 20), 
            pady=10)

    # Create a frame specifically for the buttons
    button_frame = ttk.Frame(
        main_frame, 
        bootstyle="primary")
    
    button_frame.pack(pady=10)

    back_button = ttk.Button(
        button_frame, 
        text="<-Back to Home", 
        bootstyle="danger",
        command=lambda: [profile_window.destroy(),])
    
    back_button.pack(
        side=tk.LEFT, 
        padx=10)

    edit_profile_button = ttk.Button(
        button_frame, 
        text="Edit Profile", 
        bootstyle="success",
        command=lambda: [profile_window.destroy(), edit_profile()]) 
    
    edit_profile_button.pack(
        side=tk.LEFT, 
        padx=10)

def edit_profile():
    edit_window = tk.Toplevel()
    edit_window.transient()
    edit_window.grab_set()
    edit_window.focus_set()

    # Fetch user data first
    user_ref = db.collection("users").document(session_state.current_user_uid)
    user_doc = user_ref.get()
    user_data = user_doc.to_dict()

    if not user_data:
        messagebox.showerror("Error", "User profile could not be loaded.")
        edit_window.destroy()
        return

    title = f"Edit {user_data.get('full_name', {}).get('first_name', '')}'s Profile"
    edit_window.title(title)
    window_width = 550
    window_height = 800
    screen_width = edit_window.winfo_screenwidth()
    screen_height = edit_window.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    edit_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    edit_window.resizable(False, False)

    # Main container with purple background
    main_frame = ttk.Frame(
        edit_window, 
        padding=20, 
        bootstyle="primary")
    
    main_frame.pack(
        fill=tk.BOTH, 
        expand=True)

    # === Now safe to use user_data ===
    display_name = f"Edit Profile"

    display_name_label = ttk.Label(
        main_frame,
        text=display_name,
        font=("Helvetica", 24, "bold"),
        bootstyle="inverse-primary"
    )

    display_name_label.pack(pady=(0, 10))

    #Separator
    separator = ttk.Separator(
        main_frame, 
        bootstyle="secondary")
    
    separator.pack(
        side=tk.TOP, 
        fill=tk.X, 
        padx=10, 
        pady=10)
     
    # Function to upload new profile image
    def upload_new_image():
        file_path = filedialog.askopenfilename(
            title="Select Profile Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp *.gif")]
        )
        if not file_path:
            return

        try:
            # Resize locally in memory
            img = Image.open(file_path)
            img = ImageOps.exif_transpose(img)  # Handle orientation
            img = img.resize((125, 125), Image.LANCZOS)

            # Convert to BytesIO for upload
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            # Upload to Firebase Storage
            blob_path = f"profile_images/{session_state.current_user_uid}.png"
            blob = bucket.blob(blob_path)
            blob.upload_from_file(buffer, content_type="image/png")
            blob.make_public()

            # Save public URL to Firestore
            user_ref.update({"profile_image_url": blob.public_url})

            messagebox.showinfo("Success", "Profile image uploaded!")
            edit_window.destroy()
            view_profile()
        except Exception as e:
            messagebox.showerror("Upload Failed", str(e))

    # Load existing or placeholder image
    img = load_profile_image_from_url(user_data.get("profile_image_url"))
    photo = ImageTk.PhotoImage(img)

    logo_label = ttk.Label(
        main_frame, 
        image=photo, 
        bootstyle="inverse-primary", 
        cursor="hand2")
    
    logo_label.image = photo

    logo_label.bind(
        "<Button-1>", 
        lambda e: upload_new_image())
    
    logo_label.pack(pady=10)

    # Separator for photo section
    photo_separator = ttk.Separator(
        main_frame, 
        bootstyle="secondary")
    
    photo_separator.pack(
        side=tk.TOP, 
        fill=tk.X, 
        padx=10, 
        pady=10)

     # Container for grid layout
    grid_frame = ttk.Frame(
        main_frame, 
        bootstyle="primary")
    
    grid_frame.pack(
        side=tk.TOP, 
        fill=tk.BOTH, 
        expand=True, 
        padx=10)

    form_vars = {
        "first_name": tk.StringVar(value=user_data.get("full_name", {}).get("first_name", "")),
        "last_name": tk.StringVar(value=user_data.get("full_name", {}).get("last_name", "")),
        "phone": tk.StringVar(value=user_data.get("phone", "")),
        "street": tk.StringVar(value=user_data.get("address", {}).get("street", "")),
        "city": tk.StringVar(value=user_data.get("address", {}).get("city", "")),
        "state": tk.StringVar(value=user_data.get("address", {}).get("state", "")),
        "zipCode": tk.StringVar(value=user_data.get("address", {}).get("zipCode", "")),
        "country": tk.StringVar(value=user_data.get("address", {}).get("country", "")),
        "new_password": tk.StringVar()
    }

    # Create labels and entry fields for each form variable
    for i, (key, var) in enumerate(form_vars.items()):
        # Determine label text
        label_text = "New Password" if key == "new_password" else key.replace("_", " ").capitalize()
        
        # Create and place the label
        field_label = ttk.Label(
            grid_frame,
            text=f"{label_text}:",
            width=15,
            anchor="w",
            font=("bold"),
            bootstyle="inverse-primary"
        )

        field_label.grid(
            row=i, 
            column=0, 
            sticky="w", 
            padx=(10, 15), 
            pady=8)

        # Create and place the entry field
        field_entry = ttkb.Entry(
            grid_frame,
            textvariable=var,
            width=30,
            bootstyle="primary",
            show="*" if key == "new_password" else ""
        )

        field_entry.grid(
            row=i, 
            column=1, 
            sticky="w", 
            padx=(0, 15), 
            pady=8)

    def save_changes():
        try:
            updates = {
                "full_name": {
                    "first_name": form_vars["first_name"].get().strip(),
                    "last_name": form_vars["last_name"].get().strip()
                },
                "phone": form_vars["phone"].get().strip(),
                "address": {
                    "street": form_vars["street"].get().strip(),
                    "city": form_vars["city"].get().strip(),
                    "state": form_vars["state"].get().strip(),
                    "zipCode": form_vars["zipCode"].get().strip(),
                    "country": form_vars["country"].get().strip(),
                }
            }
            user_ref.update(updates)

            new_pass = form_vars["new_password"].get().strip()
            if new_pass:
                auth.update_user(session_state.current_user_uid, password=new_pass)

            messagebox.showinfo("Success", "Profile updated successfully!")
            edit_window.destroy()
            view_profile()
        except Exception as e:
            messagebox.showerror("Update Error", str(e))
    
    # Create a frame specifically for the buttons
    button_frame = ttk.Frame(
        main_frame, 
        bootstyle="primary")
    
    button_frame.pack(pady=10)

    cancel_button = ttk.Button(
        button_frame, 
        text="Cancel", 
        bootstyle="danger",
        command=lambda: [edit_window.destroy(), view_profile()])
    
    cancel_button.pack(
        side=tk.LEFT, 
        padx=10)

    save_button = ttk.Button(
        button_frame, 
        bootstyle="success", 
        text="Save", 
        command=save_changes)
    
    save_button.pack(
        side=tk.LEFT, 
        padx=10)
