import openai
from flask import Flask, request, jsonify, render_template
import joblib
import numpy as np
import pandas as pd
import os
import re

app = Flask(__name__)

openai.api_key = os.getenv('OPENAI_API_KEY')

print("Loading models and feature names...")
models_and_features = joblib.load('models_and_features.pkl')
icu_admission_model = models_and_features['icu_admission_model']
mortality_model = models_and_features['mortality_model']
print("Models loaded.")

# Store extracted features between requests
stored_features = {}

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

    global stored_features
    for feature, value in extracted_features.items():
        if value is not None and value.lower() != 'not mentioned':
            stored_features[feature] = value

    feature_values = {}
    invalid_features = []
    for feature, value in stored_features.items():
        encoded_value = get_encoded_value(feature, value)
        if encoded_value is None:
            invalid_features.append(feature)
        else:
            feature_values[feature] = encoded_value

    if invalid_features:
        return jsonify(response=f"Error: Invalid or missing values for features: {', '.join(invalid_features)}. Please provide these values again.", invalid_features=invalid_features)

    print(f"Feature values before preparation: {feature_values}")  # Debug statement

    # Prepare features for model input
    feature_values, missing_features = prepare_features_for_model(feature_values)

    if missing_features:
        return jsonify(response=f"Error: The following required features are missing: {', '.join(missing_features)}. Please provide these values again.", invalid_features=missing_features)

    print(f"Feature values after preparation: {feature_values}")  # Debug statement

    icu_predictions = call_model_api(icu_admission_model, feature_values)
    mortality_predictions = call_model_api(mortality_model, feature_values)

    result_text = (
        f"The predicted ICU admission risk is {icu_predictions['prediction']} with a probability of {icu_predictions['probability']:.2f}.\n"
        f"The predicted 30-day mortality risk is {mortality_predictions['prediction']} with a probability of {mortality_predictions['probability']:.2f}."
    )
    return jsonify(response=result_text)

def extract_features_from_speech(speech_text):
    prompt = (
        f"Extract the following features from this text:\n"
        f"AGE, GENDER, Transfusionintraandpostop, RDW15.7, DMinsulinRCRICategory, GradeofKidneyCategory.\n"
        f"Text: {speech_text}\n"
        f"Please provide the features in the format 'Feature: Value'. If a feature is not mentioned, please specify 'Not mentioned'."
    )
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a medical assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    extracted_text = response['choices'][0]['message']['content'].strip()
    print(f"GPT-3 response: {extracted_text}")

    extracted_features = {}
    try:
        for line in extracted_text.split('\n'):
            if ':' in line:
                feature, value = line.split(':', 1)
                feature = feature.strip().lstrip('-').strip()
                value = value.strip()
                if value.lower() == 'not mentioned':
                    extracted_features[feature] = None
                else:
                    extracted_features[feature] = value
    except Exception as e:
        print(f"Error extracting features: {e}")
        return None

    print(f"Extracted features: {extracted_features}")
    return extracted_features

def get_encoded_value(feature, value):
    if value is None or value == '':
        return None

    word_to_num = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14,
        'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20
    }
    
    encoded_values = {
        'GENDER': {
            'female': 0, 'male': 1,
            'woman': 0, 'man': 1, 'girl': 0, 'boy': 1, 'lady': 0, 'gentleman': 1
        },
        'DMinsulinRCRICategory': {
            'no': 0, 'yes': 1,
            'insulin requiring diabetes': 1, 'non-insulin diabetes': 0, 'insulin': 1
        },
        'GradeofKidneyCategory': {
            'g1': 0, 'g2': 1, 'g3': 2, 'g4-g5': 3,
            '1': 0, '2': 1, '3': 2, '4': 3, '5': 4, 'stage 1': 0, 'stage 2': 1, 'stage 3': 2, 'stage 4': 3, 'stage 5': 4
        },
        'RDW15.7': {
            '<= 15.7': 0, '>15.7': 1,
            'less than 15.7': 0, 'greater than 15.7': 1, 'rdw less than 15.7': 0, 'rdw greater than 15.7': 1
        }
    }

    value = value.lower().strip()
    
    if feature == 'Transfusionintraandpostop':
        # Extract the number from the value
        numeric_value = None
        for word, num in word_to_num.items():
            if word in value:
                numeric_value = num
                break
        if numeric_value is None:
            # Try extracting the number directly
            match = re.search(r'\d+', value)
            if match:
                numeric_value = int(match.group())
        return numeric_value

    if feature == 'AGE':
        return int(''.join(filter(str.isdigit, value)))

    if value in word_to_num:
        value = word_to_num[value]
    
    if feature in encoded_values:
        return encoded_values[feature].get(value, None)
    
    try:
        return float(value)
    except ValueError:
        return None

def prepare_features_for_model(features):
    # Convert features dictionary to DataFrame for easier manipulation
    df = pd.DataFrame([features])
    
    print(f"Initial DataFrame:\n{df}\n")  # Debug statement

    required_features = [
        'GENDER', 'DMinsulinRCRICategory', 'GradeofKidneyCategory', 
        'Transfusionintraandpostop', 'RDW15.7', 'AGE'
    ]

    # Ensure all required features are present in the DataFrame
    missing_features = [feature for feature in required_features if feature not in df.columns]
    if missing_features:
        print(f"Missing features: {missing_features}")  # Debug statement
        return None, missing_features

    # Create the feature array
    feature_array = np.zeros(len(required_features))
    for i, feature in enumerate(required_features):
        feature_array[i] = df[feature].values[0] if feature in df.columns else 0

    print(f"Feature array fed to the model:\n{feature_array}\n")  # Debug statement

    return feature_array.reshape(1, -1), []

def call_model_api(model, features):
    prediction = model.predict(features)[0]
    prediction_prob = model.predict_proba(features)[0][1]
    return {'prediction': int(prediction), 'probability': float(prediction_prob)}

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(host='0.0.0.0', port=5000)
    print("Flask app started.")
