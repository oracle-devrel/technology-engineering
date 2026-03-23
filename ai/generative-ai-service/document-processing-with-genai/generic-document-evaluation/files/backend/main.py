from flask import Flask, request, jsonify
from flask_cors import CORS

from files.DocumentEvaluation import load_documents, evaluate
import pandas as pd
import io
import json

app = Flask(__name__)
CORS(app)

conversation_chain = None

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'service': 'Document Evaluation API'}

@app.route('/upload-documents', methods=['POST'])
def upload_documents():
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    global conversation_chain
    
    print("Upload to VectorStore")
    conversation_chain = load_documents(files)
    
    filenames = [file.filename for file in files if file.filename]
    
    return jsonify({
        'message': 'Documents uploaded and processed successfully',
        'files': filenames,
        'total_files': len(filenames),
        'status': 'success'
    })

@app.route('/evaluate', methods=['POST'])
def evaluate_documents():
    if 'criteria_file' not in request.files and 'criteria_json' not in request.form:
        return jsonify({'error': 'Missing required params `criteria_json` or `files`'}), 400

    criteria = None
    additional_instruction = None
    include_ranking = None
    criteria_file = request.files.get('criteria_file', None)
    criteria_json = request.form.get('criteria_json', None)
    additional_instruction = request.form.get('additional_instruction', None)
    include_ranking_marker = request.form.get('include_ranking', None)

    if criteria_file and not criteria_file.filename.lower().endswith(('.csv', '.json')):
        return jsonify({'error': 'Invalid criteria file. Please upload a CSV or JSON file'}), 400

    if criteria_file:
        if criteria_file.filename.endswith('.csv'):
            # Read as CSV (set your delimiter, e.g., ';')
            criteria = pd.read_csv(criteria_file, delimiter=';')
        elif criteria_file.filename.endswith('.json'):
            # Read as JSON (assuming it's a standard JSON file)
            # .read() gives bytes; decode to string if necessary
            file_content = criteria_file.read().decode('utf-8')
            criteria = pd.read_json(io.StringIO(file_content))
    else:
        # criteria = pd.read_json(io.StringIO(criteria_json))
        criteria = pd.DataFrame([json.loads(criteria_json)])


    response = evaluate(criteria, conversation_chain, additional_instruction, include_ranking_marker)
    
    evaluation_result = response.get('answer', str(response)) if isinstance(response, dict) else str(response)

    return jsonify({
        'message': 'Documents evaluated successfully',
        'evaluation': evaluation_result,
        'status': 'success'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)