import openai
from flask import Flask, request, jsonify, render_template
import joblib
import numpy as np
import os

app = Flask(__name__)

openai.api_key = os.getenv('OPENAI_API_KEY')

print("Loading model and feature names...")
model = joblib.load('mortality_mlp_model.pkl')
feature_names = ['AGE', 'GENDER', 'Transfusionintraandpostop', 'AnaestypeCategory',
                 'SurgRiskCategory', 'CHFRCRICategory', 'DMinsulinRCRICategory']
print("Model and feature names loaded.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_speech', methods=['POST'])
def process_speech():
    data = request.get_json()
    speech_text = data.get('speech_text', '')

    if not speech_text:
        return jsonify(response="Error: No speech input detected.")

    extracted_features = extract_features_from_speech(speech_text)
    if not extracted_features:
        return jsonify(response="Error: Could not extract features from speech.")

    feature_values = {}
    invalid_features = []
    for feature, value in extracted_features.items():
        encoded_value = get_encoded_value(feature, value)
        if encoded_value is None:
            invalid_features.append(feature)
        else:
            feature_values[feature] = encoded_value

    if invalid_features:
        return jsonify(response=f"Error: Invalid or missing values for features: {', '.join(invalid_features)}. Please provide these values again.", invalid_features=invalid_features)

    predictions = call_model_api(feature_values)
    result_text = f"The predicted 30-day mortality risk is {predictions['prediction']} with a probability of {predictions['probability']:.2f}."
    return jsonify(response=result_text)

def extract_features_from_speech(speech_text):
    prompt = (
        f"Extract the following features from this text:\n"
        f"AGE, GENDER, Transfusionintraandpostop, AnaestypeCategory,\n"
        f"SurgRiskCategory, CHFRCRICategory, DMinsulinRCRICategory.\n"
        f"Text: {speech_text}\n"
        f"Please provide the features in the format 'Feature: Value'."
    )
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a medical assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    # Debugging: Log the raw response from GPT-3
    extracted_text = response['choices'][0]['message']['content'].strip()
    print(f"GPT-3 response: {extracted_text}")

    extracted_features = {}
    try:
        for line in extracted_text.split('\n'):
            if ':' in line:
                feature, value = line.split(':', 1)
                extracted_features[feature.strip()] = value.strip()
    except Exception as e:
        print(f"Error extracting features: {e}")
        return None

    print(f"Extracted features: {extracted_features}")
    return extracted_features

def get_encoded_value(feature, value):
    encoded_values = {
        'GENDER': {'female': 0, 'male': 1},
        'AnaestypeCategory': {'ga': 0, 'ra': 1},
        'SurgRiskCategory': {'high': 0, 'low': 1, 'moderate': 2},
        'CHFRCRICategory': {'no': 0, 'yes': 1},
        'DMinsulinRCRICategory': {'no': 0, 'yes': 1}
    }
    if feature in encoded_values:
        # Handle variations in input for 'DMinsulinRCRICategory'
        if feature == 'DMinsulinRCRICategory':
            insulin_keywords = ['insulin', 'taking insulin', 'on insulin']
            for keyword in insulin_keywords:
                if keyword in value.lower():
                    return 1
            return 0
        return encoded_values[feature].get(value.lower().strip(), None)
    try:
        return float(value)
    except ValueError:
        return None

def call_model_api(features):
    features_array = np.array([features.get(feature, 0) for feature in feature_names]).reshape(1, -1)
    prediction = model.predict(features_array)[0]
    prediction_prob = model.predict_proba(features_array)[0][1]
    return {'prediction': int(prediction), 'probability': float(prediction_prob)}

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(host='0.0.0.0', port=5000)
    print("Flask app started.")
