import http.server
import socketserver
import json
import sqlite3
import math
import os
import uuid
import time
import random

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
    
    c.execute('DROP TABLE IF EXISTS sessions')
    c.execute('DROP TABLE IF EXISTS active_sessions')
    c.execute('''
        CREATE TABLE IF NOT EXISTS active_sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            duration_minutes INTEGER,
            start_time_ts INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            duration INTEGER,
            title TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

QUEST_VERBS = ["Slayed", "Defeated", "Mined", "Crafted", "Explored", "Conquered", "Researched"]
QUEST_ADJECTIVES = ["the Procrastination", "the Deep", "the Chaotic", "the Infinite", "the Forbidden"]
QUEST_NOUNS = ["Dragon", "Goblin", "Ore", "Artifact", "Dungeon", "Script", "Bug", "Algorithm"]

def generate_quest_title(duration_minutes):
    verb = random.choice(QUEST_VERBS)
    adj = random.choice(QUEST_ADJECTIVES)
    noun = random.choice(QUEST_NOUNS)
    return f"{verb} {adj} {noun} ({duration_minutes}m)"

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

def start_session(duration_minutes, db_path=DB_FILE):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    session_id = str(uuid.uuid4())
    start_time_ts = int(time.time())
    
    # clear existing active sessions for user 1
    c.execute("DELETE FROM active_sessions WHERE user_id = 1")
    
    c.execute("INSERT INTO active_sessions (id, user_id, duration_minutes, start_time_ts) VALUES (?, 1, ?, ?)", 
              (session_id, duration_minutes, start_time_ts))
    conn.commit()
    conn.close()
    return session_id, start_time_ts

def complete_session(session_id, db_path=DB_FILE):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT duration_minutes, start_time_ts FROM active_sessions WHERE id = ? AND user_id = 1", (session_id,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        raise ValueError("Invalid session ID or session already completed/abandoned.")
        
    duration_minutes, start_time_ts = row
    current_time_ts = int(time.time())
    
    # Strict Verification: Has enough real time passed?
    # duration_minutes * 60 seconds
    if current_time_ts - start_time_ts < (duration_minutes * 60):
        conn.close()
        raise ValueError(f"Anti-Cheat: You cannot complete a {duration_minutes}m session early!")
        
    # Valid! Clean up active session
    c.execute("DELETE FROM active_sessions WHERE id = ?", (session_id,))
    
    # Insert session history
    title = generate_quest_title(duration_minutes)
    c.execute('INSERT INTO sessions (user_id, duration, title) VALUES (1, ?, ?)', (duration_minutes, title))
    
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
    
    return get_user_stats(db_path), title

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
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b""
        
        try:
            request_data = json.loads(post_data) if post_data else {}
            
            if self.path == '/api/focus/start':
                session_time = request_data.get('session_time', 25)
                session_id, start_ts = start_session(session_time)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "session_id": session_id, "start_time_ts": start_ts}).encode())
                
            elif self.path == '/api/focus/complete':
                session_id = request_data.get('session_id')
                new_stats, title = complete_session(session_id)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "stats": new_stats, "quest_title": title}).encode())
                
            elif self.path == '/api/focus/dev-fast-forward':
                # Secret dev endpoint to fast forward time so we don't have to wait 25m to test
                session_id = request_data.get('session_id')
                minutes = request_data.get('minutes', 26)
                
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("UPDATE active_sessions SET start_time_ts = start_time_ts - ? WHERE id = ?", (minutes * 60, session_id))
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": f"Time traveled {minutes}m!"}).encode())
                
            else:
                self.send_response(404)
                self.end_headers()
                
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

if __name__ == "__main__":
    init_db()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), FocusHandler) as httpd:
        print(f"Serving Focus Flow at http://localhost:{PORT}")
        httpd.serve_forever()
