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
    profile_window.configure(bg="#f5f5f5")

    profile_window.title("Your Profile")
    window_width = 500
    window_height = 700
    screen_width = profile_window.winfo_screenwidth()
    screen_height = profile_window.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    profile_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    profile_window.resizable(False, False)

    print(f"Current UID: {session_state.current_user_uid}")

    user_doc = db.collection("users").document(session_state.current_user_uid).get()
    user_data = user_doc.to_dict()

    if not user_data:
        messagebox.showerror("Error", "User profile could not be loaded.")
        profile_window.destroy()
        return

    display_name = f"{user_data.get("full_name", {}).get("first_name", "")} {user_data.get("full_name", {}).get("last_name", "")}"
    ttk.Label(profile_window, text=display_name, font=("Helvetica", 18, "bold")).pack(pady=10)

    # Placeholder profile icon
    icon_frame = ttk.Frame(profile_window)
    icon_frame.pack(pady=10)
    try:
        img = Image.open("Images/profile_image_placeholder.png").resize((100, 100))
        photo = ImageTk.PhotoImage(img)
        label = ttk.Label(icon_frame, image=photo)
        label.image = photo
        label.pack()
    except:
        ttk.Label(icon_frame, text="[No Profile Image]", font=("Helvetica", 12)).pack()

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

    for label, value in fields.items():
        row = ttk.Frame(profile_window)
        row.pack(fill=tk.X, pady=4, padx=20)
        ttk.Label(row, text=f"{label}:", width=15, anchor="w", font=("Helvetica", 11, "bold")).pack(side=tk.LEFT)
        ttk.Label(row, text=value, font=("Helvetica", 11)).pack(side=tk.LEFT)

    ttk.Button(profile_window, text="Edit Profile", command=lambda: [profile_window.destroy(), edit_profile()]).pack(pady=20)

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
        frame = ttk.Frame(edit_window)
        frame.pack(fill=tk.X, pady=5, padx=20)
        ttk.Label(frame, text=f"{label}:", width=15, anchor="w", font=("Helvetica", 11, "bold")).pack(side=tk.LEFT)
        ttk.Entry(frame, textvariable=var, font=("Helvetica", 11), width=30, show="*" if key == "new_password" else "").pack(side=tk.LEFT)

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

