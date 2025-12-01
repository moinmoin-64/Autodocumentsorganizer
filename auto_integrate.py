#!/usr/bin/env python3
"""
Auto-Integration Script
Integriert logging_config und security_config automatisch in server.py und HTML-Dateien
"""

import re
from pathlib import Path


def integrate_server_py():
    """Integriert logging und security in server.py"""
    
    server_file = Path('app/server.py')
    content = server_file.read_text(encoding='utf-8')
    
    # 1. Imports hinzufügen
    imports_to_add = """from app.logging_config import setup_logging, log_request
from app.security_config import setup_security, add_security_headers

from apscheduler.schedulers.background import BackgroundScheduler
import time"""
    
    content = content.replace(
        "from apscheduler.schedulers.background import BackgroundScheduler",
        imports_to_add
    )
    
    # 2. Setup-Calls hinzufügen
    old_setup = """# Flask App
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Security Features
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-me-in-production')
csrf = CSRFProtect(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)"""
    
    new_setup = """# Flask App
app = Flask(__name__, static_folder='static', static_url_path='')

# Setup Logging (early!)
logger = setup_logging(app)

# Setup Security (includes CORS & rate limiting)
limiter = setup_security(app)

# Security Features
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-me-in-production')
csrf = CSRFProtect(app)"""
    
    content = content.replace(old_setup, new_setup)
    
    # 3. Middleware hinzufügen (vor if __name__)
    middleware = """

# === Request/Response Middleware ===

@app.before_request
def before_request_handler():
    \"\"\"Track request start time\"\"\"
    from flask import request
    request.start_time = time.time()


@app.after_request
def after_request_handler(response):
    \"\"\"Add security headers and log requests\"\"\"
    from flask import request
    
    # Add security headers
    response = add_security_headers(response)
    
    # Log request
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        log_request(request, response, duration)
    
    return response


# === Main ===

if __name__ == '__main__':"""
    
    content = content.replace("\n\nif __name__ == '__main__':", middleware)
    
    # Schreibe zurück
    server_file.write_text(content, encoding='utf-8')
    print("✅ server.py integriert!")


def integrate_html_files():
    """Fügt API Client und Error Handler zu allen HTML-Dateien hinzu"""
    
    html_files = [
        Path('app/static/index.html'),
        Path('app/static/login.html'),
        Path('app/static/photos.html')
    ]
    
    scripts_to_add = """    <!-- API Client & Error Handler -->
    <script src="/js/api-client.js"></script>
    <script src="/js/error-handler.js"></script>
"""
    
    for html_file in html_files:
        if not html_file.exists():
            print(f"⚠️  {html_file} nicht gefunden")
            continue
            
        content = html_file.read_text(encoding='utf-8')
        
        # Suche </body> Tag
        if '</body>' in content:
            # Füge vor </body> ein
            content = content.replace('</body>', f'{scripts_to_add}</body>')
            html_file.write_text(content, encoding='utf-8')
            print(f"✅ {html_file.name} aktualisiert!")
        else:
            print(f"⚠️  </body> nicht gefunden in {html_file.name}")


if __name__ == '__main__':
    print("🚀 Auto-Integration startet...")
    print()
    
    try:
        integrate_server_py()
        print()
        integrate_html_files()
        print()
        print("🎉 Integration abgeschlossen!")
        print()
        print("Nächste Schritte:")
        print("1. git add -A")
        print("2. git commit -m 'Auto-integrate logging, security, and frontend scripts'")
        print("3. git push")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
