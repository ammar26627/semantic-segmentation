from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
from process_image import preprocess, get_area
from models import Models
from io import BytesIO
import base64
from PIL import Image
from collections import defaultdict

Models.initialize_earth_engine()
model = Models()

app = Flask(__name__)
CORS(app)

@app.route('/get_gee_image', methods=['POST'])
def geeImage():
    roi_data = request.json
    model.setRoiData(roi_data)
    image = model.getNormalizedImage()
    image_png = preprocess(image, False)
    return send_file(image_png, mimetype='image/png')

@app.route('/get_mask', methods=['POST'])
def generateMask():
    class_data = request.json
    model.setClassData(class_data)
    colored_mask_pngs = model.getColoredMask()
    response = defaultdict()
    for key, value in colored_mask_pngs:
        area = get_area(value, model.scale)
        png_mask = preprocess(value, False)
        base_64 =  base64.b64encode(png_mask).decode('utf-8')
        response[key] = [base_64, area]
    return jsonify(response)
    
    
if __name__ == "__main__":
    app.run(debug=True, port=5000)