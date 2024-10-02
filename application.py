# app/application.py

from app import create_app

# Initialize the Flask application
app = create_app()

if __name__ == "__main__":

    app.run(host='0.0.0.0', port=5001)
