import http.server
import socketserver
import json
import sqlite3
import math
import os

PORT = 8000
DB_FILE = "focus_flow.db"

def init_db(db_path=DB_FILE):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            total_focus_time INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1
        )
    ''')
    # Create default user if not exists
    c.execute('SELECT COUNT(*) FROM users')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO users (id, total_focus_time, xp, level) VALUES (1, 0, 0, 1)')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            duration INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

def get_user_stats(db_path=DB_FILE):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT total_focus_time, xp, level FROM users WHERE id = 1')
    row = c.fetchone()
    conn.close()
    
    if not row:
        return {}
        
    total_time, current_xp, level = row
    
    # Calculate XP required for NEXT level: 100 * (level ^ 1.5)
    xp_for_next = int(100 * math.pow(level, 1.5))
    
    # Calculate XP required for CURRENT level to determine base of the progress bar
    xp_for_current = int(100 * math.pow(level - 1, 1.5)) if level > 1 else 0
    
    progress = 0
    if xp_for_next > xp_for_current:
        progress = ((current_xp - xp_for_current) / (xp_for_next - xp_for_current)) * 100
        
    return {
        "total_focus_time": total_time,
        "xp": current_xp,
        "level": level,
        "xp_required_for_next_level": xp_for_next,
        "xp_base_for_current_level": xp_for_current,
        "progress_percentage": round(min(100, max(0, progress)), 2)
    }

def add_session(duration_minutes, db_path=DB_FILE):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Insert session history
    c.execute('INSERT INTO sessions (user_id, duration) VALUES (1, ?)', (duration_minutes,))
    
    # Calculate XP (10 XP per minute)
    earned_xp = duration_minutes * 10
    
    # Get current stats
    c.execute('SELECT total_focus_time, xp, level FROM users WHERE id = 1')
    total_time, current_xp, current_level = c.fetchone()
    
    new_total_time = total_time + duration_minutes
    new_xp = current_xp + earned_xp
    
    # Recalculate Level (Infinite Scaling)
    new_level = current_level
    while True:
        xp_needed = int(100 * math.pow(new_level, 1.5))
        if new_xp >= xp_needed:
            new_level += 1
        else:
            break
            
    c.execute('''
        UPDATE users 
        SET total_focus_time = ?, xp = ?, level = ? 
        WHERE id = 1
    ''', (new_total_time, new_xp, new_level))
    
    conn.commit()
    conn.close()
    
    return get_user_stats(db_path)

class FocusHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/focus':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_user_stats()).encode())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/focus':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                request_data = json.loads(post_data)
                session_time = request_data.get('session_time', 0)
                
                new_stats = add_session(session_time)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "stats": new_stats}).encode())
                
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    init_db()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), FocusHandler) as httpd:
        print(f"Serving Focus Flow at http://localhost:{PORT}")
        httpd.serve_forever()
