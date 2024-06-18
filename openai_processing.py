import openai
from dotenv import load_dotenv
import os

# Load your API key from an environment variable or secret management service
load_dotenv(override=True)

settings = {
    'speechKey': os.environ.get('SPEECH_KEY'),
    'region': os.environ.get('SPEECH_REGION'),
    'language': os.environ.get('SPEECH_LANGUAGE'),
    'openAIKey': os.environ.get('OPENAI_API_KEY')
}

openai.api_key = settings['openAIKey']

def complete_openai(prompt, token=50):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=token,
            top_p=1,
            presence_penalty=1.5,
            frequency_penalty=1.5,
        )
        response_text = response.choices[0].message['content'].strip()
        return response_text
    except Exception as e:
        print(f"An exception of type {type(e).__name__} occurred with the message: {e}")
        return ""
