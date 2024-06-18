from flask import Flask, request, jsonify
import joblib
import numpy as np

app = Flask(__name__)

print("Loading model and feature names...")
model = joblib.load('mortality_mlp_model.pkl')
feature_names = joblib.load('feature_names.pkl')
print("Model and feature names loaded.")

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    features = np.array([data[feature] for feature in feature_names]).reshape(1, -1)
    prediction = model.predict(features)[0]
    prediction_prob = model.predict_proba(features)[0][1]
    return jsonify({'prediction': int(prediction), 'probability': float(prediction_prob)})

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(host='0.0.0.0', port=5000)
    print("Flask app started.")