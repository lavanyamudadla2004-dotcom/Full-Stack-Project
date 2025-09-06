from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import json
import mysql.connector

PORT = 8000

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",          # change to your MySQL username
        password="root123", # change to your password
        database="exam_system"    # change to your database
    )

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode()
        data = parse_qs(post_data)

        if self.path == "/register":
            name = data.get("fullname", [""])[0]
            email = data.get("email", [""])[0]
            username = data.get("username", [""])[0]
            password = data.get("password", [""])[0]

            try:
                conn = connect_db()
                cur = conn.cursor()
                cur.execute("INSERT INTO users (name, email, username, password) VALUES (%s, %s, %s, %s)",
                            (name, email, username, password))
                conn.commit()
                self.respond({"status": "success", "message": "Registered successfully!"})
            except mysql.connector.IntegrityError:
                self.respond({"status": "error", "message": "Username already exists!"})
            except Exception as e:
                self.respond({"status": "error", "message": str(e)})
            finally:
                cur.close()
                conn.close()

        elif self.path == "/login":
            username = data.get("username", [""])[0]
            password = data.get("password", [""])[0]

            try:
                conn = connect_db()
                cur = conn.cursor()
                cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
                user = cur.fetchone()
                if user:
                    self.respond({"status": "success", "message": "Login successful"})
                else:
                    self.respond({"status": "error", "message": "User not registered or wrong credentials."})
            except Exception as e:
                self.respond({"status": "error", "message": str(e)})
            finally:
                cur.close()
                conn.close()

    def respond(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

if __name__ == "__main__":
    print("Server running at http://localhost:8080")
    HTTPServer(('', PORT), Handler).serve_forever()