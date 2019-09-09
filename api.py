from flask import Flask, jsonify, request
import numpy as np
import pickle

# Set up the Flask app.
app = Flask('chicago_api')


@app.route('/score', methods=['POST'])
def position():
    incoming = request.get_json()

    violations = incoming['violations']

    with open('data/chicago_y_categories.pkl', 'rb') as pickle_file:
        rev_y_cats = pickle.load(pickle_file)

    with open('data/chicago_x_categories.pkl', 'rb') as pickle_file:
        x_categories = pickle.load(pickle_file)

    this_x = np.zeros((1, len(x_categories)))

    for v in violations:
        this_x[0, x_categories[v]] = 1

    with open('data/chicago_model.pkl', 'rb') as pickle_file:
        model = pickle.load(pickle_file)

    prediction = model.predict(this_x)
    probs = model.predict_proba(this_x)

    response = {
        'prediction': rev_y_cats[int(prediction)]
    }

    for k, v in rev_y_cats.items():
        response[v + '_probability'] = probs[0, k]

    return jsonify(response)
