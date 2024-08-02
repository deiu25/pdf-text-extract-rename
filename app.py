from flask import Flask, request, jsonify, render_template, send_file, after_this_request
import pdfplumber
import re
import os
import zipfile

app = Flask(__name__)
UPLOAD_FOLDER = 'uploaded_files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
all_files_ready = False 

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def extract_series_number(content):
    match = re.search(r'Fattura fiscale:\s*(\S+)', content)
    if match:
        return match.group(1)
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    global all_files_ready
    all_files_ready = False 
    uploaded_files = request.files.getlist('files[]')
    responses = []
    for file in uploaded_files:
        if file and file.filename.endswith('.pdf'):
            new_filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(new_filename)
            try:
                with pdfplumber.open(new_filename) as pdf:
                    content = pdf.pages[0].extract_text()
                series_number = extract_series_number(content)
                if series_number:
                    final_filename = f"{series_number}.pdf"
                    os.rename(new_filename, os.path.join(app.config['UPLOAD_FOLDER'], final_filename))
                    responses.append({'new_name': final_filename, 'download_url': f'/download/{final_filename}'})
                else:
                    responses.append({'error': 'Series number not found'})
            except Exception as e:
                responses.append({'error': str(e)})
                os.remove(new_filename)
        else:
            responses.append({'error': 'Invalid file format'})
    all_files_ready = True  
    return jsonify(responses)

@app.route('/download-all', methods=['GET'])
def download_all_files():
    zip_filename = 'All_PDFs.zip'
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)

    # Crearea fișierului zip
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
            for file in files:
                if file.endswith('.pdf'):
                    zf.write(os.path.join(root, file), file)

    # Funcția de curățare a fișierelor
    def remove_files(response):
        try:
            os.remove(zip_path)  # Ștergerea fișierului ZIP
            for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
                for file in files:
                    if file.endswith('.pdf'):
                        os.remove(os.path.join(root, file))
        except Exception as e:
            app.logger.error('Eroare la ștergerea fișierelor: %s', str(e))
        return response

    # Aplicarea decoratorului
    @after_this_request
    def apply_remove_files(response):
        return remove_files(response)

    # Trimiterea fișierului zip către client
    return send_file(zip_path, as_attachment=True)

@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    try:
        for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
            for file in files:
                file_path = os.path.join(root, file)
                os.remove(file_path)
        return jsonify({'status': 'success', 'message': 'Files cleaned up successfully.'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/files-ready', methods=['GET'])
def check_files_ready():
    global all_files_ready
    return jsonify({'all_files_ready': all_files_ready})

if __name__ == '__main__':
    app.run(debug=True)
