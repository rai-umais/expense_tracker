"""
Kharcha Flask Application Entrypoint
Refactored to application factory architecture with full multi-user authentication,
database persistence, and financial transaction management.
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)