# app/extras.py

import psutil

def log_resource_usage():

    cpu_usage = psutil.cpu_percent(interval=1)

    memory_info = psutil.virtual_memory()
    memory_usage = memory_info.percent
    total_memory = memory_info.total
    used_memory = memory_info.used
    resource_data = f'''
    <html>
        <head>
            <title>Memory Usage</title>
            <style>
                body {{
                    text-align: center;
                }}
                h2 {{
                    margin-top: 20px;
                }}
                p {{
                    font-size: 18px;
                }}
            </style>
        </head>
        <body>
            <h2>Resource Usage</h2>
            <br>
            <p>CPU Usage: {cpu_usage}%</p>
            <p>Memory Usage: {memory_usage}%</p>
            <p>Total Memory: {total_memory / (1024 ** 3):.2f} GB</p>  <!-- Convert bytes to GB -->
            <p>Used Memory: {used_memory / (1024 ** 3):.2f} GB</p>  <!-- Convert bytes to GB -->
        </body>
    </html>
    '''

    return resource_data

def intro():
    return '''
    <html>
        <head>
            <title>Segmentation</title>
            <style>
                body {{
                    text-align: center;
                }}
                h1 {{
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <h2>Semantic segmentation of satellite images using machine learning and deep learning models.</h2>
        </body>
    </html>
    '''