from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from pymongo import MongoClient
from textblob import TextBlob
from datetime import datetime
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set UTF-8 encoding for standard output to avoid UnicodeEncodeError
sys.stdout.reconfigure(encoding='utf-8')

# Initialize the Flask app
app = Flask(__name__)

# MongoDB setup with an environment variable for URI
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://brightcarvalho11:EtYFTn0nK0kWLbFI@cluster0.2ngbg.mongodb.net/")
client = MongoClient(MONGO_URI)
db = client["SpeechDataDB"]
collection = db["SentimentStream"]

# Function to analyze sentiment
def analyze_sentiment(text):
    """Analyze the sentiment and return the category (positive, negative, neutral)."""
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    else:
        return "Neutral"

# Function to store text in MongoDB with sentiment and timestamp
def store_text_with_sentiment(text):
    """Stores text with its sentiment and timestamp in MongoDB."""
    sentiment = analyze_sentiment(text)
    data = {
        "text": text,
        "sentiment": sentiment,
        "timestamp": datetime.now()
    }
    try:
        collection.insert_one(data)
        logging.info(f"Stored in MongoDB: {data}")
    except Exception as e:
        logging.error(f"Failed to store data in MongoDB: {e}")

# Speech-to-text processing
def process_speech():
    with sr.Microphone() as source:
        logging.info("Adjusting for ambient noise... Please wait.")
        recognizer = sr.Recognizer()
        recognizer.adjust_for_ambient_noise(source, duration=1)
        logging.info("You can start speaking now.")

        try:
            # Capture the audio once
            audio_data = recognizer.listen(source, timeout=5)
            logging.info("Recognizing...")

            # Convert audio to text
            text = recognizer.recognize_google(audio_data, language='en-IN')

            # Store in MongoDB with sentiment and timestamp
            store_text_with_sentiment(text)
            return {"text": text, "sentiment": analyze_sentiment(text)}

        except sr.UnknownValueError:
            return {"error": "Could not understand the audio."}
        except sr.RequestError as e:
            return {"error": f"Request error: {e}"}
        except Exception as e:
            return {"error": f"An error occurred: {e}"}

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_speech', methods=['POST'])
def process_speech_route():
    result = process_speech()
    if "text" in result:
        return jsonify(result)
    else:
        return jsonify(result), 500

# Run the app on port 5500
if __name__ == '__main__':
    app.run(debug=True, port=5500)
