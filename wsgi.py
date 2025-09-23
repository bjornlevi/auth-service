# wsgi.py
from app import create_app

# Gunicorn will look for this variable by default: "wsgi:app"
app = create_app()

if __name__ == "__main__":
    # This lets you run it directly for local debugging:
    # python wsgi.py
    app.run(host="0.0.0.0", port=5000, debug=True)
