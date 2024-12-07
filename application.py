# app/application.py

from app import create_app
import sys

debug = False
if len(sys.argv) > 1 and sys.argv[1] == "test":
    app = create_app(True)
    print("Running tests...")
else:
    app = create_app()




if __name__ == "__main__":

    app.run(debug=True, host='0.0.0.0', port=5001)
