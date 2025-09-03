# **AI Study Buddy**

## **Project Overview**

AI Study Buddy is a simple web application designed to help students create flashcards instantly from their study notes. The application leverages a backend API powered by Python and Flask to send notes to a powerful AI model, which then generates a set of questions and answers. The generated flashcards are saved to a MySQL database for future use and displayed on a clean, interactive frontend.

## **Features**

* **Intelligent Flashcard Generation:** Uses a text-generation model from Hugging Face to create relevant and insightful questions and answers from any study notes.  
* **Persistent Storage:** Saves all generated flashcards to a MySQL database, so you can revisit and review them later.  
* **Interactive Frontend:** A simple and clean user interface built with plain HTML, CSS, and JavaScript. Flashcards are interactive and can be flipped to reveal the answer.  
* **Clear and Responsive Design:** The frontend is designed to be easy to use and visually appealing on both desktop and mobile devices.

## **Tech Stack**

* **Frontend:** HTML5, CSS3, JavaScript  
* **Backend:** Python 3, Flask  
* **AI/NLP:** Hugging Face Transformers  
* **Database:** MySQL  
* **Dependencies:** flask, flask-cors, mysql-connector-python, transformers, torch, huggingface-hub, requests

## **Setup and Installation**

Follow these steps to get the application running on your local machine.

### **Prerequisites**

* Python 3.x  
* MySQL Server  
* A Hugging Face API key

### **1. Backend Setup**

1. **Clone the repository and navigate to the project directory.**  
   git clone <repo-url\>  
   cd <project-directory\>

2. **Create and activate a virtual environment (recommended).**  
   python -m venv venv  
   # On Windows  
   venv Scripts activate  
   # On macOS/Linux  
   source venv/bin/activate

3. **Install the required Python packages.**  
   pip install -r requirements.txt

4. **Set up your MySQL Database.**  
   * Ensure your MySQL server is running.  
   * Create a new database for the application.  
   * Update the db_config dictionary in app.py with database credentials.

db_config = {  
    "host": "localhost",  
    "user": "mysql_user",  
    "password": "mysql_password",  
    "database": "database_name"  
}

5. **Set your Hugging Face API key.**  
   * Add your Hugging Face API key to your system's environment variables.  
   * On macOS/Linux: export HF_API_KEY='your_api_key'  
   * On Windows: set HF_API_KEY='api_key'  
6. **Run the Flask application.**  
   python app.py

   The backend server will start and be accessible at http://localhost:5000.

### **2. Frontend Usage**

The frontend is a static application. Simply open the index.html file in your preferred web browser. Ensure the backend is running first.

## **Usage**

1. Open index.html in your web browser.  
2. Paste your study notes into the text area.  
3. Click the **Generate Flashcards** button.  
4. The application will display five interactive flashcards. Click on each card to flip it and reveal the answer.