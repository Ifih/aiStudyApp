# 🧠 AI Study Buddy

AI Study Buddy is a web application that helps you turn your study notes into interactive flashcards instantly using the power of AI.

The application has a simple user interface built with HTML and Tailwind CSS for styling. The core logic is handled by a Python backend using Flask, which integrates with a Hugging Face model to generate flashcards from user-provided notes.

## 🚀 Features

* **User Authentication**: Secure sign-up and sign-in functionality.
* **AI-Powered Flashcard Generation**: Paste your study notes and the application will generate question-and-answer flashcards.
* **Interactive Flashcards**: Flip flashcards to reveal the answer with a simple animation.
* **Persistent Storage**: Flashcards are saved to your user account and can be accessed later.

## 🛠️ Installation

### Prerequisites

* Python 3.8+
* A Hugging Face API token (optional, but recommended for best performance)

### Backend Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd ai-study-buddy
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the root directory and add the following:
    ```
    FLASK_SECRET=your_secure_random_key_here
    HF_API_TOKEN=your_hugging_face_api_token
    # Optional: for a production database
    # DATABASE_URL=your_database_url
    ```
    Replace `your_secure_random_key_here` with a random string and `your_hugging_face_api_token` with your actual token from the Hugging Face website.

### Running the Application

1.  **Ensure your virtual environment is activated.**
2.  **Run the Flask application:**
    ```bash
    python app.py
    ```
3.  The backend server will start and be accessible at `http://127.0.0.1:5001`. The frontend is served by the `index.html` file in the same directory. You can open `index.html` directly in your web browser.

## 📁 Project Structure

* `index.html`: The frontend user interface, including all HTML, CSS (via Tailwind CDN), and JavaScript logic.
* `app.py`: The Flask backend, handling user authentication, flashcard generation, and database interactions.
* `requirements.txt`: A list of all Python dependencies required to run the backend.

## 📄 License

This project is licensed under the MIT License.