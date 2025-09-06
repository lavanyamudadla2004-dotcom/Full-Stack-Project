from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import urllib.parse
import mysql.connector
import json
from fpdf import FPDF
import os

PORT = 8000

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",            # 👉 change if needed
        password="root123",     # 👉 change if needed
        database="exam_system"  # 👉 your database name
    )

class CombinedHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = urllib.parse.parse_qs(post_data)

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
                self.respond_json({"status": "success", "message": "Registered successfully!"})
            except mysql.connector.IntegrityError:
                self.respond_json({"status": "error", "message": "Username already exists!"})
            except Exception as e:
                self.respond_json({"status": "error", "message": str(e)})
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
                    self.respond_json({"status": "success", "message": "Login successful"})
                else:
                    self.respond_json({"status": "error", "message": "Invalid credentials."})
            except Exception as e:
                self.respond_json({"status": "error", "message": str(e)})
            finally:
                cur.close()
                conn.close()

        elif self.path == "/add_question":
            subject = data.get('subject', [''])[0]
            question = data.get('question', [''])[0]
            optionA = data.get('optionA', [''])[0]
            optionB = data.get('optionB', [''])[0]
            optionC = data.get('optionC', [''])[0]
            optionD = data.get('optionD', [''])[0]
            correct_option = data.get('correct_option', [''])[0]
            difficulty = data.get('difficulty', [''])[0]

            try:
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO questions (subject, question, optionA, optionB, optionC, optionD, correct_option, difficulty)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (subject, question, optionA, optionB, optionC, optionD, correct_option, difficulty))
                conn.commit()
                self.respond_json({'status': 'success', 'message': '✅ Question added successfully!'})
            except Exception as e:
                self.respond_json({'status': 'error', 'message': f'❌ DB Error: {str(e)}'})
            finally:
                cursor.close()
                conn.close()

        elif self.path == "/edit_question":
            # Edit question by ID
            qid = data.get('id', [''])[0]
            subject = data.get('subject', [''])[0]
            question = data.get('question', [''])[0]
            optionA = data.get('optionA', [''])[0]
            optionB = data.get('optionB', [''])[0]
            optionC = data.get('optionC', [''])[0]
            optionD = data.get('optionD', [''])[0]
            correct_option = data.get('correct_option', [''])[0]
            difficulty = data.get('difficulty', [''])[0]

            if not qid:
                self.respond_json({'status': 'error', 'message': 'Question ID required for edit'})
                return

            try:
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE questions
                    SET subject=%s, question=%s, optionA=%s, optionB=%s, optionC=%s, optionD=%s, correct_option=%s, difficulty=%s
                    WHERE id=%s
                """, (subject, question, optionA, optionB, optionC, optionD, correct_option, difficulty, qid))
                conn.commit()
                self.respond_json({'status': 'success', 'message': '✅ Question updated successfully!'})
            except Exception as e:
                self.respond_json({'status': 'error', 'message': f'❌ DB Error: {str(e)}'})
            finally:
                cursor.close()
                conn.close()

        elif self.path == "/delete_question":
            # Delete question by ID
            qid = data.get('id', [''])[0]
            if not qid:
                self.respond_json({'status': 'error', 'message': 'Question ID required for delete'})
                return
            try:
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM questions WHERE id=%s", (qid,))
                conn.commit()
                self.respond_json({'status': 'success', 'message': '✅ Question deleted successfully!'})
            except Exception as e:
                self.respond_json({'status': 'error', 'message': f'❌ DB Error: {str(e)}'})
            finally:
                cursor.close()
                conn.close()

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Invalid POST endpoint.")

    def do_GET(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/start_exam":
            query = parse_qs(parsed_url.query)
            subject = query.get("subject", [""])[0]
            difficulty = query.get("difficulty", [""])[0]

            if not subject or not difficulty:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing subject or difficulty.")
                return

            try:
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT question, optionA, optionB, optionC, optionD, correct_option
                    FROM questions
                    WHERE subject=%s AND difficulty=%s
                """, (subject, difficulty))
                questions = cursor.fetchall()

                if not questions:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"No questions found.")
                    return

                # Generate PDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, f"{subject} - {difficulty} Questions", ln=True, align='C')
                pdf.ln(10)

                for i, row in enumerate(questions, 1):
                    q, a, b, c, d, correct = row
                    pdf.multi_cell(0, 10, f"{i}. {q}")
                    pdf.cell(0, 10, f"A) {a}", ln=True)
                    pdf.cell(0, 10, f"B) {b}", ln=True)
                    pdf.cell(0, 10, f"C) {c}", ln=True)
                    pdf.cell(0, 10, f"D) {d}", ln=True)
                    pdf.cell(0, 10, f"Correct Answer: {correct}", ln=True)
                    pdf.ln(5)

                filename = f"{subject}_exam.pdf"
                pdf.output(filename)

                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header('Content-Type', 'application/pdf')
                self.send_header('Content-Disposition', f'attachment; filename={filename}')
                self.end_headers()
                with open(filename, "rb") as f:
                    self.wfile.write(f.read())
                os.remove(filename)

            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Server Error: {e}".encode())

        elif parsed_url.path == "/get_questions":
            try:
                conn = connect_db()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT id, subject, question, optionA, optionB, optionC, optionD, correct_option, difficulty FROM questions")
                rows = cursor.fetchall()

                data = {
                    "status": "success",
                    "questions": rows
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())

            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                error_msg = {"status": "error", "message": str(e)}
                self.wfile.write(json.dumps(error_msg).encode())
            finally:
                cursor.close()
                conn.close()

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Invalid endpoint.")

    def respond_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

# Start server
def run_server():
    print(f"🚀 Server running at http://localhost:{PORT}/")
    server = HTTPServer(('', PORT), CombinedHandler)
    server.serve_forever()

if __name__ == "__main__":
    run_server()