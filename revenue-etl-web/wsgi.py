"""
WSGI Entry Point
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    # For development only
    import os
    host = os.environ.get('APP_HOST', '0.0.0.0')
    port = int(os.environ.get('APP_PORT', 8000))
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'

    app.run(host=host, port=port, debug=debug)
