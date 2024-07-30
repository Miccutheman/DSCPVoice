document.addEventListener('DOMContentLoaded', function() {
    const speakButton = document.getElementById('speak-button');
    const chatBox = document.getElementById('chat-box');
    const userIcon = document.getElementById('user-icon');
    const aiIcon = document.getElementById('ai-icon');
    let initialPromptGiven = false; // Flag to track if the initial prompt has been given
    let invalidFeatures = []; // Track invalid features that need to be re-entered

    function speak(text) {
        const synth = window.speechSynthesis;
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.onstart = () => {
            aiIcon.classList.add('icon-speaking');
        };
        utterance.onend = () => {
            aiIcon.classList.remove('icon-speaking');
        };
        synth.speak(utterance);
    }

    function addMessageToChatBox(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);
        messageDiv.textContent = message;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight; // Scroll to the bottom
    }

    speakButton.addEventListener('click', function() {
        if (!initialPromptGiven) {
            // Give the initial prompt only once
            const initialPrompt = "Please provide the patient's details including age, gender, transfusion details, RDW level, insulin-requiring diabetes mellitus, and grade of kidney disease.";
            addMessageToChatBox(initialPrompt, 'bot');
            speak(initialPrompt);
            initialPromptGiven = true; // Set the flag to true after the initial prompt
            return; // Exit the function to avoid starting speech recognition immediately
        }

        const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = 'en-US';
        recognition.start();
        userIcon.classList.add('icon-speaking');

        recognition.onresult = function(event) {
            const userMessage = event.results[0][0].transcript;
            userIcon.classList.remove('icon-speaking');

            addMessageToChatBox(userMessage, 'user');

            // Send the entire speech text or specific invalid feature to the backend for processing
            let speechText = userMessage;
            if (invalidFeatures.length > 0) {
                const feature = invalidFeatures.shift();
                speechText = `${feature}: ${userMessage}`;
            }

            fetch('/process_speech', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({speech_text: speechText})
            })
            .then(response => response.json())
            .then(data => {
                if (data.invalid_features && data.invalid_features.length > 0) {
                    invalidFeatures = data.invalid_features;
                    const prompt = `Please re-enter the value for the following features: ${invalidFeatures.join(', ')}.`;
                    addMessageToChatBox(prompt, 'bot');
                    speak(prompt);
                } else {
                    addMessageToChatBox(data.response, 'bot');
                    speak(data.response);
                }
            })
            .catch(error => {
                const errorMessage = "Error: Could not process your request.";
                addMessageToChatBox(errorMessage, 'bot');
                speak(errorMessage);
                console.error('Error:', error);
            });
        };

        recognition.onerror = function(event) {
            userIcon.classList.remove('icon-speaking');
            const errorMessage = "Error: Speech recognition failed.";
            addMessageToChatBox(errorMessage, 'bot');
            speak(errorMessage);
            console.error("Speech recognition error:", event.error);
        };
    });

    // Initial prompt to guide the user
    const initialPrompt = "Please provide the patient's details including age, gender, transfusion details, RDW level, insulin-requiring diabetes mellitus, and grade of kidney disease.";
    addMessageToChatBox(initialPrompt, 'bot');
    speak(initialPrompt);
    initialPromptGiven = true; // Set the flag to true after the initial prompt
});
