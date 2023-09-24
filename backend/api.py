from flask import Flask, request, jsonify, url_for, make_response
from flask_cors import CORS, cross_origin
from PIL import Image
import numpy as np
from analyzer import *
import time 

app = Flask(__name__)
CORS(app, support_credentials=True)

@app.route('/test', methods=['GET'])
def test():
    print("Here we go...")
    result = analyze_test_img()
    print("Done!")

    filename = f'static/med_reminder{time.time()}.ics' 

    # Save the ICS file
    with open(filename, "wb") as f:
        f.write(result.to_ical())

    # Create a JSON response with the analysis result
    response = filename

    return jsonify(response)

@app.route('/analyze', methods=['POST'])
def analyze():
    # Check if the post request has a file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']

    # If the user does not select a file, the browser submits an empty part without a filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    # Check if the file has a valid extension (e.g., jpg)
    if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() == 'jpg' or file.filename.rsplit('.', 1)[1].lower() == 'jpeg':
        try:
            # Open the uploaded image using PIL
            temp_file_path = f'tmp/temp_{time.time()}.jpg'
            file.save(temp_file_path)

            # Call the analyze_img function to process the image
            print("Here we go...")
            result = analyze_img(temp_file_path)
            print("Done!")

            filename = f'static/med_reminder{time.time()}.ics' 

            # Save the ICS file
            with open(filename, "wb") as f:
                f.write(result.to_ical())

            # Create a JSON response with the analysis result
            response = filename

            return jsonify(response)

        except Exception as e:
            return jsonify({'error': str(e)})

    else:
        print(f"Invalid file extension: {file.filename.rsplit('.', 1)[1].lower()}")
        return jsonify({'error': 'Invalid file extension'})

if __name__ == '__main__':
    app.run(debug=True)