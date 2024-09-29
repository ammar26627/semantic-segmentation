# app/application.py

from app import create_app

# Initialize the Flask application
app = create_app()

# Register the Blueprint with the main app

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
