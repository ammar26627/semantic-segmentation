# app/route.py

# from app import socketio
from flask import jsonify, request, Blueprint, session, Response, stream_with_context
from app.process_image import preprocess, get_area
from app.extras import log_resource_usage, intro
from app.models import Models
from app.mask import ImageMask
from app.gee_image import GeeImage
import base64, json, threading
from queue import Queue
from collections import defaultdict
from app.image_thread import ImageThread
from keras import models
from keras import preprocessing


ip_set = set()

# Create a Blueprint for routes
api_bp = Blueprint('api', __name__)


@api_bp.route('/image', methods=['POST'])
def image():
    """
    Endpoint to get a Google Earth Engine image based on the region of interest (ROI).
    """
    roi_data = request.json
    if api_bp.config['TESTING']:
        with open('/testing/sample_test_json/images/area_1.json', 'r') as file:
            roi_data = json.load(file)

    # Initialize GeeImage and set ROI
    image = GeeImage()
    image.setRoiData(roi_data)  # Set the ROI in the image

    image_queue = Queue()

    # For streaming the image
    def generate():
        print("Starting stream...")
        while True:
            message = image_queue.get()
            if message['status'] == "Completed":
                yield f"data: {message}\n\n"
                print("Data sent, Closing connection")
                break
            yield f"data: {json.dumps(message)}\n\n"

    image_thread = ImageThread(image.getImage, image_queue)
    threading.Thread(target=image_thread.image_with_thread_pool, args=(50, image.roi_array)).start()
    return Response(stream_with_context(generate(), mimetype='text/event-stream'))

# @api_bp.route('/stream_images', methods=['GET'])
# def stream_images():
#     """
#     SSE endpoint to stream processed images.
# """
#     image = session.get('image')
#     try:
#         if not image.roi_array:
#             return jsonify({'error': 'No ROI data found'}), 400
#     except Exception as e:
#         print(e)


#     sse_queue = Queue()

#     def generate():
#         while True:
#             message = sse_queue.get()
#             if message['status'] == "Completed":
#                 global global_image_array
#                 global_image_array = image.img_array
#                 print("sent")
#                 yield f"data: {message}\n\n"
#                 break
#             yield f"data: {json.dumps(message)}\n\n"
#     image_thread = ImageThread(image.getImage, sse_queue)
#     threading.Thread(target=image_thread.image_with_thread_pool, args=(50, image.roi_array)).start()
#     return Response(stream_with_context(generate(), mimetype='text/event-stream'))


@api_bp.route('/machine_learning', methods=['POST'])
def machineLearning():
    """
    Endpoint to get a Google Earth Engine image based on the region of interest (ROI).
    """
    data = request.json
    roi_data = data['roi_data']
    class_data = data['class_data']
    if api_bp.config['TESTING']:
        with open('testing/sample_test_json/masks/area_1.json', 'r') as file:
            class_data = json.load(file)
    image = session.get('image')
    image_mask = ImageMask(bands=image.bands, scale=image.scale, start_date=image.start_date, end_date=image.end_date)
    image_mask.setClassData(class_data)

    mask_queue = Queue()

    # For streaming the masks
    def generate():
        print("Starting stream...")
        while True:
            message = mask_queue.get()
            print(message)
            if message['status'] == "Completed":
                yield f"data: {json.dumps(message)}\n\n"
                print("Data sent, Closing connection")
                break
            yield f"data: {json.dumps(message)}\n\n"
    image_thread = ImageThread(helper=image_mask, queue=mask_queue)
    threading.Thread(target=image_thread.image_with_thread_pool, args=(50, image.img_array, True)).start()
    return Response(generate(), mimetype='text/event-stream')


@api_bp.route('/deep_learning', methods=['POST'])
def deepLearning():
    """
    Endpoint to get a Google Earth Engine image based on the region of interest (ROI).
    """
    class_data = request.json
    if api_bp.config['TESTING']:
        with open('testing/sample_test_json/masks/area_1.json', 'r') as file:
            class_data = json.load(file)
    image = session.get('image')
    image_mask = ImageMask(bands=image.bands, scale=image.scale, start_date=image.start_date, end_date=image.end_date)
    image_mask.setClassData(class_data)

    mask_queue = Queue()

    # For streaming the masks
    def generate():
        print("Starting stream...")
        while True:
            message = mask_queue.get()
            print(message)
            if message['status'] == "Completed":
                yield f"data: {json.dumps(message)}\n\n"
                print("Data sent, Closing connection")
                break
            yield f"data: {json.dumps(message)}\n\n"
    image_thread = ImageThread(helper=image_mask, queue=mask_queue)
    threading.Thread(target=image_thread.image_with_thread_pool, args=(50, image.img_array, True)).start()
    return Response(generate(), mimetype='text/event-stream')



# @api_bp.route('/get_mask_stream', methods=['GET'])
# def generate_mask():
#     """
#     Endpoint to generate a colored mask based on class data.
#     """

#     if 'image' in session:
#         image = session['image']
#         image_mask = session['image_mask']
#     else:
#         return 'Please select an ROI first. If the problem persist, enable cookies in the browser.', 400
    
#     mask_queue = Queue()
#     def generate():
#         while True:
#             message = mask_queue.get()
#             print(message)
#             if message['status'] == "Completed":
#                 yield f"data: {json.dumps(message)}\n\n"
#                 break
#             yield f"data: {json.dumps(message)}\n\n"
#     image_thread = ImageThread(helper=image_mask, queue=mask_queue)
#     global global_image_array
#     threading.Thread(target=image_thread.image_with_thread_pool, args=(4, global_image_array, True)).start()
#     return Response(generate(), mimetype='text/event-stream')

    # mask = Models(image.bands, image.scale, image.img_array, image.start_date, image.end_date)
    
    # try:
    #     mask.setClassData(class_data)  # Set the class data in the image
    #     colored_mask_pngs = mask.getColoredMask()  # Get the colored mask images
    # except Exception as e:
    #     return 'Error while generating mask. Please refresh and retry.', 400

    # response = defaultdict()
    # for key, value in colored_mask_pngs.items():
    #     area = get_area(value, mask.scale)  # Calculate area
    #     png_mask = preprocess(value, True)  # Preprocess the mask (Remove black background)
    #     base_64 = base64.b64encode(png_mask.getvalue()).decode('utf-8')  # Convert to base64
    #     response[key] = [base_64, 1, area]  # Build the response dictionary

    # # Empty the session variable
    # session.pop('image', None)
    # session.pop('band', None)
    # session.pop('scale', None)
    # session.pop('start_date', None)
    # session.pop('end_date', None)

    # return jsonify(response)

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

