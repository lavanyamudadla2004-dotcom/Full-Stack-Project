from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import mysql.connector
import json

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/submit":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = urllib.parse.parse_qs(post_data)

            try:
                subject = data.get("subject", [""])[0]
                question = data.get("question", [""])[0]
                optionA = data.get("optionA", [""])[0]
                optionB = data.get("optionB", [""])[0]
                optionC = data.get("optionC", [""])[0]
                optionD = data.get("optionD", [""])[0]
                correct_option = data.get("correct_option", [""])[0]
                difficulty = data.get("difficulty", [""])[0]

                conn = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="root123",  # CHANGE THIS
                    database="exam_system"   # CHANGE THIS
                )

                cursor = conn.cursor()
                query = "INSERT INTO questions (subject, question, optionA, optionB, optionC, optionD, correct_option, difficulty) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                values = (subject, question, optionA, optionB, optionC, optionD, correct_option, difficulty)
                cursor.execute(query, values)
                conn.commit()

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"message": "✅ Question added successfully!"}).encode())

            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"❌ Error: {str(e)}"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

server = HTTPServer(('localhost', 8000), RequestHandler)
print("✅ Server running at http://localhost:8000")
server.serve_forever()



