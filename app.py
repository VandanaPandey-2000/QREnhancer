# from flask import Flask, request, render_template, send_file
# import os
# import subprocess
# import uuid

# app = Flask(__name__)

# UPLOAD_FOLDER = 'static'
# MAX_FILE_SIZE_MB = 2

# def is_file_size_valid(filepath, max_mb):
#     return os.path.getsize(filepath) <= max_mb * 1024 * 1024

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     result_path = os.path.join(UPLOAD_FOLDER, 'output.png')

#     if request.method == 'POST':
#         qr_file = request.files['qr']
#         embed_file = request.files['image']
#         seed = request.form.get('seed', '')

#         # Save uploaded files temporarily
#         qr_path = os.path.join(UPLOAD_FOLDER, f'qr_{uuid.uuid4().hex}.png')
#         embed_path = os.path.join(UPLOAD_FOLDER, f'img_{uuid.uuid4().hex}.png')

#         qr_file.save(qr_path)
#         embed_file.save(embed_path)

#         # Check file size limits
#         if not is_file_size_valid(qr_path, MAX_FILE_SIZE_MB):
#             os.remove(qr_path)
#             os.remove(embed_path)
#             return "QR code image is too large (limit 2 MB)."

#         if not is_file_size_valid(embed_path, MAX_FILE_SIZE_MB):
#             os.remove(qr_path)
#             os.remove(embed_path)
#             return "Embed image is too large (limit 2 MB)."

#         # Run the C++ binary
#         try:
#             subprocess.run(["./embed", qr_path, embed_path, result_path, seed], check=True)
#         except subprocess.CalledProcessError as e:
#             return f"Error in embedding: {e}"
#         finally:
#             # Clean up uploaded files
#             os.remove(qr_path)
#             os.remove(embed_path)

#         return render_template('index.html', result='output.png')

#     return render_template('index.html')
    

# @app.route('/download')
# def download():
#     path = os.path.join(UPLOAD_FOLDER, 'output.png')
#     return send_file(path, as_attachment=True)

# if __name__ == '__main__':
#     app.run(debug=True)

from flask import Flask, render_template, request, send_file
import os
import subprocess
from werkzeug.utils import secure_filename
from embed import embed 

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        qr_file = request.files.get('qr')
        embed_file = request.files.get('embed')
        try:                                        #edited: added try except
            blend_percent = int(request.form.get('blend', '30'))
        except ValueError:
            blend_percent = 30
        # blend_percent = int(request.form.get('blendpercent', 100))
        random_seed = request.form.get('seed', "")

        print(f"DEBUG: blend_percent={blend_percent}, random_seed='{random_seed}'") #edited: added line

        if not qr_file or not embed_file:
            return "Both QR and image to embed are required", 400

        qr_filename = secure_filename(qr_file.filename)
        embed_filename = secure_filename(embed_file.filename)

        qr_path = os.path.join(app.config['UPLOAD_FOLDER'], qr_filename)
        embed_path = os.path.join(app.config['UPLOAD_FOLDER'], embed_filename)
        output_path = os.path.join(STATIC_FOLDER, 'output.png')

        qr_file.save(qr_path)
        embed_file.save(embed_path)

        # cmd = ['./embed', qr_path, embed_path, output_path, str(blend_percent), random_seed]
        cmd = ['./embed', qr_path, embed_path, output_path, random_seed, str(blend_percent)]    #edited: order changed according to cpp
        print("DEBUG: Running command:", " ".join(cmd))
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0:
            return f"Error: {result.stderr.decode()}", 500

        return render_template('index.html', image_url='/static/output.png')

    return render_template('index.html', image_url=None)

@app.route('/download')
def download():
    return send_file('static/output.png', as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # use PORT from env or fallback to 5000
    app.run(host="0.0.0.0", port=port)
    # app.run(debug=True)
