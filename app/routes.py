# app/route.py

# from app import socketio
from flask import jsonify, request, Blueprint, session, Response, stream_with_context, current_app
from app.extras import log_resource_usage, intro
from app.mask import ImageMask
from app.gee_image import GeeImage
import json, threading
from queue import Queue
from app.threading import ImageThread
from app.subpolygon import SubPolygon
# from keras import models
# from keras import preprocessing


ip_set = set()

# Create a Blueprint for routes
api_bp = Blueprint('api', __name__)


@api_bp.route("/images", methods=['POST'])
def image_url():
    url_data = request.json
    image = GeeImage()
    image.setRoiData(url_data)  # Set the ROI in the image
    image_url = image.getImageUrl()  # Fetch the image based on ROI
    response = {f"image_url": str(image_url), "access_token": current_app.config['ACCESS_TOKEN']}
    session["image"] = image
    return jsonify(response), 200



@api_bp.route('/machine_learning', methods=['POST'])
def machineLearning():
    """
    Endpoint to get a Google Earth Engine image based on the region of interest (ROI).
    """
    data = request.json
    class_data = data['classGeojson']
    roi_data = data['roi']
    print(data)
    image = session.get('image')
    if not image.img_array:
        roi = roi_data['geometry']['coordinates'][0] 
        polygon_array = SubPolygon(roi)
        image.roi_array = polygon_array.getSubPolygons()
    image_mask = ImageMask(bands=image.bands, start_date=image.start_date, end_date=image.end_date)
    image_mask.setClassData(class_data)
    session['image_mask'] = image_mask
    return jsonify({"status": "Class data set."}), 200

@api_bp.route('/machine_learning_stream', methods=['GET'])
def machineLearningStream():
    """
    Endpoint to get a Google Earth Engine image based on the region of interest (ROI).
    """
    image = session.get('image')
    image_mask = session.get('image_mask')

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
    image_thread = ImageThread(img_object=image, mask_object=image_mask, queue=mask_queue)
    if not image.img_array:
        function = 'ml'
        items = image.roi_array
    else:
        function = 'image_ml'
        items = image.img_array
    threading.Thread(target=image_thread.thread_pool, args=(50, items, function)).start()
    return Response(stream_with_context(generate()), content_type='text/event-stream')


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
    threading.Thread(target=image_thread.thread_pool, args=(50, image.img_array, True)).start()
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

