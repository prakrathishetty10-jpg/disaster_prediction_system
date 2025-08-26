from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
import pandas as pd
import pymysql
from geopy.geocoders import Nominatim
import pygame
import requests
import json
from datetime import datetime, timedelta
import threading
import time
import math
import os

# Database connection helpers
con = None
conn = None

def _connect(port: int | None = None, with_db: bool = True):
    global con, conn
    params = {
        'host': 'localhost',
        'user': 'root',
        'password': 'root',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.Cursor,
        'autocommit': True,
    }
    if port is not None:
        params['port'] = port
    else:
        params['port'] = 3307
    if with_db:
        params['database'] = 'alpha'
    con = pymysql.connect(**params)
    conn = con.cursor()

def _init_schema():
    """Create database/tables if missing."""
    global con, conn
    try:
        # Ensure DB exists
        tmp = con.cursor()
        tmp.execute("CREATE DATABASE IF NOT EXISTS alpha CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        tmp.execute("USE alpha")
        # Users table
        tmp.execute(
            """
            CREATE TABLE IF NOT EXISTS users_details (
              id INT PRIMARY KEY AUTO_INCREMENT,
              name VARCHAR(255) NOT NULL,
              username VARCHAR(255) NOT NULL UNIQUE,
              pass VARCHAR(255) NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        # Earthquake history table
        tmp.execute(
            """
            CREATE TABLE IF NOT EXISTS eq_history (
              id INT PRIMARY KEY AUTO_INCREMENT,
              user_id INT,
              latitude DOUBLE,
              longitude DOUBLE,
              magnitude DOUBLE,
              location TEXT,
              status VARCHAR(64),
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              INDEX(user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
    except Exception as e:
        print(f"Schema init error: {e}")

def connect_db():
    """Try connecting on 3307 then 3306; create DB/tables if needed."""
    global con, conn
    try:
        _connect(3307, with_db=True)
    except Exception as e1:
        print(f"Connect on 3307 failed: {e1}")
        try:
            _connect(3306, with_db=True)
        except Exception as e2:
            print(f"Connect on 3306 with db failed: {e2}")
            # Try without DB then create
            try:
                _connect(3307, with_db=False)
            except Exception as e3:
                print(f"Connect server only on 3307 failed: {e3}")
                _connect(3306, with_db=False)
            _init_schema()
            # Reconnect with DB selected
            _connect(3307, with_db=True)
    try:
        _init_schema()
    except Exception as e:
        print(f"Init schema post-connect error: {e}")

def ensure_db_connection():
    global con, conn
    try:
        if con is None or conn is None:
            connect_db()
        else:
            # Some drivers expose .open flag; if missing, ping
            try:
                con.ping(reconnect=True)
            except Exception:
                connect_db()
    except Exception as e:
        print(f"ensure_db_connection error: {e}")

# Establish initial connection eagerly
try:
    connect_db()
except Exception as e:
    print(f"Initial DB connect error: {e}")

# USGS API configuration
USGS_BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
USGS_CATALOG_URL = "https://earthquake.usgs.gov/fdsnws/event/1/catalog"

root = Tk()
root.geometry('904x604+230+50')
root.title("Natural Disaster Risk Prediction Using Climate Data")
root.resizable(False, False)

# Global variable for real-time data
real_time_earthquake_data = []
last_fetch_time = None

def fetch_usgs_data():
    """Fetch real-time earthquake data from USGS"""
    global real_time_earthquake_data, last_fetch_time
    try:
        # Get earthquakes from the last 7 days for better coverage
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=7)
        
        params = {
            'format': 'geojson',
            'starttime': start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'endtime': end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'minmagnitude': 0,
            'orderby': 'time',
            'limit': 1000  # Get more data for better coverage
        }
        
        response = requests.get(USGS_BASE_URL, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            real_time_earthquake_data = data.get('features', [])
            last_fetch_time = datetime.now()
            print(f"Fetched {len(real_time_earthquake_data)} earthquakes from USGS at {last_fetch_time}")
            return True, f"Successfully fetched {len(real_time_earthquake_data)} earthquakes"
        else:
            print(f"Failed to fetch USGS data: {response.status_code}")
            return False, f"Failed to fetch USGS data: HTTP {response.status_code}"
    except Exception as e:
        print(f"Error fetching USGS data: {e}")
        real_time_earthquake_data = []
        return False, f"Error: {str(e)}"

def manual_refresh_usgs_data():
    """Manually refresh USGS data and return status"""
    success, message = fetch_usgs_data()
    if success:
        messagebox.showinfo("USGS Data Refresh", f"Data refreshed successfully!\n{message}")
    else:
        messagebox.showerror("USGS Data Refresh", f"Failed to refresh data:\n{message}")
    return success, message

def start_data_fetching():
    """Start background thread for fetching USGS data"""
    def fetch_loop():
        while True:
            try:
                fetch_usgs_data()
                time.sleep(600)  # Fetch every 10 minutes
            except Exception as e:
                print(f"Error in fetch loop: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    thread = threading.Thread(target=fetch_loop, daemon=True)
    thread.start()

# Start fetching data in background
start_data_fetching()

class ForgotPasswordWindow:
    def __init__(self, parent):
        self.window = Toplevel(parent)
        self.window.title("Forgot Password")
        self.window.geometry('400x350')
        self.window.resizable(False, False)
        self.window.configure(bg='white')
        
        # Center the window
        self.window.transient(parent)
        self.window.grab_set()
        
        # Heading
        heading = Label(self.window, text='Reset Password', font=('Arial', 16, 'bold'), bg='white', fg='#4152b3')
        heading.pack(pady=20)
        
        # Username field
        Label(self.window, text='Username:', font=('Arial', 10, 'bold'), bg='white').pack(anchor='w', padx=50)
        self.username_entry = Entry(self.window, width=30, font=('Arial', 10))
        self.username_entry.pack(pady=5)
        
        # New password field
        Label(self.window, text='New Password:', font=('Arial', 10, 'bold'), bg='white').pack(anchor='w', padx=50)
        self.new_password_entry = Entry(self.window, width=30, font=('Arial', 10), show='*')
        self.new_password_entry.pack(pady=5)
        
        # Confirm password field
        Label(self.window, text='Confirm Password:', font=('Arial', 10, 'bold'), bg='white').pack(anchor='w', padx=50)
        self.confirm_password_entry = Entry(self.window, width=30, font=('Arial', 10), show='*')
        self.confirm_password_entry.pack(pady=5)
        
        # Reset button
        reset_btn = Button(self.window, text='Reset Password', width=20, bg='#4152b3', fg='white', 
                          font=('Arial', 10, 'bold'), bd=0, cursor='hand2', command=self.reset_password)
        reset_btn.pack(pady=20)
        
        # Status label
        self.status_label = Label(self.window, text='', font=('Arial', 9), bg='white', fg='red')
        self.status_label.pack(pady=5)
        
    def reset_password(self):
        username = self.username_entry.get().strip()
        new_pass = self.new_password_entry.get()
        confirm_pass = self.confirm_password_entry.get()
        
        if not username or not new_pass or not confirm_pass:
            self.status_label.config(text='All fields are required!', fg='red')
            return
            
        if new_pass != confirm_pass:
            self.status_label.config(text='Passwords do not match!', fg='red')
            return
            
        if len(new_pass) < 6:
            self.status_label.config(text='Password must be at least 6 characters!', fg='red')
            return
            
        try:
            ensure_db_connection()
                
            # Check if username exists
            q1 = "SELECT * FROM users_details WHERE username = %s"
            conn.execute(q1, (username,))
            user = conn.fetchone()
            
            if user is None:
                self.status_label.config(text='Username not found!', fg='red')
                return
                
            # Update password
            q2 = "UPDATE users_details SET pass = %s WHERE username = %s"
            conn.execute(q2, (new_pass, username))
            con.commit()
            
            self.status_label.config(text='Password updated successfully!', fg='green')
            messagebox.showinfo('Success', 'Password updated successfully!')
            self.window.destroy()
            
        except Exception as e:
            error_msg = f'Database error: {str(e)}'
            self.status_label.config(text=error_msg, fg='red')
            print(f"Password reset error: {e}")

        
class Login_class:

    #functions : 

    def hide_password(self):
        password.config(show='*')

    def register_page(self):
        rp.register_page2()

    def dashboard_page(self):
        dc.dashboard_page3()

    def clear(self):
        username.delete(0, END)
        password.delete(0, END)


    def user_login(self):
        if username.get() == '' or password.get() == '':
            messagebox.showerror('Error', 'All fields are required!')
            return
        
        try:
            ensure_db_connection()
                
            username_val = username.get()
            pass_val = password.get()

            q1 = "select * from users_details where username = %s and pass = %s"
            conn.execute(q1, (username_val, pass_val))

            global login_user_data
            login_user_data = conn.fetchone()

            if login_user_data == None:
                messagebox.showerror('Error', "Wrong username or password!\nOR\nYou're not registered!")
                lc.clear()
            else:
                
                con.commit()
                lc.clear()
                lc.dashboard_page()
                
        except Exception as e:
            messagebox.showerror('Error', f'Database error: {str(e)}')
            print(f"Login error: {e}")


    

    def remove_widgets(self):
        for i in root.winfo_children():
            i.destroy()

    def login_page1(self):
        lc.remove_widgets()
        root.state('normal')
        root.geometry('904x604+230+50')
        root.resizable(False, False)
        

        global bg
        
        bg = PhotoImage(file='login_bg.png')
        bgLabel = Label(root, image=bg)
        bgLabel.grid(row=0, column=0)

        heading = Label(root, text='Get more things done with\nthe loggin platform', font=('Arial', 12, 'bold'), bg='white')
        heading.place(x=560, y=110)

        subheading = Label(root, text='Access the most powerfull tool', font=('Arial', 8, ''), bg='white', fg='gray')
        subheading.place(x=584, y=155)

        lb1 = Label(root, text='Login', font=('Arial', 10, 'bold'), bg='white', fg='#4152b3')
        lb1.place(x=530, y=190)

        lb2 = Button(root, text='Register', font=('Arial', 10, 'bold'), bg='white', fg='gray', cursor='hand2', bd=0, activebackground='white', command=lc.register_page)
        lb2.place(x=580, y=190)

        lb3 = Label(root, text='Username', font=('Arial', 8, 'bold'), bg='white', fg='black')
        lb3.place(x=530, y=230)

        global username
        username = Entry(root, width=33, font=('Courier New', 10, 'bold'), bd=0, fg='#4152b3')
        username.place(x=534, y=254)

        Frame(root, width=268, height=1, bg='#4152b3').place(x=534, y=275)

        lb4 = Label(root, text='Password', font=('Arial', 8, 'bold'), bg='white', fg='black')
        lb4.place(x=530, y=290)

        global password
        password = Entry(root, width=38, show='*', font=('', 10, 'bold'), bd=0, fg='#4152b3')
        password.place(x=534, y=314)
        # Show/Hide Password Feature
        def toggle_password():
            if password.cget('show') == '':
                password.config(show='*');
                con = pymysql.connect(host='localhost', user='root', password='root')
                conn = con.cursor()
                conn.execute("use alpha")               
                con = pymysql.connect(host='localhost', user='root', password='root')
                conn = con.cursor()
                conn.execute("use alpha")                
                con = pymysql.connect(host='localhost', user='root', password='root')
                conn = con.cursor()
                conn.execute("use alpha")
                show_btn.config(text='👁')
            else:
                password.config(show='')
                show_btn.config(text='🙈')

        show_btn = Button(root, text='👁', font=('Arial', 10), bd=0, bg='white', activebackground='white', cursor='hand2', command=toggle_password)
        show_btn.place(x=770, y=314)

        Frame(root, width=268, height=1, bg='#4152b3').place(x=534, y=335)

        lb4 = Button(root, text='Forgot Password?', font=('', 8, 'bold'), bg='white', fg='red', cursor='hand2', bd=0, activebackground='white', command=lambda: ForgotPasswordWindow(root))
        lb4.place(x=698, y=340)

        login_btn = Button(root, text='Login', width=32, bg='#4152b3', fg='white', font=('', 10, 'bold'), bd=0, activebackground='#4152b3', cursor='hand2', command=lc.user_login).place(x=534, y=400)

        lb5 = Label(root, text='Don\'t have any account?', font=('', 8, 'bold'), bg='white', fg='black')
        lb5.place(x=550, y=460)

        lb6 = Button(root, text='Create new one.', font=('', 8, 'bold'), bg='white', fg='blue', cursor='hand2', bd=0, activebackground='white', command=lc.register_page)
        lb6.place(x=685, y=460)

        admin_btn = Button(root, text='Admin Login', font=('Arial', 10, 'bold'), bg='white', fg='blue', cursor='hand2', bd=0, activebackground='white', command=lambda: AdminLogin())
        admin_btn.place(x=534, y=500)


global lc
lc = Login_class()
lc.login_page1()
















class register_class:

    #functions : 

    def hide_password(self):
        password.config(show='*')

    def login_page(self):
        lc.login_page1()

    def clear(self):
        name.delete(0, END)
        username.delete(0, END)
        password.delete(0, END)
        com_password.delete(0, END)

    def user_register(self):
        if name.get() == '' or username.get() == '' or password.get() == '' or com_password.get() == '':
            messagebox.showerror('Error', 'All fields are required!')
            return
        
        elif password.get() != com_password.get():
            messagebox.showerror("Error", 'Password Mismatch!')
            return

        try:
            ensure_db_connection()
                
            name_val = name.get()
            username_val = username.get()
            pass_val = password.get()

            q1 = "select * from users_details where username = %s"
            conn.execute(q1, (username_val,))
            row1 = conn.fetchone()
            
            if row1 != None:
                messagebox.showwarning('Warning', "Username already exists!\nPlease enter other one.")

            else:   
                q2 = "insert into users_details(name, username, pass) values(%s, %s, %s)"
                conn.execute(q2, (name_val, username_val, pass_val))
                con.commit()

                messagebox.showinfo("Success", "Successfully Registered")
                rp.clear()
                rp.login_page()
                
        except Exception as e:
            messagebox.showerror('Error', f'Database error: {str(e)}')
            print(f"Registration error: {e}")


    def remove_widgets(self):
        for i in root.winfo_children():
            i.destroy()

    def register_page2(self):
        rp.remove_widgets()

        global bg

        bg = PhotoImage(file='signup_bg.png')
        bgLabel = Label(root, image=bg)
        bgLabel.grid(row=0, column=0)

        heading = Label(root, text='Create your account', font=('Arial', 12, 'bold'), bg='white')
        heading.place(x=588, y=110)

        subheading = Label(root, text='Let\'s get started.\nAre you ready to be a part of something new?', font=('Arial', 8, ''), bg='white', fg='gray')
        subheading.place(x=560, y=135)

        lb1 = Button(root, text='Login', font=('Arial', 10, 'bold'), bg='white', fg='gray', cursor='hand2', bd=0, activebackground='white', command=rp.login_page)
        lb1.place(x=530, y=190)

        lb2 = Label(root, text='Register', font=('Arial', 10, 'bold'), bg='white', fg='#ff37fa')
        lb2.place(x=580, y=190)

        lb3 = Label(root, text='Name', font=('Arial', 8, 'bold'), bg='white', fg='black')
        lb3.place(x=530, y=230)

        global name

        name = Entry(root, width=33, font=('Arial', 10, 'bold'), bd=0, fg='#4152b3')
        name.place(x=534, y=254)

        Frame(root, width=268, height=1, bg='#ff37fa').place(x=534, y=275)

        lb4 = Label(root, text='Username', font=('Arial', 8, 'bold'), bg='white', fg='black')
        lb4.place(x=530, y=290)

        global username

        username = Entry(root, width=38, font=('', 10, 'bold'), bd=0, fg='#4152b3')
        username.place(x=534, y=314)

        Frame(root, width=268, height=1, bg='#ff37fa').place(x=534, y=335)

        lb5 = Label(root, text='Password', font=('Arial', 8, 'bold'), bg='white', fg='black')
        lb5.place(x=530, y=350)

        global password

        password = Entry(root, width=38, show='*', font=('', 10, 'bold'), bd=0, fg='#4152b3')
        password.place(x=534, y=374)

        Frame(root, width=268, height=1, bg='#ff37fa').place(x=534, y=395)

        lb6 = Label(root, text='Confirm Password', font=('Arial', 8, 'bold'), bg='white', fg='black')
        lb6.place(x=530, y=410)

        global com_password

        com_password = Entry(root, width=38, show='*', font=('', 10, 'bold'), bd=0, fg='#4152b3')
        com_password.place(x=534, y=434)

        Frame(root, width=268, height=1, bg='#ff37fa').place(x=534, y=455)

        register_btn = Button(root, text='Register', width=33, bg='#ff37fa', fg='white', font=('', 10, 'bold'), bd=0, activebackground='#ff37fa', cursor='hand2', command=rp.user_register).place(x=534, y=470)

        lb7 = Label(root, text='Already registered?', font=('', 8, 'bold'), bg='white', fg='black')
        lb7.place(x=590, y=500)

        lb8 = Button(root, text='Login.', font=('', 8, 'bold'), bg='white', fg='blue', cursor='hand2', bd=0, activebackground='white', command=rp.login_page)
        lb8.place(x=705, y=500)

global rp
rp = register_class()






class nav_sidebar:

    def default(self):
        # Safely read login_user_data and show full name + username
        try:
            name = login_user_data[1] if login_user_data and len(login_user_data) > 1 else ''
            uname = login_user_data[2] if login_user_data and len(login_user_data) > 2 else ''
        except NameError:
            name = ''
            uname = ''

        profile_name.config(text=f"Name: {name}")
        profile_username.config(text=f"Username: {uname}")


    def dashboard_btn(self):
        dc.dashboard_page3()


    def efc_btn(self):
        self.page5()


    def eqh_btn(self):
        self.page6()


    def ea_btn(self):
        self.page7()

    def logout_btn(self):
        lc.login_page1()


    def navbar_sidebar(self):
        
        global logo

        logo = Image.open("logo.png")
        logo = logo.resize((50, 50))
        logo = ImageTk.PhotoImage(logo)
        logo_img = Label(root, image=logo, bd=0, bg='#5271ff')
        logo_img.place(x=30, y=23)

        pro_name = Label(root, text='EARTHQUAKE PREDICTION SYSTEM', font=('Arial', 12, 'bold'), bg='#5271ff', fg='white')
        pro_name.place(x=90, y=35)

        # top-right profile labels: use relx anchor so they stay visible on fullscreen
        global profile_name
        profile_name = Label(root,
                             text='',
                             font=('Arial', 11, 'bold'),
                             bg='#5271ff',
                             fg='white',
                             justify='right',
                             anchor='e',
                             wraplength=300)  # allow wrapping if name is long
        profile_name.place(relx=0.99, y=28, anchor='ne')

        global profile_username
        profile_username = Label(root,
                                 text='',
                                 font=('Arial', 9, 'bold'),
                                 bg='#5271ff',
                                 fg='white',
                                 justify='right',
                                 anchor='e',
                                 wraplength=300)
        profile_username.place(relx=0.99, y=52, anchor='ne')


        #sidebar

        global logo_2

        logo_2 = Image.open("logo.png")
        logo_2 = logo_2.resize((100, 100))
        logo_2 = ImageTk.PhotoImage(logo_2)
        logo_img_1 = Label(root, image=logo_2, bd=0, bg='#252525')
        logo_img_1.place(x=87, y=120)

        heading_text1 = Label(root, text='Main Menu', font=('Arial', 10, 'bold'), bg='#252525', fg='white')
        heading_text1.place(x=30, y=250)

        Frame(root, width=206, height=1, bg='#4152b3').place(x=33, y=275)

        btn1 = Button(root, text='Dashboard', font=('', 9, 'bold'), bg='#4152b3', fg='white', cursor='hand2', bd=0, activebackground='white', width=29, command=dc.dashboard_btn)
        btn1.place(x=32, y=300)

        btn4 = Button(root, text='Earthquake Prediction', font=('', 9, 'bold'), bg='#4152b3', fg='white', cursor='hand2', bd=0, activebackground='white', width=29, command=efc.efc_btn)
        btn4.place(x=32, y=350)

        btn5 = Button(root, text='Earthquake History', font=('', 9, 'bold'), bg='#4152b3', fg='white', cursor='hand2', bd=0, activebackground='white', width=29, command=eqh.eqh_btn)
        btn5.place(x=32, y=400)

        heading_text2 = Label(root, text='Action', font=('Arial', 10, 'bold'), bg='#252525', fg='red')
        heading_text2.place(x=30, y=615)

        Frame(root, width=206, height=1, bg='red').place(x=33, y=640)

        btn5_logout = Button(root, text='Logout', font=('', 9, 'bold'), bg='red', fg='white', cursor='hand2', bd=0, activebackground='white', width=29, command=self.logout_btn)
        btn5_logout.place(x=32, y=660)



class dashboard_class(nav_sidebar):
     

    #functions :
    def remove_widgets(self):
        for i in root.winfo_children():
            i.destroy()

    

    def dashboard_page3(self):
        dc.remove_widgets()
        root.state('zoomed')

        global bg1

        bg1 = PhotoImage(file='dashboard_bg_2.png')
        bgLabel = Label(root, image=bg1)
        bgLabel.grid(row=0, column=0)

        
        dc.navbar_sidebar()


        global robo

        robo = Image.open("welcome.jpg")
        robo = robo.resize((500, 250))
        robo = ImageTk.PhotoImage(robo)
        robo_img = Label(root, image=robo, bd=0)
        robo_img.place(x=540, y=130)
        

        heading = Label(root, text='EARTHQUAKE PREDICTION SYSTEM', font=('Arial', 20, 'bold'), bg='white', fg='blue')
        heading.place(x=540, y=380)

        subheading = Label(root, text='On this page you will find our new exhibition now available.', font=('Arial', 12, ''), bg='white', fg='black')
        subheading.place(x=590, y=430)

        dc.default()

global dc
dc = dashboard_class()






class flood_form_class(nav_sidebar):
     

    #functions :
    def remove_widgets(self):
        for i in root.winfo_children():
            i.destroy()

    

    def page4(self):
        ffc.remove_widgets()
        root.state('zoomed')


        ffc.navbar_sidebar()


        heading = Label(root, text='FLOOD PREDICTION', font=('Arial', 20, 'bold'), bg='white', fg='blue')
        heading.place(x=470, y=380)


        ffc.default()

global ffc
ffc = flood_form_class()




class earthquake_form_class(nav_sidebar):
     
    #functions :
    def remove_widgets(self):
        for i in root.winfo_children():
            i.destroy()

    def clear(self):
        latitude.delete(0, END)
        longitude.delete(0, END)
        magnitude.config(text='Will be detected automatically')
        location_info.config(text='Location will be detected automatically')
    
    def new_prediction(self):
        """Enable input fields for new prediction"""
        latitude.config(state='normal')
        longitude.config(state='normal')
        latitude.delete(0, END)
        longitude.delete(0, END)
        latitude.insert(0, "40.7128")  # Default to NYC coordinates
        longitude.insert(0, "-74.0060")  # Default to NYC coordinates
        magnitude.config(text='Will be detected automatically')
        location_info.config(text='Location will be detected automatically')

    def validate_coordinates(self, lat, lon):
        """Validate latitude and longitude coordinates"""
        if not (-90 <= lat <= 90):
            return False, "Latitude must be between -90 and 90 degrees"
        if not (-180 <= lon <= 180):
            return False, "Longitude must be between -180 and 180 degrees"
        return True, "Valid coordinates"

    def get_location_name(self, lat, lon):
        """Get location name from coordinates using reverse geocoding"""
        try:
            geolocator = Nominatim(user_agent="earthquake_prediction_system")
            location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
            if location:
                return str(location)
            else:
                return f"Unknown location ({lat}, {lon})"
        except Exception as e:
            print(f"Geocoding error: {e}")
            return f"Location ({lat}, {lon})"

    def get_nearby_earthquake_magnitude(self, lat, lon):
        """Get magnitude from nearby earthquakes in USGS data with improved algorithm"""
        if not real_time_earthquake_data:
            return 0.0, "No USGS data available"
        
        min_distance = float('inf')
        nearest_magnitude = 0.0
        nearest_location = ""
        nearby_earthquakes = []
        
        for earthquake in real_time_earthquake_data:
            try:
                eq_lat = earthquake['geometry']['coordinates'][1]
                eq_lon = earthquake['geometry']['coordinates'][0]
                eq_mag = earthquake['properties'].get('mag', 0.0)
                eq_time = earthquake['properties'].get('time', 0)
                eq_place = earthquake['properties'].get('place', 'Unknown')
                
                # Calculate distance using Haversine formula for more accurate results
                distance = self.haversine_distance(lat, lon, eq_lat, eq_lon)
                
                # Store nearby earthquakes within 1000 km
                if distance <= 1000:
                    nearby_earthquakes.append({
                        'distance': distance,
                        'magnitude': eq_mag,
                        'place': eq_place,
                        'time': eq_time
                    })
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_magnitude = eq_mag
                    nearest_location = eq_place
                    
            except (KeyError, IndexError, TypeError) as e:
                continue
        
        # If no nearby earthquakes found, return a default value
        if min_distance == float('inf'):
            return 0.0, "No nearby earthquakes found"
        
        # Calculate weighted average magnitude based on distance
        if nearby_earthquakes:
            total_weight = 0
            weighted_magnitude = 0
            
            for eq in nearby_earthquakes:
                # Weight by inverse distance (closer earthquakes have more weight)
                weight = 1 / (eq['distance'] + 1)  # Add 1 to avoid division by zero
                weighted_magnitude += eq['magnitude'] * weight
                total_weight += weight
            
            if total_weight > 0:
                avg_magnitude = weighted_magnitude / total_weight
                return avg_magnitude, f"Based on {len(nearby_earthquakes)} nearby earthquakes"
        
        return nearest_magnitude, f"Nearest earthquake at {nearest_location}"

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in kilometers
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c

    def predict(self):
        if(latitude.get()=='' or longitude.get()==''):
            messagebox.showerror('Error', 'Latitude and Longitude are required!')
            return

        try:
            # Declare global variables first
            global lati, longi, magni, location_name
            
            lati = float(latitude.get())
            longi = float(longitude.get())
            
            # Validate coordinates
            is_valid, message = self.validate_coordinates(lati, longi)
            if not is_valid:
                messagebox.showerror('Error', message)
                return
            
            # Get magnitude and location from USGS data
            magni, info = self.get_nearby_earthquake_magnitude(lati, longi)
            
            # Get location name
            location_name = self.get_location_name(lati, longi)
            
            # Disable input fields after prediction
            latitude.config(state='disabled')
            longitude.config(state='disabled')
            
            # Update magnitude and location labels with actual values
            magnitude.config(text=f'{magni:.2f}')
            location_info.config(text=f'{location_name}')
            
            # Show prediction page
            ea.page7()
            
        except ValueError:
            messagebox.showerror('Error', 'Please enter valid numeric values for latitude and longitude!')

    def data_fetch(self):
        try:
            if con and conn:
                conn.execute('select * from eq_history where user_id = %s', (login_user_data[0]))
                global data1
                data1 = conn.fetchall()
            else:
                data1 = []
        except Exception as e:
            print(f"Data fetch error: {e}")
            data1 = []

    def page5(self):
        efc.remove_widgets()
        root.state('zoomed')

        efc.navbar_sidebar()

        heading = Label(root, text='EARTHQUAKE PREDICTION', font=('Arial', 20, 'bold'), bg='white', fg='blue')
        heading.place(x=600, y=100)

        sub_heading = Label(root, text='Enter coordinates to predict earthquake risk using real-time USGS data', font=('Arial', 15, 'bold'), bg='white', fg='black')
        sub_heading.place(x=450, y=150)

        # USGS data status
        if last_fetch_time:
            status_text = f"USGS Data: Last updated {last_fetch_time.strftime('%H:%M:%S')} ({len(real_time_earthquake_data)} earthquakes)"
        else:
            status_text = "USGS Data: Fetching..."
        
        status_label = Label(root, text=status_text, font=('Arial', 10), bg='white', fg='green')
        status_label.place(x=450, y=180)

        lb1 = Label(root, text='Latitude', font=('Arial', 8, 'bold'), bg='white', fg='black')
        lb1.place(x=560, y=230)

        global latitude
        latitude = Entry(root, width=33, font=('Arial', 12, 'bold'), bd=0, fg='#4152b3')
        latitude.place(x=434, y=254)
        latitude.insert(0, "40.7128")  # Default to NYC coordinates

        Frame(root, width=299, height=1, bg='#ff37fa').place(x=434, y=275)

        lb2 = Label(root, text='Longitude', font=('Arial', 8, 'bold'), bg='white', fg='black')
        lb2.place(x=975, y=230)

        global longitude
        longitude = Entry(root, width=33, font=('Arial', 12, 'bold'), bd=0, fg='#4152b3')
        longitude.place(x=854, y=254)
        longitude.insert(0, "-74.0060")  # Default to NYC coordinates

        Frame(root, width=299, height=1, bg='#ff37fa').place(x=854, y=275)

        lb3 = Label(root, text='Magnitude (Auto-detected from USGS)', font=('Arial', 8, 'bold'), bg='white', fg='black')
        lb3.place(x=555, y=300)

        global magnitude
        magnitude = Label(root, text='Will be detected automatically', font=('Arial', 10, 'bold'), bg='white', fg='gray')
        magnitude.place(x=434, y=324)

        # Location info
        Label(root, text='Location:', font=('Arial', 8, 'bold'), bg='white', fg='black').place(x=555, y=350)
        global location_info
        location_info = Label(root, text='Location will be detected automatically', font=('Arial', 10, 'bold'), bg='white', fg='gray')
        location_info.place(x=434, y=374)

        btn3 = Button(root, text='Predict', font=('', 9, 'bold'), bg='#4152b3', fg='white', cursor='hand2', bd=0, activebackground='white', width=42, command=efc.predict)
        btn3.place(x=854, y=323)

        # Refresh USGS data button
        refresh_btn = Button(root, text='Refresh USGS Data', font=('', 9, 'bold'), bg='#ff37fa', fg='white', cursor='hand2', bd=0, activebackground='#ff37fa', width=20, command=lambda: [manual_refresh_usgs_data(), status_label.config(text=f"USGS Data: Last updated {datetime.now().strftime('%H:%M:%S')} ({len(real_time_earthquake_data)} earthquakes)")])
        refresh_btn.place(x=434, y=400)
        
        # New Prediction button
        new_prediction_btn = Button(root, text='New Prediction', font=('', 9, 'bold'), bg='#4152b3', fg='white', cursor='hand2', bd=0, activebackground='#4152b3', width=20, command=self.new_prediction)
        new_prediction_btn.place(x=650, y=400)

        s = ttk.Style()
        s.theme_use('clam')
        
        list1 = ttk.Treeview(root, columns=('id', 'latitude', 'longitude', 'magnitude', 'location', 'status'), show='headings')
        list1.heading('id', text='Id')
        list1.column("id", minwidth=0, width=50, stretch=NO, anchor=CENTER)

        list1.heading('latitude', text='Latitude')
        list1.column("latitude", minwidth=0, width=100, stretch=NO, anchor=CENTER)

        list1.heading('longitude', text='Longitude')
        list1.column("longitude", minwidth=0, width=100, stretch=NO, anchor=CENTER)

        list1.heading('magnitude', text='Magnitude')
        list1.column("magnitude", minwidth=0, width=100, stretch=NO, anchor=CENTER)

        list1.heading('location', text='Location')
        list1.column("location", minwidth=0, width=500, stretch=YES, anchor=CENTER)

        list1.heading('status', text='Status')
        list1.column("status", minwidth=0, width=100, stretch=NO, anchor=CENTER)

        list1.place(x=320, y=450)

        self.data_fetch()

        for i in data1:
            list1.insert(parent='', index=i[0], values=i)

        efc.default()

global efc
efc = earthquake_form_class()

# Define earthquake_history_class and instantiate eqh before it is used
class earthquake_history_class(nav_sidebar):
    def eqh_btn(self):
        self.page6()

    def page6(self):
        # Placeholder implementation for Earthquake History page
        self.remove_widgets()
        root.state('zoomed')
        self.navbar_sidebar()
        heading = Label(root, text='EARTHQUAKE HISTORY', font=('Arial', 20, 'bold'), bg='white', fg='blue')
        heading.place(x=600, y=100)
        # Add more widgets as needed

global eqh
eqh = earthquake_history_class()

global ea
ea = None  # Will be set after class def

class earthquake_analysis(nav_sidebar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)   # ✅ fixed
        self.data_set = None              

    def page7(self):
        """Earthquake Risk Analysis Result Page"""
        try:
            # Create a new window for results
            result_win = Toplevel(root)
            result_win.title("Earthquake Risk Analysis Result")
            result_win.state('zoomed')   # fullscreen within the desktop
            result_win.configure(bg='#eaeaea')

            # compute sizes
            screen_w = result_win.winfo_screenwidth()
            screen_h = result_win.winfo_screenheight()
            left_margin = 20
            top_margin = 20
            available_w = screen_w - 2 * left_margin
            left_ratio = 0.66
            left_w = int(available_w * left_ratio)
            right_w = max(240, available_w - left_w - 20)
            frame_h = screen_h - 2 * top_margin

            # Left: result container
            left_frame = Frame(result_win, bg='white', relief='raised', bd=3)
            left_frame.place(x=left_margin, y=top_margin, width=left_w, height=frame_h)

            sub_heading = Label(left_frame, text='Earthquake Risk Analysis Result', font=('Arial', 20, 'bold'), bg='white', fg='blue')
            sub_heading.place(x=12, y=10)

            if last_fetch_time:
                usgs_info = Label(left_frame, text=f'Analysis based on USGS data from {last_fetch_time.strftime("%Y-%m-%d %H:%M:%S")}',
                                  font=('Arial', 10), bg='white', fg='green')
            else:
                usgs_info = Label(left_frame, text='USGS data not available', font=('Arial', 10), bg='white', fg='red')
            usgs_info.place(x=12, y=46)

            Label(left_frame, text='Latitude : ', font=('Arial', 11, 'bold'), bg='white').place(x=12, y=86)
            lat_label = Label(left_frame, text=f'{lati}', font=('Arial', 11), bg='white')
            lat_label.place(x=160, y=86)

            Label(left_frame, text='Longitude : ', font=('Arial', 11, 'bold'), bg='white').place(x=12, y=112)
            long_label = Label(left_frame, text=f'{longi}', font=('Arial', 11), bg='white')
            long_label.place(x=160, y=112)

            Label(left_frame, text='Magnitude : ', font=('Arial', 11, 'bold'), bg='white').place(x=12, y=138)
            mag_label = Label(left_frame, text=f'{magni}', font=('Arial', 11), bg='white')
            mag_label.place(x=160, y=138)

            Label(left_frame, text='Location : ', font=('Arial', 11, 'bold'), bg='white').place(x=12, y=166)
            loc_wrap = max(420, left_w - 260)
            loc_label = Label(left_frame, text=f'{location_name}', font=('Arial', 11), bg='white', wraplength=loc_wrap, justify='left', anchor='nw')
            loc_label.place(x=160, y=166, width=loc_wrap, height=int(frame_h * 0.28))

            # Risk assessment based on magnitude
            risk_text = ""
            risk_color = "black"
            if magni < 4.0:
                risk_text = "LOW RISK - Safe zone"
                risk_color = "green"
            elif magni < 6.0:
                risk_text = "MODERATE RISK - Caution advised"
                risk_color = "orange"
            else:
                risk_text = "HIGH RISK - Immediate attention required"
                risk_color = "red"

            Label(left_frame, text='Risk Assessment : ', font=('Arial', 11, 'bold'), bg='white').place(x=12, y=166 + int(frame_h * 0.28) + 12)
            status_label = Label(left_frame, text=risk_text, font=('Arial', 16, 'bold'), bg='white', fg=risk_color, wraplength=loc_wrap, justify='left', anchor='nw')
            status_label.place(x=160, y=210 + int(frame_h * 0.28), width=loc_wrap, height=int(frame_h * 0.32))

            # Create a dedicated button container frame (simple and robust)
            button_container = Frame(left_frame, bg='white', relief='flat', bd=0)
            # Pin near bottom-left of the results panel
            button_container.place(x=20, y=frame_h - 90, width=280, height=70)
            
            # Back button closes the result window and returns to main UI
            back_btn = Button(
                button_container,
                text='Back to Prediction',
                font=('Arial', 12, 'bold'),
                bg='#4152b3', fg='white',
                cursor='hand2', bd=2, relief='raised',
                activebackground='#2d3b8a',
                width=22, height=1,
                command=result_win.destroy
            )
            # Use pack to avoid clipping with absolute coordinates
            back_btn.pack(padx=10, pady=12, anchor='w')

            # Right: image panel (independent, keeps main window untouched)
            right_x = left_margin + left_w + 12
            right_frame = Frame(result_win, bg='#f6f6f6', relief='flat', bd=0)
            right_frame.place(x=right_x, y=top_margin, width=right_w, height=frame_h)

            bg_right_label = Label(right_frame, bg='#f6f6f6')
            bg_right_label.place(relx=0.5, rely=0.5, anchor='center')

            # Choose image by risk level
            img_path = None
            if magni < 4.0:
                img_path = 'success.png'
            elif magni < 6.0:
                img_path = 'warning.png'
            else:
                img_path = 'danger.png'

            # Load and fit image safely, keep reference
            bg_right_img = None
            try:
                if img_path and os.path.exists(img_path):
                    img = Image.open(img_path)
                    # preserve aspect and fit into right_w x frame_h
                    img.thumbnail((right_w - 20, frame_h - 20), Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.ANTIALIAS)
                    bg_right_img = ImageTk.PhotoImage(img)
                    bg_right_label.config(image=bg_right_img, text='')
                    bg_right_label.image = bg_right_img
                else:
                    bg_right_label.config(text='Image not found', font=('Arial', 12), fg='red')
            except Exception as e:
                print(f"Error loading right-side image: {e}")
                bg_right_label.config(text='Image error', font=('Arial', 12), fg='red')

            # Make sure left frame content is on top of the right panel
            try:
                left_frame.lift()
                button_container.lift()
                back_btn.lift()
                status_label.lift()
                result_win.update_idletasks()
            except Exception:
                pass

        except Exception as e:
            print(f"page7 error: {e}")
            messagebox.showerror("Error", f"Could not open result window: {e}")


# ✅ Create an object
ea = earthquake_analysis()

# INSERT: simple AdminLogin dialog so AdminLogin() is defined when login_page1 creates the admin button
class AdminLogin:
    def __init__(self, parent=root):
        self.window = Toplevel(parent)
        self.window.title("Admin Login")
        self.window.geometry('360x220+600+250')
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        Label(self.window, text='Admin Login', font=('Arial', 14, 'bold')).pack(pady=10)
        Label(self.window, text='Username', font=('Arial', 10)).pack(anchor='w', padx=20)
        self.user_entry = Entry(self.window, width=30)
        self.user_entry.pack(padx=20, pady=5)

        Label(self.window, text='Password', font=('Arial', 10)).pack(anchor='w', padx=20)
        self.pass_entry = Entry(self.window, width=30, show='*')
        self.pass_entry.pack(padx=20, pady=5)

        login_btn = Button(self.window, text='Login', width=20, bg='#4152b3', fg='white',
                           command=self.attempt_login)
        login_btn.pack(pady=10)

        self.status = Label(self.window, text='', fg='red')
        self.status.pack()

    def attempt_login(self):
        user = self.user_entry.get().strip()
        passwd = self.pass_entry.get().strip()
        # Admin credentials: username='admin', password='admin123'
        # Replace with real admin authentication system when available
        if user == 'admin' and passwd == 'admin123':
            self.status.config(text='Login successful', fg='green')
            # Open admin dashboard after successful login
            self.window.after(1000, self.open_admin_dashboard)  # Wait 1 second to show success message
        else:
            self.status.config(text='Invalid admin credentials', fg='red')
    
    def open_admin_dashboard(self):
        """Open the admin dashboard page"""
        try:
            # Close the login window
            self.window.destroy()
            
            # Create admin dashboard window
            admin_win = Toplevel(root)
            admin_win.title("Admin Dashboard - Earthquake Prediction System")
            admin_win.state('zoomed')  # Fullscreen
            admin_win.configure(bg='#f0f0f0')
            
            # Header
            header_frame = Frame(admin_win, bg='#4152b3', height=80)
            header_frame.pack(fill='x')
            header_frame.pack_propagate(False)
            
            Label(header_frame, text='ADMIN DASHBOARD', font=('Arial', 24, 'bold'), 
                  bg='#4152b3', fg='white').pack(pady=20)
            
            # Main content area
            main_frame = Frame(admin_win, bg='#f0f0f0')
            main_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            # Welcome message
            Label(main_frame, text='Welcome to the Admin Dashboard', font=('Arial', 18, 'bold'), 
                  bg='#f0f0f0', fg='#4152b3').pack(pady=20)
            
            # Admin functions
            functions_frame = Frame(main_frame, bg='#f0f0f0')
            functions_frame.pack(pady=20)
            
            # User Management Button
            user_btn = Button(functions_frame, text='User Management', font=('Arial', 14, 'bold'), 
                             bg='#4152b3', fg='white', width=25, height=2, cursor='hand2',
                             command=lambda: self.show_user_management(admin_win))
            user_btn.pack(pady=10)
            
            # Prediction History Button
            history_btn = Button(functions_frame, text='Prediction History', font=('Arial', 14, 'bold'), 
                                bg='#4152b3', fg='white', width=25, height=2, cursor='hand2',
                                command=lambda: self.show_prediction_history(admin_win))
            history_btn.pack(pady=10)
            
            # System Statistics Button
            stats_btn = Button(functions_frame, text='System Statistics', font=('Arial', 14, 'bold'), 
                              bg='#4152b3', fg='white', width=25, height=2, cursor='hand2',
                              command=lambda: self.show_system_stats(admin_win))
            stats_btn.pack(pady=10)
            
            # Back to Main Menu Button
            back_btn = Button(main_frame, text='Back to Main Menu', font=('Arial', 12, 'bold'), 
                             bg='red', fg='white', width=20, height=2, cursor='hand2',
                             command=admin_win.destroy)
            back_btn.pack(pady=20)
            
        except Exception as e:
            print(f"Error opening admin dashboard: {e}")
            messagebox.showerror("Error", f"Could not open admin dashboard: {e}")
    
    def show_user_management(self, admin_win):
        """Show user management interface"""
        try:
            # Create user management window
            user_win = Toplevel(admin_win)
            user_win.title("User Management")
            user_win.geometry('900x650')
            user_win.configure(bg='white')

            Label(user_win, text='User Management', font=('Arial', 20, 'bold'),
                  bg='white', fg='#4152b3').pack(pady=10)

            # Controls frame
            controls = Frame(user_win, bg='white')
            controls.pack(fill='x', padx=20)

            status_lbl = Label(controls, text='', bg='white', fg='green', font=('Arial', 10, 'bold'))
            status_lbl.pack(side='right')

            # Treeview for users
            table_frame = Frame(user_win, bg='white')
            table_frame.pack(fill='both', expand=True, padx=20, pady=10)

            columns = ('ID', 'Name', 'Username')
            users_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=18)
            for col, width in zip(columns, (80, 220, 220)):
                users_tree.heading(col, text=col)
                users_tree.column(col, width=width, anchor='center')

            yscroll = ttk.Scrollbar(table_frame, orient='vertical', command=users_tree.yview)
            users_tree.configure(yscrollcommand=yscroll.set)
            users_tree.pack(side='left', fill='both', expand=True)
            yscroll.pack(side='right', fill='y')

            def load_users():
                try:
                    # Clear existing
                    for i in users_tree.get_children():
                        users_tree.delete(i)

                    if con is None or conn is None:
                        status_lbl.config(text='DB not connected', fg='red')
                        return

                    # Fetch users (do not show password)
                    conn.execute("SELECT id, name, username FROM users_details ORDER BY id DESC")
                    rows = conn.fetchall()
                    for row in rows:
                        users_tree.insert('', 'end', values=row)
                    status_lbl.config(text=f'Loaded {len(rows)} users', fg='green')
                except Exception as e:
                    status_lbl.config(text=f'Load error: {e}', fg='red')
                    print(f"User load error: {e}")

            # Buttons
            btns = Frame(user_win, bg='white')
            btns.pack(fill='x', padx=20, pady=10)

            Button(btns, text='Refresh', font=('Arial', 11, 'bold'), bg='#4152b3', fg='white',
                   width=14, command=load_users).pack(side='left')

            Button(btns, text='Close', font=('Arial', 11, 'bold'), bg='red', fg='white',
                   width=14, command=user_win.destroy).pack(side='right')

            # Initial load
            load_users()
            
        except Exception as e:
            print(f"Error opening user management: {e}")
    
    def show_prediction_history(self, admin_win):
        """Show prediction history interface"""
        try:
            # Create prediction history window
            history_win = Toplevel(admin_win)
            history_win.title("Prediction History")
            history_win.geometry('1200x750')
            history_win.configure(bg='white')

            Label(history_win, text='Prediction History', font=('Arial', 20, 'bold'),
                  bg='white', fg='#4152b3').pack(pady=10)

            controls = Frame(history_win, bg='white')
            controls.pack(fill='x', padx=20)
            hist_status = Label(controls, text='', bg='white', fg='green', font=('Arial', 10, 'bold'))
            hist_status.pack(side='right')

            # Create treeview for prediction history
            tree_frame = Frame(history_win, bg='white')
            tree_frame.pack(fill='both', expand=True, padx=20, pady=10)

            columns = ('ID', 'User', 'Latitude', 'Longitude', 'Magnitude', 'Location', 'Status', 'CreatedAt')
            tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=22)

            widths = (60, 140, 100, 100, 110, 520, 120, 160)
            for col, width in zip(columns, widths):
                tree.heading(col, text=col)
                tree.column(col, width=width, anchor='center')

            scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)

            tree.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')

            def load_history():
                try:
                    # Clear existing
                    for i in tree.get_children():
                        tree.delete(i)

                    if con is None or conn is None:
                        hist_status.config(text='DB not connected', fg='red')
                        return

                    # Try to read eq_history with username via join if possible
                    try:
                        conn.execute(
                            """
                            SELECT eh.id, ud.username, eh.latitude, eh.longitude, eh.magnitude,
                                   eh.location, eh.status, eh.created_at
                              FROM eq_history eh
                              LEFT JOIN users_details ud ON ud.id = eh.user_id
                             ORDER BY eh.id DESC
                            """
                        )
                        rows = conn.fetchall()
                    except Exception:
                        # Fallback if columns differ
                        conn.execute("SELECT * FROM eq_history ORDER BY id DESC")
                        rows = conn.fetchall()

                    for row in rows:
                        tree.insert('', 'end', values=row)
                    hist_status.config(text=f'Loaded {len(rows)} records', fg='green')
                except Exception as e:
                    hist_status.config(text=f'Load error: {e}', fg='red')
                    print(f"History load error: {e}")

            btns = Frame(history_win, bg='white')
            btns.pack(fill='x', padx=20, pady=10)

            Button(btns, text='Refresh', font=('Arial', 11, 'bold'), bg='#4152b3', fg='white',
                   width=14, command=load_history).pack(side='left')

            Button(btns, text='Close', font=('Arial', 11, 'bold'), bg='red', fg='white',
                   width=14, command=history_win.destroy).pack(side='right')

            # Initial load
            load_history()
            
        except Exception as e:
            print(f"Error opening prediction history: {e}")
    
    def show_system_stats(self, admin_win):
        """Show system statistics interface"""
        try:
            # Create system stats window
            stats_win = Toplevel(admin_win)
            stats_win.title("System Statistics")
            stats_win.geometry('600x500')
            stats_win.configure(bg='white')
            
            Label(stats_win, text='System Statistics', font=('Arial', 20, 'bold'), 
                  bg='white', fg='#4152b3').pack(pady=20)
            
            # Statistics display (placeholder)
            stats_frame = Frame(stats_win, bg='white')
            stats_frame.pack(pady=20)
            
            stats_data = [
                ('Total Users:', '150'),
                ('Total Predictions:', '1,250'),
                ('System Uptime:', '99.9%'),
                ('Last Backup:', '2024-01-15 02:00:00'),
                ('Database Size:', '45.2 MB'),
                ('Active Sessions:', '23')
            ]
            
            for i, (label, value) in enumerate(stats_data):
                Label(stats_frame, text=label, font=('Arial', 12, 'bold'), 
                      bg='white', fg='black').grid(row=i, column=0, sticky='w', padx=20, pady=10)
                Label(stats_frame, text=value, font=('Arial', 12), 
                      bg='white', fg='#4152b3').grid(row=i, column=1, sticky='w', padx=20, pady=10)
            
            Button(stats_win, text='Close', font=('Arial', 12, 'bold'), 
                   bg='#4152b3', fg='white', command=stats_win.destroy).pack(pady=20)
            
        except Exception as e:
            print(f"Error opening system stats: {e}")

# Instantiate ea after class definition
ea = earthquake_analysis()

# Run mainloop once
if __name__ == "__main__":
    root.mainloop()
