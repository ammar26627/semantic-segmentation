# app/cpu_usage

import psutil

def log_resource_usage():
    # Get CPU usage
    cpu_usage = psutil.cpu_percent(interval=1)
    # Get memory usage
    memory_info = psutil.virtual_memory()
    memory_usage = memory_info.percent
    total_memory = memory_info.total
    used_memory = memory_info.used

    resource_data = {
        "cpu_usage": f"{cpu_usage}%",
        "memory_usage": f"{memory_usage}%",
        "total_memory_mb": f"{total_memory / (1024 ** 2):.2f} MB",
        "used_memory_mb": f"{used_memory / (1024 ** 2):.2f} MB"
    }

    return resource_data