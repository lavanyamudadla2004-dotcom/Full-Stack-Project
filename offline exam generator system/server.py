from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import json
import mysql.connector

class MyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/add_question':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = urllib.parse.parse_qs(post_data)

            # Extract form data
            subject = data.get('subject', [''])[0]
            question = data.get('question', [''])[0]
            optionA = data.get('optionA', [''])[0]
            optionB = data.get('optionB', [''])[0]
            optionC = data.get('optionC', [''])[0]
            optionD = data.get('optionD', [''])[0]
            correct_option  = data.get('correct_option', [''])[0]
            difficulty = data.get('difficulty', [''])[0]

            try:
                # Connect to MySQL
                conn = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="root123",
                    database="exam_system"
                )
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO questions (subject, question, optionA, optionB, optionC, optionD, correct_option, difficulty)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (subject, question, optionA, optionB, optionC, optionD, correct_option, difficulty))
                conn.commit()
                cursor.close()
                conn.close()

                # ✅ Send JSON response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'message': '✅ Question added successfully!'}
                self.wfile.write(json.dumps(response).encode())

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'error': f'❌ Database error: {str(e)}'}
                self.wfile.write(json.dumps(response).encode())

        else:
            self.send_response(404)
            self.end_headers()

# Start server
def run():
    server_address = ('', 8000)  # http://localhost:8000
    httpd = HTTPServer(server_address, MyHandler)
    print("🚀 Server running at http://localhost:8000/")
    httpd.serve_forever()

if __name__ == '__main__':
    run()