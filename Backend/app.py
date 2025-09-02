from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
CORS(app)


# Database Configuration

db_config = {
    'host': 'localhost',
    'user': 'Falaye_Ifeoluwa',   
    'password': '1234',          
    'database': 'flashcardsDB'
}


# Database Setup

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**db_config)
        print("✅ Connection to MySQL DB successful")
    except Error as e:
        print(f"❌ Database error: {e}")
    return connection

def create_flashcards_table(connection):
    cursor = connection.cursor()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS flashcards (
      id INT AUTO_INCREMENT PRIMARY KEY,
      question TEXT NOT NULL,
      answer TEXT NOT NULL
    ) ENGINE=InnoDB;
    """
    try:
        cursor.execute(create_table_query)
        connection.commit()
        print("✅ Flashcards table ready")
    except Error as e:
        print(f"❌ Table creation error: {e}")

def save_flashcard(connection, question, answer):
    cursor = connection.cursor()
    add_card_query = """
    INSERT INTO flashcards (question, answer) VALUES (%s, %s)
    """
    try:
        cursor.execute(add_card_query, (question, answer))
        connection.commit()
        print(f"💾 Flashcard saved: {question}")
        return {'id': cursor.lastrowid, 'question': question, 'answer': answer}
    except Error as e:
        print(f"❌ Insert error: {e}")
        return None


# Load Hugging Face Q&A model

qa_model = None
try:
    qa_model = pipeline("question-answering", model="deepset/roberta-base-squad2")
    print("✅ Hugging Face Q&A model loaded successfully")
except Exception as e:
    print(f"❌ Error loading Hugging Face model: {e}")

# Connect to DB
conn = create_connection()
if conn:
    create_flashcards_table(conn)


# AI Q&A Flashcard Generation

def get_ai_generated_qa(notes):
    if not qa_model:
        print("❌ Model not available")
        return []

    # Example template questions
    question_templates = [
        "What is the main concept discussed?",
        "Explain the significance of this topic.",
        "What problem does this solve?",
        "what are the key takeaways?",
        "What are the challenges associated with this topic?",
    ]

    qa_pairs = []
    for q in question_templates:
        try:
            result = qa_model(question=q, context=notes)
            qa_pairs.append({
                "question": q,
                "answer": result.get("answer", "No answer found")
            })
        except Exception as e:
            qa_pairs.append({"question": q, "answer": f"Error: {e}"})

    return qa_pairs


# Routes

@app.route('/generate', methods=['POST'])
def generate_flashcards():
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    data = request.json
    if not data or 'notes' not in data:
        return jsonify({'error': 'No notes provided'}), 400

    notes = data['notes']
    generated_qas = get_ai_generated_qa(notes)

    saved_flashcards = []
    for qa in generated_qas:
        saved_card = save_flashcard(conn, qa['question'], qa['answer'])
        if saved_card:
            saved_flashcards.append(saved_card)

    return jsonify({'flashcards': saved_flashcards})

@app.route('/flashcards', methods=['GET'])
def get_flashcards():
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM flashcards")
    results = cursor.fetchall()
    return jsonify(results)


# Run App

if __name__ == '__main__':
    app.run(debug=True)