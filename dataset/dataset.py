from gee_images import GeeImage
from image_thread import ImageThread
import threading, json, os, ee
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

def initialize_earth_engine():
    load_dotenv()
    data = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    credentials = json.loads(data)
    scopes = ['https://www.googleapis.com/auth/earthengine']
    credentials = Credentials.from_service_account_info(credentials, scopes= scopes)
    ee.Initialize(credentials)

class Dataset(GeeImage):
    def __init__(self, geoJson, name):
        super().__init__()
        self.file_name = name
        self.setRoiData(geoJson)

    def getData(self):
        image_thread = ImageThread(function=self.getImage, name=self.file_name)
        threading.Thread(target=image_thread.image_with_thread_pool, args=(4, self.roi_array)).start()

if 'name' == '__main__':
    initialize_earth_engine()
    file_name = 'Uttar_Pradesh'
    with open(f'./{file_name}.json') as f:
        data = json.load(f)
    os.makedirs(f'./images/{file_name}')
    os.makedirs(f'./masks/{file_name}')
    dataset = Dataset(data, file_name)
    dataset.getData()