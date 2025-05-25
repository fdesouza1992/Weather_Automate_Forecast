import tkinter as tk
from tkinter import ttk, messagebox
from firebase_config import db
from firebase_admin import auth
import session_state
from PIL import Image, ImageTk

def view_profile():
    global main_frame, root

    profile_window = tk.Toplevel()
    profile_window.transient()
    profile_window.grab_set()
    profile_window.focus_set()

    # === Fetch user data FIRST ===
    user_doc = db.collection("users").document(session_state.current_user_uid).get()
    user_data = user_doc.to_dict()

    if not user_data:
        messagebox.showerror("Error", "User profile could not be loaded.")
        profile_window.destroy()
        return

    title = f"{user_data.get('full_name', {}).get('first_name', '')} {user_data.get('full_name', {}).get('last_name', '')} Profile"
    profile_window.title(title)
    window_width = 500
    window_height = 700
    screen_width = profile_window.winfo_screenwidth()
    screen_height = profile_window.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    profile_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    profile_window.resizable(False, False)

    # Main container with purple background
    main_frame = ttk.Frame(profile_window, padding=20, bootstyle="primary")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # === Profile Image ===
    try:
        img = Image.open("Images/profile_image_placeholder_white.png").resize((100, 100))
        photo = ImageTk.PhotoImage(img)
        logo_label = ttk.Label(main_frame, image=photo, bootstyle="inverse-primary")
        logo_label.image = photo
        logo_label.pack(pady=10)
    except:
        ttk.Label(main_frame, text="[No Profile Image]", bootstyle="inverse-primary").pack(pady=10)

    # === Now safe to use user_data ===
    display_name = f"{user_data.get('full_name', {}).get('first_name', '')}'s Profile"
    ttk.Label(
        main_frame,
        text=display_name,
        font=("Helvetica", 20, "bold"),
        bootstyle="inverse-primary"
    ).pack(pady=(0, 10))

#Separator
    separator = ttk.Separator(main_frame, bootstyle="secondary")
    separator.pack(side=tk.TOP, fill=tk.X, padx=10, pady=15)  

 # Container for grid layout
    grid_frame = ttk.Frame(main_frame, bootstyle="primary")
    grid_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10)

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
        field_name_label.grid(row=i, column=0, sticky="w", padx=(20, 20), pady=10)

        # Label for field value
        field_value_label=ttk.Label(
            grid_frame, 
            text=value, 
            bootstyle="inverse-primary"
        )
        field_value_label.grid(row=i, column=1, sticky="w", padx=(0, 20), pady=10)

    edit_profile_button = ttk.Button(
        main_frame, 
        text="Edit Profile", 
        bootstyle="success",
        command=lambda: [profile_window.destroy(), edit_profile()]) 
    edit_profile_button.pack(pady=20)

def edit_profile():
    edit_window = tk.Toplevel()
    edit_window.title("Edit Profile")
    window_width = 500
    window_height = 700
    screen_width = edit_window.winfo_screenwidth()
    screen_height = edit_window.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    edit_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    edit_window.resizable(False, False)

    user_ref = db.collection("users").document(session_state.current_user_uid)
    user_doc = user_ref.get()
    user_data = user_doc.to_dict()

    if not user_data:
        messagebox.showerror("Error", "User profile could not be loaded.")
        edit_window.destroy()
        return

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

    ttk.Label(edit_window, text="Edit Profile", font=("Helvetica", 18, "bold")).pack(pady=10)

    for key, var in form_vars.items():
        if key == "new_password":
            label = "New Password"
        else:
            label = key.replace("_", " ").capitalize()
        frame = ttk.Frame(edit_window, bootstyle="primary")
        frame.pack(fill=tk.X, pady=5, padx=20)
        ttk.Label(frame, text=f"{label}:", width=15, anchor="w", bootstyle="primary", font=("Helvetica", 11, "bold")).pack(side=tk.LEFT)
        ttk.Entry(frame, textvariable=var, font=("Helvetica", 11), bootstyle="primary", width=30, show="*" if key == "new_password" else "").pack(side=tk.LEFT)

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
        except Exception as e:
            messagebox.showerror("Update Error", str(e))

    ttk.Button(edit_window, text="Save Changes", command=save_changes).pack(pady=20)

