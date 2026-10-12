from flask import Flask, flash, redirect, render_template, request, session, send_from_directory, url_for, jsonify
from flask_session import Session
import sqlite3
from datetime import timedelta
from functions import chargeBot, demoBot, openData, clear_old_chat_records, create_vector_store
from apscheduler.schedulers.background import BackgroundScheduler
from charging import charging_session


import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.utils import secure_filename

app = Flask(__name__)

load_dotenv()
    
# Getting chatGPT api_key for interacting with the api
api_key = os.getenv('OPENAI_API_KEY') or os.getenv('CHATGPT_API_KEY')
# Without an API key the website still runs, but only in demo mode
AI_ENABLED = bool(api_key)
if not AI_ENABLED:
    print("No OPENAI_API_KEY (or CHATGPT_API_KEY) set: running in demo mode only")
# Initialize OpenAI client with API key
client = OpenAI(api_key=api_key) if AI_ENABLED else None
# Id of the last bot response, used to keep the conversation going (None = new conversation)
previous_response_id = None
vector_store = None

def create_app():

    # Define the upload folder in the configuration
    app.config['AUDIO_FOLDER'] = 'static/data/audio_files'
    app.config['TXT_FOLDER'] = 'static/data/txt_files'
    
    # Ensure the upload folders exist
    os.makedirs(app.config['AUDIO_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TXT_FOLDER'], exist_ok=True)
    
    # Set up the scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=clear_old_chat_records, trigger="interval", hours=1)  # Runs every hour
    scheduler.start()

    # Configure session to use filesystem (instead of signed cookies)
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
    
    # Set secret key for session management
    app.secret_key = os.getenv('SECRET_KEY')
    
    # Initialize session
    Session(app)

    # Run openData() within the app context
    with app.app_context():
        try:
            openData()
        except Exception as e:
            # Keep serving with the activity.txt already on disk
            print(f"Error refreshing data from Open Data Hub: {e}")

    # Create a vector store called "VS" with the activity data
    global vector_store
    if AI_ENABLED:
        vector_store = create_vector_store(client)

    def is_demo():
        # Demo mode is switched on by the "Demo mode" slider, or forced when there is no API key
        return not AI_ENABLED or request.cookies.get('demo') == '1'

    def answer(question):
        global previous_response_id
        charging = charging_session.bot_context()
        if is_demo():
            return demoBot(question, charging)
        output, previous_response_id = chargeBot(question, client, vector_store, previous_response_id, charging)
        return output

    @app.context_processor
    def inject_demo():
        return {"demo_forced": not AI_ENABLED}
    
    # Define your routes
    
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory('static/images/', 'favicon.ico', max_age=0)  # No caching
            
    @app.route("/check-database", methods=["GET"])
    def check_database():
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chat")
            rows = cursor.fetchall()
            
            conn.commit()
            conn.close()
            
            result = [{'id': row[0], 'user': row[1], 'machine': row[2]} for row in rows]
            return jsonify(result)
        
        except sqlite3.Error as e:
            return jsonify({"error": str(e)}), 500
        
    @app.route("/charging-status", methods=["GET"])
    def charging_status():
        return jsonify(charging_session.snapshot())

    @app.route("/charging/stop", methods=["POST"])
    def charging_stop():
        charging_session.stop()
        return jsonify(charging_session.snapshot())

    @app.route("/charging/restart", methods=["POST"])
    def charging_restart():
        charging_session.restart()
        return jsonify(charging_session.snapshot())

    @app.route("/audio_folder/<filename>", methods=["GET"])
    def audio_folder(filename):
        
        # Serve the file from the AUDIO_FOLDER directory
        return send_from_directory(app.config['AUDIO_FOLDER'], filename)
            
    @app.route("/")
    def index():
        global previous_response_id
        # Start a new conversation
        previous_response_id = None
        
        # Delete all from the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM chat")
        cursor.execute("DELETE FROM time")
        
                    
        conn.commit()
        conn.close()
        
        #delete all from the audio_folder
        for filename in os.listdir(app.config['AUDIO_FOLDER']):
            file_path = os.path.join(app.config['AUDIO_FOLDER'], filename)
            
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
                
        return render_template("homepage.html")
    
    @app.route("/start_chat_page", methods=["GET", "POST"])
    def start_chat():
        if request.method == "POST":
            if 'audioStorage' in request.files:

                question = request.files['audioStorage']
                
                if question.filename == '':
                    return jsonify(message='No selected file'), 400
                
                audio_mime_types = ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4']
        
                if question.content_type in audio_mime_types:
                    filename = secure_filename(question.filename)
                    question.save(os.path.join(app.config['AUDIO_FOLDER'], filename))
                else:
                    return jsonify(message='Invalid file type'), 400
                
                output = answer(question)
                question = filename
            else:
                question = request.form.get("question")
                
                if not question:
                    return jsonify({'error': 'Question is required.'}), 400
                
                output = answer(question)
                
            try:
                conn = sqlite3.connect('database.db')

                cursor = conn.cursor()
                
                # Insert into chat table
                cursor.execute("INSERT INTO chat (user, machine) VALUES (?, ?)", (question, output))
                chat_id = cursor.lastrowid

                # Insert into time table with chat_id
                cursor.execute("INSERT INTO time (chat_id) VALUES (?)", (chat_id,))
            
            except sqlite3.Error as e:
                conn.close()
                return jsonify({'error': f'An error occurred: {e}'}), 500

            conn.commit()
            conn.close()
            # Return JSON response with redirection URL
            return jsonify({'redirect': '/start_chat_page', 'message': 'Chat recorded successfully!'})

        return redirect("/chat_page")

    @app.route("/chat_page", methods=["GET", "POST"])
    def chat():
        if request.method == "POST":
            if 'audioStorage' in request.files:
                #insert code to convert the audio file in text
                question = request.files['audioStorage']
                
                if question.filename == '':
                    return jsonify(message='No selected file'), 400
                
                audio_mime_types = ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4']
        
                if question.content_type in audio_mime_types:
                    filename = secure_filename(question.filename)
                    question.save(os.path.join(app.config['AUDIO_FOLDER'], filename))
                else:
                    return jsonify(message='Invalid file type'), 400
                
                output = answer(question)
                question = filename
            else:
                question = request.form.get("messageInput")
                
                if not question:
                    return jsonify({'error': 'Question is required.'}), 400
                
                output = answer(question)
            
            try:
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                
                # Insert into chat table
                cursor.execute("INSERT INTO chat (user, machine) VALUES (?, ?)", (question, output))
                chat_id = cursor.lastrowid

                # Insert into time table with chat_id
                cursor.execute("INSERT INTO time (chat_id) VALUES (?)", (chat_id,))
                
            except sqlite3.Error as e:
                conn.close()
                return jsonify({'error': f'An error occurred: {e}'}), 500

            conn.commit()
            conn.close()
            # Return JSON response with redirection URL
            return jsonify({'message': output})
        
        return render_template("chat.html")
    
    @app.route("/home", methods=["GET", "POST"])
    def homepage():
        return redirect("/")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run()
else:
    # For production (Gunicorn)
    app = create_app()
    
    