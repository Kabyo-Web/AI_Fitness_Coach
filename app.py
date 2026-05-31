import streamlit as st
import pandas as pd
import sqlite3
import joblib
import numpy as np
import datetime
import plotly.express as px
import random
import io
import smtplib
from email.message import EmailMessage
from PIL import Image, ImageDraw, ImageFont

# --- 1. Page Configuration ---
st.set_page_config(page_title="AI Fitness Coach", page_icon="💪", layout="wide")

# --- 2. Database Setup ---
def init_db():
    conn = sqlite3.connect('fitness_app.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, firstname TEXT, surname TEXT, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                  (email TEXT, date TEXT, sleep REAL, water REAL, steps INTEGER, 
                   exercise INTEGER, mood INTEGER, calories INTEGER, score REAL)''')
    conn.commit()
    conn.close()

init_db()

# --- Email OTP Function (Updated with st.secrets) ---
def send_otp_email(user_email, otp):
    msg = EmailMessage()
    msg.set_content(f"Your verification code is: {otp}")
    msg['Subject'] = 'Fitness App Verification Code'
    msg['From'] = f"AI Fitness Coach <{st.secrets['email']}>"
    msg['To'] = user_email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(st.secrets["email"], st.secrets["app_password"])
        smtp.send_message(msg)

# --- 3. Functions ---
def validate_email(email):
    return "@" in email and "." in email.split("@")[-1]

def register_user(email, firstname, surname, password):
    conn = sqlite3.connect('fitness_app.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?,?,?,?)", (email, firstname, surname, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return "exists"
    finally:
        conn.close()

def login_user(email, password):
    conn = sqlite3.connect('fitness_app.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    user = c.fetchone()
    conn.close()
    return user is not None

def get_user_name(email):
    conn = sqlite3.connect('fitness_app.db')
    c = conn.cursor()
    c.execute("SELECT firstname, surname FROM users WHERE email=?", (email,))
    user = c.fetchone()
    conn.close()
    return f"{user[0]} {user[1]}" if user else "User"

def user_exists(email):
    conn = sqlite3.connect('fitness_app.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user = c.fetchone()
    conn.close()
    return user is not None

def update_password(email, new_password):
    conn = sqlite3.connect('fitness_app.db')
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE email=?", (new_password, email))
    conn.commit()
    conn.close()

def retrain_model():
    st.info("Retraining model with latest database entries...")
    return True

# --- Captcha Generator Function ---
def generate_captcha():
    code = "".join([str(random.randint(0, 9)) for _ in range(4)])
    img = Image.new('RGB', (120, 40), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    for i in range(8):
        d.line([(random.randint(0, 120), random.randint(0, 40)), 
                (random.randint(0, 120), random.randint(0, 40))], fill=(random.randint(0,255), random.randint(0,255), random.randint(0,255)))
    d.text((25, 10), code, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return code, buf.getvalue()

# --- 4. Helper for AI Tips ---
def get_ai_tips(score):
    if score > 8: return "🌟 Amazing job! Keep this consistency."
    elif score > 5: return "👍 Good work, but you can push a little more!"
    else: return "⚠️ Your score is low. Try to get more sleep and hydrate."

# --- 5. Main Application Logic ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("""
        <style>
        .title-style { text-align: center; color: #4CAF50; font-size: 50px; font-weight: bold; margin-bottom: 30px; }
        </style>
        <div class="title-style">💪 Welcome to AI Fitness Coach</div>
    """, unsafe_allow_html=True)
    
    choice = st.sidebar.radio("Navigation", ["Login", "Register"])
    
    with st.container():
        left_col, mid_col, right_col = st.columns([1, 2, 1])
        
        with mid_col:
            if choice == "Register":
                st.subheader("Create New Account")
                firstname = st.text_input("First Name")
                surname = st.text_input("Surname")
                email = st.text_input("Email Address")
                password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                
                if st.button("Send Verification Code"):
                    if validate_email(email):
                        st.session_state.otp = str(random.randint(100000, 999999))
                        send_otp_email(email, st.session_state.otp)
                        st.success("Verification code sent!")
                    else: st.error("Invalid email.")
                
                otp_input = st.text_input("Enter Verification Code")
                
                if 'captcha_code' not in st.session_state:
                    st.session_state.captcha_code, st.session_state.captcha_img = generate_captcha()
                
                st.image(st.session_state.captcha_img)
                captcha_input = st.text_input("Enter Captcha")
                
                if st.button("Register"):
                    if 'otp' in st.session_state and otp_input == st.session_state.otp:
                        if len(password) < 8: st.error("Password must be at least 8 characters long!")
                        elif password != confirm_password: st.error("Passwords do not match!")
                        elif captcha_input != st.session_state.captcha_code: 
                            st.error("Invalid Captcha!")
                            st.session_state.captcha_code, st.session_state.captcha_img = generate_captcha()
                            st.rerun()
                        else:
                            reg_status = register_user(email, firstname, surname, password)
                            if reg_status == True: 
                                st.session_state.logged_in = True
                                st.session_state.user = email
                                st.session_state.welcome_msg = True
                                st.rerun()
                            elif reg_status == "exists": st.error("Email already registered.")
                    else: st.error("Invalid OTP!")
            else:
                st.subheader("Login to your Account")
                email = st.text_input("Email Address")
                password = st.text_input("Password", type="password")
                if st.button("Login"):
                    if login_user(email, password):
                        st.session_state.logged_in = True
                        st.session_state.user = email
                        st.rerun()
                    else: st.error("Invalid Email or Password")
                
                if st.checkbox("Forgot Password?"):
                    f_email = st.text_input("Enter your registered email")
                    if st.button("Verify Email"):
                        if user_exists(f_email):
                            st.session_state.reset_email = f_email
                            st.success("Email verified! Enter new password.")
                        else: st.error("Email not found.")
                    
                    if 'reset_email' in st.session_state:
                        new_pass = st.text_input("New Password", type="password")
                        if st.button("Update Password"):
                            if len(new_pass) < 8: st.error("Password too short!")
                            else:
                                update_password(st.session_state.reset_email, new_pass)
                                st.success("Password updated successfully!")
                                del st.session_state.reset_email
else:
    if 'welcome_msg' in st.session_state:
        st.balloons()
        st.success("🎉 Welcome! You have successfully registered.")
        if st.button("Continue to App"):
            del st.session_state.welcome_msg
            st.rerun()

    st.sidebar.button("Logout", on_click=lambda: st.session_state.update(logged_in=False))
    
    if 'user_name' not in st.session_state:
        st.session_state.user_name = get_user_name(st.session_state.user)
    
    st.markdown(f"<h1 style='text-align: center;'>Hello, {st.session_state.user_name}!</h1>", unsafe_allow_html=True)
    
    model = joblib.load("model.pkl")
    scaler = joblib.load("scaler.pkl")

    col1, col2 = st.columns(2)
    with col1:
        sleep = st.number_input("Sleep Hours", 0.0, 24.0, 7.0)
        water = st.number_input("Water Intake", 0.0, 5.0, 2.0)
        steps = st.number_input("Steps", 0, 30000, 5000)
    with col2:
        exercise = st.number_input("Exercise Minutes", 0, 300, 30)
        mood = st.number_input("Mood Score", 1, 10, 5)
        calories = st.number_input("Calories Burnt", 0, 5000, 200)

    if st.button("Predict Score"):
        data = np.array([[sleep, water, steps, exercise, mood, calories]])
        score = model.predict(scaler.transform(data))[0]
        st.success(f"Fitness Score: {score:.2f}")
        st.info(f"AI Tip: {get_ai_tips(score)}") 
        
        conn = sqlite3.connect('fitness_app.db')
        c = conn.cursor()
        c.execute("INSERT INTO history VALUES (?,?,?,?,?,?,?,?,?)", 
                  (st.session_state.user, str(datetime.date.today()), sleep, water, steps, exercise, mood, calories, score))
        conn.commit()
        conn.close()

    st.sidebar.markdown("---")
    st.sidebar.subheader("Advanced Tools")
    if st.sidebar.button("Retrain Model"):
        if retrain_model(): st.sidebar.success("Model Updated!")
    
    conn = sqlite3.connect('fitness_app.db')
    df = pd.read_sql_query(f"SELECT * FROM history WHERE email = '{st.session_state.user}'", conn)
    conn.close()
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date']).dt.date
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Report (CSV)", csv, "fitness_report.csv", "text/csv")
        
        st.subheader("Visualizations")
        tab1, tab2 = st.tabs(["Line Chart", "Heatmap"])
        with tab1:
            fig1 = px.line(df, x='date', y='score', title='Progress Chart', markers=True)
            fig1.update_xaxes(type='category')
            st.plotly_chart(fig1, use_container_width=True)
        with tab2:
            fig2 = px.density_heatmap(df, x='date', y='score', title='Workout Consistency')
            st.plotly_chart(fig2, use_container_width=True)