from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
CORS(app)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'Falaye_Ifeoluwa',
    'password': '1234',
    'database': 'flashcardsDB'
}


def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**db_config)
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
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
        print("Flashcards table created successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

# Load the text generation model
# The model will download on the first run.
generator = None
try:
    generator = pipeline('text-generation', model='distilgpt2')
    print("Hugging Face model loaded successfully.")
except Exception as e:
    print(f"Error loading Hugging Face model: {e}")

# Database connection and table creation
conn = create_connection()
if conn:
    create_flashcards_table(conn)

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**db_config)
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
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
        print("Flashcards table created successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

def save_flashcard(connection, question, answer):
    cursor = connection.cursor()
    add_card_query = """
    INSERT INTO flashcards (question, answer) VALUES (%s, %s)
    """
    card_data = (question, answer)
    try:
        cursor.execute(add_card_query, card_data)
        connection.commit()
        print(f"Flashcard '{question}' saved successfully.")
        return {'id': cursor.lastrowid, 'question': question, 'answer': answer}
    except Error as e:
        print(f"The error '{e}' occurred")
        return None

def get_ai_generated_qa(notes):
    if not generator:
        print("Hugging Face model is not available")
        return []

    prompt = f"From the following notes, generate 5 questions and answers. \n\nNotes: {notes}\n\nQuestions & Answers:"
    generated_text = generator(
        prompt,
        max_length=200,
        num_return_sequences=1,
        truncation=True
    )
    text = generated_text[0]['generated_text']
    qa_pairs = []
    lines = text.split('\n')
    for line in lines:
        if line.strip():
            parts = line.split('?', 1)
            if len(parts) == 2:
                question = parts[0].strip() + '?'
                answer = parts[1].strip()
                qa_pairs.append({'question': question, 'answer': answer})
    return qa_pairs


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


if __name__ == '__main__':
    app.run(debug=True)