from dotenv import load_dotenv
import os
from datetime import datetime
from openai_processing import complete_openai
from speech_processing import start_recording, speak

# ---------------------------------------------------------------------------- #
#                                     Setup                                    #
# ---------------------------------------------------------------------------- #

load_dotenv(override=True)

settings = {
    'speechKey': os.environ.get('SPEECH_KEY'),
    'region': os.environ.get('SPEECH_REGION'),
    'language': os.environ.get('SPEECH_LANGUAGE'),
    'openAIKey': os.environ.get('OPENAI_API_KEY')
}

output_folder = f'./Output/{datetime.now().strftime("%Y%m%d_%H%M%S")}/'
os.makedirs(output_folder)

conversation = []

while True:
    try:
        speech = start_recording()
        if speech:
            print(f"User said: {speech}")
            
            # Exit condition
            if "exit" in speech.lower() or "quit" in speech.lower():
                print("Ending conversation.")
                break

            conversation.append(speech)
            prompt = ""
            for j in range(len(conversation) - 4, len(conversation)):
                if j >= 0:
                    if j % 2 == 0:
                        prompt += f"Q: {conversation[j]}\n"
                    else:
                        prompt += f"A: {conversation[j]}\n"
            prompt += "A: "
            result = complete_openai(prompt=prompt, token=3000)
            if result:
                print(f"AI said: {result}")  # Print the response
                speak(result, output_folder=output_folder)
                conversation.append(result)
            
            print("Loop continues...")

    except Exception as e:
        print(f"An exception occurred in the main loop: {e}")
        

