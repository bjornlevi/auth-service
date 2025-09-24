# wsgi.py
from app import create_app, bootstrap_defaults

app = create_app()
bootstrap_defaults(app)   # runs once with --preload
