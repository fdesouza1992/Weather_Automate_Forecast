import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from ttkbootstrap import Style, Window
from firebase_admin import auth
from firebase_config import db
from auth_controller import create_user, verify_password
import re
from PIL import Image, ImageTk

image_references = {}

class LoginScreen:
    def __init__(self, master, on_login_success):
        self.master = master
        self.on_login_success = on_login_success
        self.style = Style(theme='pulse')
        
        # Main container frame
        self.main_frame = ttk.Frame(master, padding="20", bootstyle="primary")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # App logo
        try:
            icon_path = "Images/FelipeWeatherAppLogo.png"
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                img = img.resize((32, 32), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                image_references['icon'] = photo  # Prevent GC
                self.master.iconphoto(True, photo)
        except Exception as e:
            print(f"Could not load window icon: {e}")


        try:
            img = Image.open("Images/FelipeWeatherAppLogo.png").resize((150, 150))
            self.logo = ImageTk.PhotoImage(img)
            logo_label=ttk.Label(
                self.main_frame, 
                image=self.logo)
            logo_label.pack(side=tk.TOP, pady=10)
        except Exception as e:
            print(f"Error loading logo: {e}")
        
        # Title
        title_label = ttk.Label(
            self.main_frame, 
            text="Weather Forecast Generator",
            font=("Helvetica", 28, "bold"),
            bootstyle="inverse-primary"
        )
        title_label.pack(side=tk.TOP, pady=5)
        
        # Separator
        separator = ttk.Separator(self.main_frame)
        separator.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Notebook for Login/Register tabs
        self.notebook = ttk.Notebook(self.main_frame, bootstyle="primary")
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # Login Frame
        self.login_frame = ttk.Frame(
            self.notebook, 
            padding=10, 
            bootstyle="primary")
        self.notebook.add(self.login_frame, text="Login")
        self._setup_login_form()
        
        # Register Frame
        self.register_frame = ttk.Frame(
            self.notebook, 
            padding=10, 
            bootstyle="primary")
        self.notebook.add(self.register_frame, text="Register")
        self._setup_register_form()
    
    def _setup_login_form(self):
        # Email
        email_label = ttk.Label(
            self.login_frame, 
            bootstyle="inverse-primary", 
            text="Email:")
        email_label.grid(row=0, column=0, sticky="w", pady=5, padx=10)
        
        self.login_email = ttk.Entry(
            self.login_frame, 
            width=30, 
            bootstyle="primary")
        self.login_email.grid(row=0, column=1, pady=15, padx=15)
        
        # Password
        password_label = ttk.Label(
            self.login_frame, 
            bootstyle="inverse-primary", 
            text="Password:")
        password_label.grid(row=1, column=0, sticky="w", pady=5, padx=10)
        
        self.login_password = ttk.Entry(
            self.login_frame, 
            bootstyle="primary", 
            width=30, 
            show="*")
        self.login_password.grid(row=1, column=1, pady=15, padx=15)
        
        # Login Button
        login_btn = ttk.Button(
            self.login_frame, 
            text="Login", 
            command=self._handle_login,
            bootstyle="success"
        )
        login_btn.grid(row=2, column=0, columnspan=3, pady=20)
        
        # Bind Enter key to login
        self.login_password.bind('<Return>', lambda e: self._handle_login())

        # Forgot Password Link
        forgot_password = ttk.Label(
            self.login_frame,
            text="Forgot Password?",
            #foreground="blue",
            cursor="hand2",
            font=("underline"),
            bootstyle="inverse-info"
        )
        forgot_password.grid(row=2, column=1, sticky="e", padx=5)
        forgot_password.bind("<Button-1>", lambda e: self._handle_password_reset())

    def _setup_register_form(self):
        # First Name
        first_name_label = ttk.Label(
            self.register_frame, 
            bootstyle="inverse-primary", 
            text="First Name:")
        first_name_label.grid(row=0, column=0, sticky="w", pady=5)
        
        self.reg_first_name = ttk.Entry(
            self.register_frame, 
            bootstyle="primary", 
            width=30)
        self.reg_first_name.grid(row=0, column=1, pady=5, padx=5)
        
        # Last Name
        last_name_label = ttk.Label(
            self.register_frame, 
            bootstyle="inverse-primary", 
            text="Last Name:")
        last_name_label.grid(row=1, column=0, sticky="w", pady=5)
        
        self.reg_last_name = ttk.Entry(
            self.register_frame, 
            bootstyle="primary", 
            width=30)
        self.reg_last_name.grid(row=1, column=1, pady=5, padx=5)
        
        # Email
        email_label = ttk.Label(
            self.register_frame, 
            bootstyle="inverse-primary", 
            text="Email:")
        email_label.grid(row=2, column=0, sticky="w", pady=5)
        
        self.reg_email = ttk.Entry(
            self.register_frame, 
            bootstyle="primary", 
            width=30)
        self.reg_email.grid(row=2, column=1, pady=5, padx=5)
        
        # Password
        password_label=ttk.Label(
            self.register_frame, 
            bootstyle="inverse-primary", 
            text="Password:")
        password_label.grid(row=3, column=0, sticky="w", pady=5)
        
        self.reg_password = ttk.Entry(
            self.register_frame, 
            bootstyle="primary", 
            width=30, 
            show="*")
        self.reg_password.grid(row=3, column=1, pady=5, padx=5)
        
        # Confirm Password
        confirm_password_label=ttk.Label(
            self.register_frame, 
            bootstyle="inverse-primary", 
            text="Confirm Password:")
        confirm_password_label.grid(row=4, column=0, sticky="w", pady=5)
        
        self.reg_confirm = ttk.Entry(
            self.register_frame, 
            bootstyle="primary", 
            width=30, 
            show="*")
        self.reg_confirm.grid(row=4, column=1, pady=5, padx=5)
        
        # Phone (optional)
        phone_label = ttk.Label(
            self.register_frame, 
            bootstyle="inverse-primary", 
            text="Phone (optional):")
        phone_label.grid(row=5, column=0, sticky="w", pady=5)

        self.reg_phone = ttk.Entry(
            self.register_frame, 
            bootstyle="primary", 
            width=30)
        self.reg_phone.grid(row=5, column=1, pady=5, padx=5)
        
        # Register Button
        register_btn = ttk.Button(
            self.register_frame, 
            text="Register", 
            command=self._handle_register,
            bootstyle="success"
        )
        register_btn.grid(row=6, column=0, columnspan=2, pady=20)
        
        # Bind Enter key to register
        self.reg_confirm.bind('<Return>', lambda e: self._handle_register())
    
    def _handle_login(self):
        email = self.login_email.get().strip()
        password = self.login_password.get().strip()
        
        if not email or not password:
            messagebox.showerror("Error", "Please enter both email and password")
            return
        
        try:
            uid, error_msg = verify_password(email, password)
            
            if error_msg:
                # Handle specific Firebase errors
                if "INVALID_LOGIN_CREDENTIALS" in error_msg:
                    error_msg = "Invalid email or password"
                elif "TOO_MANY_ATTEMPTS" in error_msg:
                    error_msg = "Too many attempts. Try again later"
                    
                messagebox.showerror("Login Error", error_msg)
                return
                
            # Get user data from Firestore - CORRECTED VERSION
            user_ref = db.collection('users').document(uid)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                 # Construct full name from first and last name
                full_name = ""
                if 'full_name' in user_data:
                    first_name = user_data['full_name'].get('first_name', '')
                    last_name = user_data['full_name'].get('last_name', '')
                    full_name = f"{first_name} {last_name}".strip()
                
                messagebox.showinfo("Success", f"Welcome back: \n{full_name or 'User'}!")
                self.on_login_success(uid, user_data)
            else:
                messagebox.showerror("Error", "User data not found")
                
        except Exception as e:
            messagebox.showerror("Error", f"Login failed: {str(e)}")
    
    # Handles password reset
    def _handle_password_reset(self):
        reset_win = tk.Toplevel(self.master)
        reset_win.title("Reset Password")
        reset_win.transient(self.master)
        reset_win.grab_set()
        reset_win.focus_set()

        window_width = 400
        window_height = 270
        screen_width = reset_win.winfo_screenwidth()
        screen_height = reset_win.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        reset_win.geometry(f"{window_width}x{window_height}+{x}+{y}")
        reset_win.resizable(False, False)

        # App Header
        main_frame = ttk.Frame(
            reset_win, 
            bootstyle="primary")
        
        main_frame.pack(
            fill=tk.X, 
            pady=(5, 0))

        # App logo
        try:
            logo_path = "Images/FelipeWeatherAppLogo.png"
            if os.path.exists(logo_path):
                img = Image.open(logo_path).resize((75, 75))
                logo_photo = ImageTk.PhotoImage(img)
                image_references['reset_logo'] = logo_photo  # Prevent GC
                logo_label = ttk.Label(main_frame, image=logo_photo)
                logo_label.pack(pady=10)
        except Exception as e:
            print(f"Could not load logo: {e}")

        reset_label=ttk.Label(
            main_frame, 
            text="Enter your registered email:",
            font=("Helvetica", 16, "bold"), 
            bootstyle="inverse-primary")
        reset_label.pack(pady=(30, 5))

        email_entry = ttk.Entry(
            main_frame, 
            width=35)
        email_entry.pack(pady=5)

        btn_frame = ttk.Frame(
            main_frame, 
            bootstyle="primary")
        btn_frame.pack(pady=20)

        def send_reset():
            email = email_entry.get().strip()
            if not email:
                messagebox.showerror("Error", "Please enter your email")
                return

            from auth_controller import send_password_reset_email_rest
            success, error = send_password_reset_email_rest(email)

            if success:
                messagebox.showinfo("Reset Email Sent", f"A reset email has been sent to:\n{email}")
                reset_win.destroy()
            else:
                messagebox.showerror("Reset Failed", f"Error: {error}")

        send_email_button=ttk.Button(
            btn_frame, 
            text="Send Reset Email", 
            command=send_reset, 
            bootstyle="success")
        send_email_button.pack(side=tk.LEFT, padx=10)

        cancel_button = ttk.Button(
            btn_frame, 
            text="Cancel", 
            command=reset_win.destroy, 
            bootstyle="danger")
        cancel_button.pack(side=tk.LEFT, padx=10)



    def _handle_register(self):
        first_name = self.reg_first_name.get().strip()
        last_name = self.reg_last_name.get().strip()
        email = self.reg_email.get().strip()
        password = self.reg_password.get().strip()
        confirm = self.reg_confirm.get().strip()
        phone = self.reg_phone.get().strip()
        
        # Validation
        if not all([first_name, last_name, email, password, confirm]):
            messagebox.showerror("Error", "Please fill all required fields")
            return
            
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match")
            return
            
        if len(password) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters")
            return
            
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showerror("Error", "Invalid email format")
            return
            
        try:
            # Create user in Firebase Auth
            display_name = f"{first_name} {last_name}"
            uid = create_user(
                email=email,
                password=password,
                display_name=display_name,
                phone_number=phone if phone else None
            )
            
            if uid:
                # Store user data in Firestore with full_name structure
                user_data = {
                    'full_name': {
                        'first_name': first_name,
                        'last_name': last_name
                    },
                    'email': email,
                    'phone': phone if phone else None,
                    'password': password,  # Note: Storing passwords in Firestore is not recommended
                    'address': {
                        'street': '',
                        'city': '',
                        'state': '',
                        'country': '',
                        'zipCode': ''
                    },
                    'favorite_cities': [],
                    'friends': [],
                    'previously_used_password': None,
                    'password_change_date': None,
                }
                
                # Save to Firestore
                db.collection('users').document(uid).set(user_data)

                messagebox.showinfo("Success", "Registration successful! Please login.")
                self.notebook.select(0)  # Switch to login tab
                self.login_email.delete(0, tk.END)
                self.login_email.insert(0, email)
                self.login_password.focus()
                
        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {str(e)}")
    