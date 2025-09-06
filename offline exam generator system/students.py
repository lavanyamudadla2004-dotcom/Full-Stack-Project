from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import mysql.connector
from fpdf import FPDF
import os

class ExamHandler(BaseHTTPRequestHandler):
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
                # 🛠️ Change DB details as needed
                conn = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="root123",  # your password
                    database="exam_system"
                )
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

                # 📝 Generate PDF
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

                filename=f"{subject}_exam.pdf"
                pdf.output(filename)

                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin","*")
                self.send_header('Content-Type', 'application/pdf')
                self.send_header('Content-Disposition', f'attachment; filename={filename}')
                self.end_headers()
                with open("filename", "rb") as f:
                    self.wfile.write(f.read())
                os.remove("filename")

            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Server Error: {e}".encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Invalid endpoint.")

def run():
    print("✅ Server running at http://localhost:8000/")
    server = HTTPServer(("", 8000), ExamHandler)
    server.serve_forever()

if __name__ == "__main__":
    run()