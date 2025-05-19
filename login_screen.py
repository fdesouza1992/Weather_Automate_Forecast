import tkinter as tk
from tkinter import ttk, messagebox
from ttkbootstrap import Style, Window
from firebase_admin import auth
from firebase_config import db
from auth_controller import create_user
import re
from PIL import Image, ImageTk

class LoginScreen:
    def __init__(self, master, on_login_success):
        self.master = master
        self.on_login_success = on_login_success
        self.style = Style(theme='pulse')
        
        # Main container frame
        self.main_frame = ttk.Frame(master, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # App logo
        try:
            img = Image.open("Images/FelipeWeatherAppLogo.png").resize((150, 150))
            self.logo = ImageTk.PhotoImage(img)
            ttk.Label(self.main_frame, image=self.logo).pack(side=tk.TOP, pady=10)
        except Exception as e:
            print(f"Error loading logo: {e}")
        
        # Title
        ttk.Label(
            self.main_frame, 
            text="Weather Forecast Generator",
            font=("Helvetica", 28, "bold"),
            bootstyle="primary"
        ).pack(side=tk.TOP, pady=5)
        
        # Separator
        ttk.Separator(self.main_frame).pack(fill=tk.X, pady=10)
        
        # Notebook for Login/Register tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # Login Frame
        self.login_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.login_frame, text="Login")
        self._setup_login_form()
        
        # Register Frame
        self.register_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.register_frame, text="Register")
        self._setup_register_form()
    
    def _setup_login_form(self):
        # Email
        ttk.Label(self.login_frame, text="Email:").grid(row=0, column=0, sticky="w", pady=5)
        self.login_email = ttk.Entry(self.login_frame, width=30)
        self.login_email.grid(row=0, column=1, pady=5, padx=5)
        
        # Password
        ttk.Label(self.login_frame, text="Password:").grid(row=1, column=0, sticky="w", pady=5)
        self.login_password = ttk.Entry(self.login_frame, width=30, show="*")
        self.login_password.grid(row=1, column=1, pady=5, padx=5)
        
        # Login Button
        login_btn = ttk.Button(
            self.login_frame, 
            text="Login", 
            command=self._handle_login,
            bootstyle="success"
        )
        login_btn.grid(row=2, column=0, columnspan=2, pady=20)
        
        # Bind Enter key to login
        self.login_password.bind('<Return>', lambda e: self._handle_login())
    
    def _setup_register_form(self):
        # Name
        ttk.Label(self.register_frame, text="Full Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.reg_name = ttk.Entry(self.register_frame, width=30)
        self.reg_name.grid(row=0, column=1, pady=5, padx=5)
        
        # Email
        ttk.Label(self.register_frame, text="Email:").grid(row=1, column=0, sticky="w", pady=5)
        self.reg_email = ttk.Entry(self.register_frame, width=30)
        self.reg_email.grid(row=1, column=1, pady=5, padx=5)
        
        # Password
        ttk.Label(self.register_frame, text="Password:").grid(row=2, column=0, sticky="w", pady=5)
        self.reg_password = ttk.Entry(self.register_frame, width=30, show="*")
        self.reg_password.grid(row=2, column=1, pady=5, padx=5)
        
        # Confirm Password
        ttk.Label(self.register_frame, text="Confirm Password:").grid(row=3, column=0, sticky="w", pady=5)
        self.reg_confirm = ttk.Entry(self.register_frame, width=30, show="*")
        self.reg_confirm.grid(row=3, column=1, pady=5, padx=5)
        
        # Phone (optional)
        ttk.Label(self.register_frame, text="Phone (optional):").grid(row=4, column=0, sticky="w", pady=5)
        self.reg_phone = ttk.Entry(self.register_frame, width=30)
        self.reg_phone.grid(row=4, column=1, pady=5, padx=5)
        
        # Register Button
        register_btn = ttk.Button(
            self.register_frame, 
            text="Register", 
            command=self._handle_register,
            bootstyle="primary"
        )
        register_btn.grid(row=5, column=0, columnspan=2, pady=20)
        
        # Bind Enter key to register
        self.reg_confirm.bind('<Return>', lambda e: self._handle_register())
    
    def _handle_login(self):
        email = self.login_email.get().strip()
        password = self.login_password.get().strip()
        
        if not email or not password:
            messagebox.showerror("Error", "Please enter both email and password")
            return
        
        try:
            # Verify user credentials with Firebase
            user = auth.get_user_by_email(email)
            
            # In a real app, you would verify the password here
            # For Firebase, you'd typically use Firebase Auth SDK on client side
            # For this example, we'll just check if the user exists
            
            # Get additional user data from Firestore
            user_ref = db.collection('users').document(user.uid)
            user_data = user_ref.get().to_dict()
            
            if user_data:
                messagebox.showinfo("Success", f"Welcome back, {user_data.get('name', 'User')}!")
                self.on_login_success(user.uid, user_data)
            else:
                messagebox.showerror("Error", "User data not found")
                
        except auth.UserNotFoundError:
            messagebox.showerror("Error", "User not found. Please register.")
        except Exception as e:
            messagebox.showerror("Error", f"Login failed: {str(e)}")
    
    def _handle_register(self):
        name = self.reg_name.get().strip()
        email = self.reg_email.get().strip()
        password = self.reg_password.get().strip()
        confirm = self.reg_confirm.get().strip()
        phone = self.reg_phone.get().strip()
        
        # Validation
        if not all([name, email, password, confirm]):
            messagebox.showerror("Error", "Please fill all required fields")
            return
            
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match")
            return
            
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters")
            return
            
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showerror("Error", "Invalid email format")
            return
            
        try:
            # Create user in Firebase Auth
            uid = create_user(
                email=email,
                password=password,
                display_name=name,
                phone_number=phone if phone else None
            )
            
            if uid:
                messagebox.showinfo("Success", "Registration successful! Please login.")
                self.notebook.select(0)  # Switch to login tab
                self.login_email.delete(0, tk.END)
                self.login_email.insert(0, email)
                self.login_password.focus()
                
        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {str(e)}")