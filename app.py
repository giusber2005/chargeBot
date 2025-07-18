from flask import Flask, flash, redirect, render_template, request, session, send_from_directory, url_for, jsonify
from flask_session import Session
import sqlite3
from datetime import timedelta
from functions import chargeBot, openData, clear_old_chat_records
from apscheduler.schedulers.background import BackgroundScheduler


import os
from werkzeug.utils import secure_filename


def create_app():
    app = Flask(__name__)

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
    app.secret_key = "woqnEp-hygtev-0gyxsi"
    
    # Initialize session
    Session(app)

    # Run openData() within the app context
    with app.app_context():
        openData()
    
    # Define your routes
    @app.route("/check-database", methods=["GET"])
    def check_database():
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chat")
            rows = cursor.fetchall()

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
                
                output = chargeBot(question)
                question = filename
            else:
                question = request.form.get("question")
                
                if not question:
                    return jsonify({'error': 'Question is required.'}), 400
                
                output = chargeBot(question)

            try:
                with sqlite3.connect('database.db') as conn:
                    cursor = conn.cursor()
                    
                    # Insert into chat table
                    cursor.execute("INSERT INTO chat (user, machine) VALUES (?, ?)", (question, output))
                    chat_id = cursor.lastrowid

                    # Insert into time table with chat_id
                    cursor.execute("INSERT INTO time (chat_id) VALUES (?)", (chat_id,))
                    
                    conn.commit()
            
            except sqlite3.Error as e:
                return jsonify({'error': f'An error occurred: {e}'}), 500

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
                
                output = chargeBot(question)
                question = filename
            else:
                question = request.form.get("messageInput")
                
                if not question:
                    return jsonify({'error': 'Question is required.'}), 400
                
                output = chargeBot(question)
            
            try:
                with sqlite3.connect('database.db') as conn:
                    cursor = conn.cursor()
                    
                    # Insert into chat table
                    cursor.execute("INSERT INTO chat (user, machine) VALUES (?, ?)", (question, output))
                    chat_id = cursor.lastrowid

                    # Insert into time table with chat_id
                    cursor.execute("INSERT INTO time (chat_id) VALUES (?)", (chat_id,))
                    
                    conn.commit()
            
            except sqlite3.Error as e:
                return jsonify({'error': f'An error occurred: {e}'}), 500

            # Return JSON response with redirection URL
            return jsonify({'message': output})
        
        return render_template("chat.html")
    
    @app.route("/home", methods=["GET", "POST"])
    def homepage():
        return redirect("/")

    return app
