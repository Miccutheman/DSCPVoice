import azure.cognitiveservices.speech as speechsdk
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import string

# Load environment variables
load_dotenv()

settings = {
    'speechKey': os.environ.get('SPEECH_KEY'),
    'region': os.environ.get('SPEECH_REGION'),
    'language': os.environ.get('SPEECH_LANGUAGE')
}

# Encoded values for categorical features
encoded_values = {
    'GENDER': {'female': 0, 'male': 1},
    'Anemia category': {'mild': 0, 'moderate': 1, 'none': 2, 'severe': 3},
    'GradeofKidneydisease': {'g1': 0, 'g2': 1, 'g3a': 2, 'g3b': 3, 'g4': 4},
    'PriorityCategory': {'elective': 0, 'emergency': 1}
}

def speak(text):
    try:
        speech_config = speechsdk.SpeechConfig(subscription=settings['speechKey'], region=settings['region'])
        speech_config.speech_synthesis_voice_name = 'en-US-JennyNeural'
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

        speech_synthesis_result = speech_synthesizer.speak_text(text)
        if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("Speech synthesis completed successfully.")
        elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_synthesis_result.cancellation_details
            print(f"Speech synthesis cancelled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print(f"Error details: {cancellation_details.error_details}")
    except Exception as e:
        print(f"An exception occurred in speak function: {e}")

def recognize_speech():
    try:
        speech_config = speechsdk.SpeechConfig(subscription=settings['speechKey'], region=settings['region'])
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        
        print("Speak into your microphone...")
        result = speech_recognizer.recognize_once()
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            recognized_text = result.text.strip().strip(string.punctuation).lower()
            print(f"Recognized: {recognized_text}")
            return recognized_text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized")
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"Speech Recognition canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print(f"Error details: {cancellation_details.error_details}")
    except Exception as e:
        print(f"An exception occurred in recognize_speech function: {e}")
    return ""

def get_encoded_value(feature, value):
    if feature in encoded_values:
        return encoded_values[feature].get(value, None)
    return float(value)

def call_model_api(features):
    url = 'http://127.0.0.1:5000/predict'
    response = requests.post(url, json=features)
    return response.json()

def main():
    feature_names = ['AGE', 'GENDER', 'RCRI score', 'Anemia category', 'GradeofKidneydisease', 'PriorityCategory']
    feature_values = {}

    for feature in feature_names:
        if feature == 'GENDER':
            speak("Please provide your gender. Say 'male' or 'female'.")
        elif feature == 'Anemia category':
            speak(f"Please provide your {feature.replace('_', ' ')}. Say 'mild', 'moderate', 'none', or 'severe'.")
        elif feature == 'GradeofKidneydisease':
            speak(f"Please provide your grade of kidney disease. Say 'G1', 'G2', 'G3a', 'G3b', or 'G4'.")
        elif feature == 'PriorityCategory':
            speak(f"Please provide your priority category. Say 'elective' or 'emergency'.")
        elif feature == 'RCRI score':
            speak(f"Please provide your RCRI score.")
        else:
            speak(f"Please provide your {feature.replace('_', ' ')}.")
        
        value = recognize_speech()
        
        if feature in encoded_values:
            encoded_value = get_encoded_value(feature, value)
            while encoded_value is None:
                speak(f"I couldn't understand the value for {feature.replace('_', ' ')}. Please provide it again.")
                value = recognize_speech()
                encoded_value = get_encoded_value(feature, value)
            feature_values[feature] = encoded_value
        else:
            try:
                feature_values[feature] = float(value)
            except ValueError:
                speak(f"I couldn't understand the value for {feature.replace('_', ' ')}. Please provide it again.")
                value = recognize_speech()
                try:
                    feature_values[feature] = float(value)
                except ValueError:
                    speak(f"Failed to understand the value for {feature.replace('_', ' ')}. Moving to the next feature.")
    
    predictions = call_model_api(feature_values)
    result_text = (f"The predicted 30-day mortality risk is {predictions['prediction']} with a probability of "
                   f"{predictions['probability']:.2f}.")
    speak(result_text)
    print(result_text)

if __name__ == '__main__':
    main()
