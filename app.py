from flask import Flask, flash, redirect, render_template, request, session, send_from_directory, url_for, jsonify
from flask_session import Session
import sqlite3
from datetime import timedelta
from functions import chargeBot, openData, clear_old_chat_records, reassign_assistant
from apscheduler.schedulers.background import BackgroundScheduler


import os
from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.utils import secure_filename

app = Flask(__name__)

load_dotenv()
    
# Getting chatGPT api_key for interacting with the api
api_key = os.getenv('CHATGPT_API_KEY')
# Initialize OpenAI client with API key
client = OpenAI(api_key=api_key)
#Initializing the thread
thread = client.beta.threads.create()
#Create new assistant
assistant = reassign_assistant(client, None)
    
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
        openData()
    
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
        
    @app.route("/audio_folder/<filename>", methods=["GET"])
    def audio_folder(filename):
        
        # Serve the file from the AUDIO_FOLDER directory
        return send_from_directory(app.config['AUDIO_FOLDER'], filename)
            
    @app.route("/")
    def index():
        global thread
        global client
        global assistant
        try:
            response = client.beta.threads.delete(thread_id=thread.id)
            print(f"Thread {thread.id} deleted successfully")
        except Exception as e:
            print(f"Error deleting thread: {e}")
        thread = client.beta.threads.create()
        assistant = reassign_assistant(client, assistant)
        
        #delete all from the database
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
                
                output = chargeBot(question, client, thread, assistant)
                question = filename
            else:
                question = request.form.get("question")
                
                if not question:
                    return jsonify({'error': 'Question is required.'}), 400
                
                output = chargeBot(question, client, thread, assistant)
                
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
                
                output = chargeBot(question, client, thread, assistant)
                question = filename
            else:
                question = request.form.get("messageInput")
                
                if not question:
                    return jsonify({'error': 'Question is required.'}), 400
                
                output = chargeBot(question, client, thread, assistant)
            
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
    
    