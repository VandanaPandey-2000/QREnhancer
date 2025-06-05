from flask import Flask, render_template, request, send_file
import os
import subprocess
from werkzeug.utils import secure_filename
from embed import embed_image 

app = Flask(__name__)
# UPLOAD_FOLDER = 'uploads'
# STATIC_FOLDER = 'static'
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
STATIC_FOLDER = os.path.join(os.getcwd(), 'static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    print("DEBUG: Request received, method =", request.method)  
    if request.method == 'POST':
        print("a")
        qr_file = request.files.get('qr')
        print("b")
        embed_file = request.files.get('embed')

        if not qr_file or not embed_file:
            return "Both QR and image to embed are required", 400
             
        try:                                        #edited: added try except
            blend_percent = int(request.form.get('blend', '30'))
            print("c")
        except ValueError:
            blend_percent = 30
            print("d")
        # blend_percent = int(request.form.get('blendpercent', 100))
        random_seed = request.form.get('seed', "")

        print(f"DEBUG: blend_percent={blend_percent}, random_seed='{random_seed}'") #edited: added line

       

        qr_filename = secure_filename(qr_file.filename)
        embed_filename = secure_filename(embed_file.filename)
        print("f")

        qr_path = os.path.join(app.config['UPLOAD_FOLDER'], qr_filename)
        embed_path = os.path.join(app.config['UPLOAD_FOLDER'], embed_filename)
        output_path = os.path.join(STATIC_FOLDER, 'output1.png')
        print("g")

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(STATIC_FOLDER, exist_ok=True)
        print("h")

        qr_file.save(qr_path)
        embed_file.save(embed_path)
        print("i")

        try:
            print(f"Calling embed_image with: {qr_path}, {embed_path}, {output_path}, {blend_percent}, {random_seed}")
            embed_image(qr_path, embed_path, output_path, blend_percent, random_seed)
            print(f"Embedding succeeded, output at: {output_path}")
        except Exception as e:
            print(f"Embedding failed: {e}")
            return f"Error in embedding: {str(e)}", 500

        if os.path.exists(output_path):
            print("Output image exists, ready to display: {output_path}")
        else:
            print("Output image missing!")
            
        return render_template('index.html', image_url='/static/output1.png')
        print("j")

     # For GET requests, show the form without image
    return render_template('index.html', image_url=None)
    print("k")

@app.route('/download')
def download():
    return send_file('static/output1.png', as_attachment=True)
    

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # use PORT from env or fallback to 5000
    app.run(host="0.0.0.0", port=port)
    # app.run(debug=True)
