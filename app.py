from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
from doc_ret import process_current_policy, search_policy
from policy_rec import recommend_policy_rag
from chatbot import start_chatbot, respond_to_query  # Import chatbot logic

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Store the latest uploaded policy PDF path
current_pdf_path = None

# Home page
@app.route('/')
def home():
    return render_template('home.html')  # Render the home page with buttons

# Chatbot Page
@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if request.method == 'POST':
        user_message = request.form['user_message']
        bot_reply = respond_to_query(user_message)  # Get bot response
        return render_template('chatbot.html', bot_reply=bot_reply)
    
    return render_template('chatbot.html', bot_reply=None)  # Initial state with no reply

# Document Upload and Search Page

@app.route('/doc_search', methods=['GET', 'POST'])
def doc_search():
    global current_pdf_path

    if request.method == 'POST':
        if 'pdf' in request.files:
            pdf = request.files['pdf']
            if pdf.filename != '':
                path = os.path.join(UPLOAD_FOLDER, pdf.filename)
                pdf.save(path)
                current_pdf_path = path
                process_current_policy(current_pdf_path)
        query = request.form.get('query')
        if query and current_pdf_path:
            summary = search_policy(query)
            return render_template('upload.html', summary=summary)
    
    return render_template('upload.html')


# Policy Recommendation Page
@app.route('/policy_recommend', methods=['GET', 'POST'])
def policy_recommend():
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            recommendation = recommend_policy_rag(query)
            return render_template('recommend.html', recommendation=recommendation)
    return render_template('recommend.html')

if __name__ == '__main__':
    app.run(debug=True)
