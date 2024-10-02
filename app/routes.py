# app/route.py

from flask import jsonify, send_file, request, Blueprint, session
from app.process_image import preprocess, get_area
from app.resource_tracker import log_resource_usage
from app.models import Models
import base64, pickle
from collections import defaultdict



# Create a Blueprint for routes
api_bp = Blueprint('api', __name__)


@api_bp.route('/get_gee_image', methods=['POST'])
def gee_image():
    """
    Endpoint to get a Google Earth Engine image based on the region of interest (ROI).
    """
    model = Models()
    roi_data = request.json  # Expecting JSON data with ROI information
    model.setRoiData(roi_data)  # Set the ROI in the model
    model.getImage()  # Fetch the image based on ROI
    image = model.getNormalizedImage()  # Normalize the image for processing
    session['model'] = pickle.dumps(model)
    image_png = preprocess(image, False)  # Preprocess the image (modify as needed)
    
    # Send the image as a response
    return send_file(image_png, mimetype='image/png')

@api_bp.route('/get_mask', methods=['POST'])
def generate_mask():
    """
    Endpoint to generate a colored mask based on class data.
    """
    class_data = request.json  # Expecting JSON data with class information
    if 'model' in session:
        model = pickle.loads(session['model'])
    else:
        return jsonify({'No Google Earth Image Found.'}), 400
    
    model.setClassData(class_data)  # Set the class data in the model
    colored_mask_pngs = model.getColoredMask()  # Get the colored mask images
    response = defaultdict()

    for key, value in colored_mask_pngs.items():
        area = get_area(value, model.scale)  # Calculate area (modify as per your logic)
        png_mask = preprocess(value, True)  # Preprocess the mask (modify as needed)
        base_64 = base64.b64encode(png_mask.getvalue()).decode('utf-8')  # Convert to base64
        response[key] = [base_64, 1, area]  # Build the response dictionary

    # Empty the session variable
    session.pop('model', None)
    # Return the response as JSON
    return jsonify(response)

@api_bp.route("/resource_usage")
def checkResource():
    resourse_log = log_resource_usage()

    return resourse_log

@api_bp.route('/')
def default():
    """
    Default entry endpoint.
    """
    return "Semantic segmentation of satellite images using machine learning and deep learning models."
