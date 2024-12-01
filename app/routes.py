# app/route.py

from flask import jsonify, send_file, request, Blueprint, session
from app.process_image import preprocess, get_area
from app.extras import log_resource_usage, intro
from app.models import Models
from app.mask import ImageMask
from app.gee_image import GeeImage
import base64
from collections import defaultdict
from googleapiclient.errors import HttpError

ip_set = set()

# Create a Blueprint for routes
api_bp = Blueprint('api', __name__)


@api_bp.route('/get_gee_image', methods=['POST'])
def gee_image():
    """
    Endpoint to get a Google Earth Engine image based on the region of interest (ROI).
    """
    image = GeeImage()
    roi_data = request.json
    try:
        image.setRoiData(roi_data)  # Set the ROI in the image
        image.getImage()  # Fetch the image based on ROI
    except Exception as e:
        return 'Selected ROI too large. Please select an area less scale of 5 KM. Please refresh and retry', 400

    norm_image = image.getNormalizedImage()  # Normalize the image for processing

    session['image'] = image.img_array
    session['band'] = image.bands
    session['scale'] = image.scale
    session['start_date'] = image.start_date
    session['end_date'] = image.end_date
    image_png = preprocess(norm_image, False)  # Preprocess the image (Remove black background)

    # Send the image as a response
    return send_file(image_png, mimetype='image/png'), 200

@api_bp.route('/get_mask', methods=['POST'])
def generate_mask():
    """
    Endpoint to generate a colored mask based on class data.
    """
    class_data = request.json
    if 'image' in session:
        img_array = session['image']
        bands = session['band']
        scale = session['scale']
        start_date = session['start_date']
        end_date = session['end_date']
        mask = Models(bands, scale, img_array, start_date, end_date)
    else:
        return 'Please select an ROI first. If the problem persist, enable cookies in the browser.', 400

    try:
        mask.setClassData(class_data)  # Set the class data in the image
        colored_mask_pngs = mask.getColoredMask()  # Get the colored mask images
    except Exception as e:
        return 'Error while generating mask. Please refresh and retry.', 400

    response = defaultdict()
    for key, value in colored_mask_pngs.items():
        area = get_area(value, mask.scale)  # Calculate area
        png_mask = preprocess(value, True)  # Preprocess the mask (Remove black background)
        base_64 = base64.b64encode(png_mask.getvalue()).decode('utf-8')  # Convert to base64
        response[key] = [base_64, 1, area]  # Build the response dictionary

    # Empty the session variable
    session.pop('image', None)
    session.pop('band', None)
    session.pop('scale', None)
    session.pop('start_date', None)
    session.pop('end_date', None)

    return jsonify(response)

@api_bp.route("/resource_usage")
def checkResource():

    return log_resource_usage(), 200

@api_bp.route('/')
def default():
    return intro(), 200

@api_bp.route('/get_ip')
def ip():
    ip_address = list(ip_set)
    return jsonify(ip_address), 200

@api_bp.route('/set_ip')
def set_ip():
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    ip_set.add(ip_address)
    return "Ip Recieved", 200


@api_bp.route("/image-url")
def image_url():
    image = GeeImage()
    roi_data = request.json
    try:
        image.setRoiData(roi_data)  # Set the ROI in the image
        image_url = image.getImageUrl()  # Fetch the image based on ROI
        session["band"] = image.bands
        session["scale"] = image.scale
        session["start_date"] = image.start_date
        session["end_date"] = image.end_date
        session["image_url"] = image_url
        response = {"image_url": image_url}
        return jsonify(response), 200
    except Exception as e:
        return (
            "Selected ROI too large. Please select an area less scale of 5 KM. Please refresh and retry",
            400,
        )
