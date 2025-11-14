"""
WSGI Entry Point
สำหรับ run ด้วย Gunicorn ใน production
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    # สำหรับ development เท่านั้น
    # Production ให้ใช้ Gunicorn
    app.run(debug=False, host='127.0.0.1', port=8000)
