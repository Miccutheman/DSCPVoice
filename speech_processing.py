import os
import time
from datetime import datetime
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
import simpleaudio as sa

load_dotenv(override=True)

settings = {
    'speechKey': os.environ.get('SPEECH_KEY'),
    'region': os.environ.get('SPEECH_REGION'),
    'language': os.environ.get('SPEECH_LANGUAGE'),
    'openAIKey': os.environ.get('OPENAI_API_KEY')
}

def speak(text, output_folder):
    try:
        # Configure speech synthesis
        speech_config = speechsdk.SpeechConfig(
            subscription=settings['speechKey'], region=settings['region'])
        
        file_name = f'{output_folder}/{datetime.now().strftime("%Y%m%d_%H%M%S")}.wav'
        
        speech_config.speech_synthesis_voice_name = 'en-US-JennyNeural'
        audio_config = speechsdk.audio.AudioOutputConfig(filename=file_name)

        # Create the speech synthesizer
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_config
        )

        # Perform the speech synthesis
        speech_synthesis_result = speech_synthesizer.speak_text(text)

        if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            # Play the audio file
            play_obj = sa.WaveObject.from_wave_file(file_name).play()
            play_obj.wait_done()
        elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_synthesis_result.cancellation_details
            print(f"Speech synthesis cancelled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print(f"Error details: {cancellation_details.error_details}")

        print("Speech synthesis completed successfully.")

    except Exception as e:
        print(f"An exception occurred in speak function: {e}")

def start_recording():
    speech_config = speechsdk.SpeechConfig(
        subscription=settings['speechKey'], region=settings['region'])
    
    speech_config.request_word_level_timestamps()
    speech_config.set_property(
        property_id=speechsdk.PropertyId.SpeechServiceResponse_OutputFormatOption, value="detailed")
    
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=audio_config)
    
    # Initialize results list
    results = []
    done = False

    def speech_detected():
        nonlocal last_spoken
        last_spoken = int(datetime.now().timestamp() * 1000)

    def handle_results(evt):
        nonlocal results
        speech_detected()
        if evt.result.text != "":
            results.append(evt.result.text)
            print(f"text: {evt.result.text}")

    def stop_recognition(evt):
        nonlocal done
        print(f"Event: {evt}")
        done = True

    # Connect event handlers
    speech_recognizer.session_started.connect(lambda evt: print(f"Session Started {evt}"))
    speech_recognizer.session_stopped.connect(stop_recognition)
    speech_recognizer.canceled.connect(stop_recognition)
    speech_recognizer.recognized.connect(handle_results)
    speech_recognizer.recognizing.connect(lambda evt: speech_detected())  # Handle recognizing event to update last_spoken

    # Start continuous recognition
    result_future = speech_recognizer.start_continuous_recognition_async()
    result_future.get()

    last_spoken = int(datetime.now().timestamp() * 1000)

    while not done:
        time.sleep(1)
        now = int(datetime.now().timestamp() * 1000)
        inactivity = now - last_spoken

        if inactivity > 6000:
            print("No speech detected for 6 seconds, stopping recognition.")
            speech_recognizer.stop_continuous_recognition_async().get()
            break

    # Return the most recent result or None if no speech was recognized
    return results[-1] if results else None
