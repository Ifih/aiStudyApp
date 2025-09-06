import os
import traceback
from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import requests
from sqlalchemy import create_engine

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')

# DATABASE configuration with fallback to sqlite if DATABASE_URL fails
db_uri = os.environ.get('DATABASE_URL')
if not db_uri:
    sqlite_path = os.path.join(os.path.dirname(__file__), 'dev_data.sqlite')
    db_uri = f"sqlite:///{sqlite_path}"
    print(f"[warning] DATABASE_URL not set. Using SQLite at: {sqlite_path}")

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Attempt a lightweight connection to the configured DB; fallback to SQLite on failure
try:
    engine = create_engine(db_uri)
    conn = engine.connect()
    conn.close()
    print(f"[info] Successfully connected to database: {db_uri}")
except Exception as e:
    sqlite_path = os.path.join(os.path.dirname(__file__), 'dev_data.sqlite')
    fallback = f"sqlite:///{sqlite_path}"
    app.config['SQLALCHEMY_DATABASE_URI'] = fallback
    print(f"[warning] Could not connect to DATABASE_URL ({e}). Falling back to SQLite at: {sqlite_path}")

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})


# --- DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    flashcards = db.relationship('Flashcard', backref='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.username}>'

class Flashcard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'question': self.question, 'answer': self.answer}


# --- HELPERS ---
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'message': 'Authentication required.'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


def hf_api_query(payload, api_url, headers=None):
    try:
        response = requests.post(api_url, headers=headers or {}, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[warning] Hugging Face API Error: {e}")
        return None


# --- ROUTES ---
@app.route("/")
def index():
    return "AI Study Buddy Backend is running!"


# --- AUTH ---
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify({'message': 'Missing username, email, or password.'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, email=email, password_hash=hashed_password)

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User created successfully.'}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Username or email already exists.'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'An error occurred: {e}'}), 500


@app.route('/api/auth/signin', methods=['POST'])
def signin():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Missing email or password.'}), 400

    user = User.query.filter_by(email=email).first()

    if user and bcrypt.check_password_hash(user.password_hash, password):
        session.permanent = True
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({'message': 'Login successful.', 'user': {'id': user.id, 'username': user.username}}), 200
    else:
        return jsonify({'message': 'Invalid email or password.'}), 401


@app.route('/api/auth/signout', methods=['POST'])
def signout():
    session.clear()
    return jsonify({'message': 'Successfully signed out.'}), 200


@app.route('/api/auth/status', methods=['GET'])
@login_required
def status():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if user:
        return jsonify({'isAuthenticated': True, 'user': {'id': user.id, 'username': user.username}}), 200
    return jsonify({'isAuthenticated': False}), 401


# --- FLASHCARD GENERATION ---
@app.route('/api/generate', methods=['POST'])
@login_required
def generate_flashcards():
    notes = (request.json or {}).get('notes', '')
    user_id = session.get('user_id')

    if not notes or not notes.strip():
        return jsonify({'message': 'Notes content is missing.'}), 400

    # Local transformers attempt
    TRANSFORMERS_AVAILABLE = False
    try:
        from transformers import pipeline
        TRANSFORMERS_AVAILABLE = True
    except Exception as e:
        print(f"[info] transformers not available locally: {e}")

    HF_API_TOKEN = os.environ.get('HF_API_TOKEN')
    QG_DEFAULT = os.environ.get('HF_Q_MODEL', 'mrm8488/t5-base-finetuned-question-generation-ap')
    QA_DEFAULT = os.environ.get('HF_A_MODEL', 'deepset/roberta-base-squad2')
    QG_API_URL = os.environ.get('QG_API_URL', f"https://api-inference.huggingface.co/models/{QG_DEFAULT}")
    QA_API_URL = os.environ.get('QA_API_URL', f"https://api-inference.huggingface.co/models/{QA_DEFAULT}")
    HF_HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"} if HF_API_TOKEN else {}

    LOCAL_QG_PIPELINE = None
    LOCAL_QA_PIPELINE = None
    LOCAL_MODELS_LOADED = False
    TRANSFORMERS_DEVICE = int(os.environ.get('TRANSFORMERS_DEVICE', '-1'))

    if TRANSFORMERS_AVAILABLE:
        try:
            q_model = os.environ.get('HF_Q_MODEL', QG_DEFAULT)
            a_model = os.environ.get('HF_A_MODEL', QA_DEFAULT)
            print(f"[info] Attempting to load local models: QG={q_model}, QA={a_model}")
            LOCAL_QG_PIPELINE = pipeline('text2text-generation', model=q_model, device=TRANSFORMERS_DEVICE)
            LOCAL_QA_PIPELINE = pipeline('question-answering', model=a_model, tokenizer=a_model, device=TRANSFORMERS_DEVICE)
            LOCAL_MODELS_LOADED = True
        except Exception as e:
            print(f"[warning] Failed to load local transformers models: {e}")
            traceback.print_exc()
            LOCAL_MODELS_LOADED = False

    generated_cards = []

    # 1) Try local pipelines
    if LOCAL_MODELS_LOADED and LOCAL_QG_PIPELINE and LOCAL_QA_PIPELINE:
        try:
            q_out = LOCAL_QG_PIPELINE(notes, max_length=256, do_sample=False)
            q_text = ''
            if isinstance(q_out, list) and len(q_out) and isinstance(q_out[0], dict):
                q_text = q_out[0].get('generated_text') or q_out[0].get('text') or ''
            elif isinstance(q_out, dict):
                q_text = q_out.get('generated_text') or q_out.get('text') or ''
            else:
                q_text = str(q_out)

            questions = [q.strip() for q in q_text.replace('\n', '.').split('.') if q.strip()][:5]
            if len(questions) < 5:
                questions += [f"What is key point {i+1}?" for i in range(len(questions), 5)]

            for q in questions[:5]:
                try:
                    a_out = LOCAL_QA_PIPELINE({'question': q, 'context': notes})
                    answer = a_out.get('answer') if isinstance(a_out, dict) else str(a_out)
                except Exception:
                    answer = q
                generated_cards.append({'question': q, 'answer': answer})
        except Exception as e:
            print(f"[warning] Local transformers generation failed: {e}")
            traceback.print_exc()
            generated_cards = []

    # 2) Try HF Inference API
    if not generated_cards and HF_API_TOKEN:
        try:
            qg_payload = {"inputs": notes}
            qg_response = hf_api_query(qg_payload, QG_API_URL, headers=HF_HEADERS)
            questions = []
            if qg_response and isinstance(qg_response, list) and isinstance(qg_response[0], dict) and 'generated_text' in qg_response[0]:
                q_text = qg_response[0]['generated_text']
                questions = [q.strip() for q in q_text.replace('\n', '.').split('.') if q.strip()][:5]
            if not questions:
                questions = [f"What is key point {i+1}?" for i in range(5)]

            for q in questions:
                qa_payload = {"inputs": {"question": q, "context": notes}}
                qa_response = hf_api_query(qa_payload, QA_API_URL, headers=HF_HEADERS)
                answer = None
                if qa_response and isinstance(qa_response, dict) and 'answer' in qa_response:
                    answer = qa_response['answer']
                elif isinstance(qa_response, list) and len(qa_response) and isinstance(qa_response[0], dict) and 'generated_text' in qa_response[0]:
                    answer = qa_response[0]['generated_text']
                if not answer:
                    answer = q
                generated_cards.append({'question': q, 'answer': answer})
        except Exception as e:
            print(f"[warning] HF inference generation failed: {e}")
            traceback.print_exc()
            generated_cards = []

    # 3) Fallback deterministic generator
    if not generated_cards:
        sentences = [s.strip() for s in notes.replace('\n', ' ').split('.') if s.strip()]
        for i in range(5):
            snippet = sentences[i] if i < len(sentences) else (sentences[-1] if sentences else '')
            if snippet:
                q = f"What is: {snippet[:120]}?"
                a = snippet
            else:
                q = f"What is key point {i+1}?"
                a = f"Key point {i+1}"
            generated_cards.append({'question': q, 'answer': a})

    # Ensure exactly 5 cards
    if len(generated_cards) < 5:
        generated_cards += generated_cards[:(5 - len(generated_cards))]
    generated_cards = generated_cards[:5]

    # Save to DB
    try:
        saved = []
        for card in generated_cards:
            fc = Flashcard(question=card['question'], answer=card['answer'], user_id=user_id)
            db.session.add(fc)
            saved.append({'question': card['question'], 'answer': card['answer']})
        db.session.commit()
        return jsonify(saved), 201
    except Exception as e:
        db.session.rollback()
        print(f"[error] Failed to save generated flashcards: {e}")
        traceback.print_exc()
        return jsonify({'message': f'Failed to save flashcard: {e}'}), 500


@app.route('/api/flashcards', methods=['GET'])
@login_required
def get_flashcards():
    user_id = session.get('user_id')
    flashcards = Flashcard.query.filter_by(user_id=user_id).order_by(Flashcard.id.desc()).all()
    return jsonify([card.to_dict() for card in flashcards]), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
