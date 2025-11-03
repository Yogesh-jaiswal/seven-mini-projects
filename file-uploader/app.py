from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session
import os
from werkzeug.utils import secure_filename
import shutil

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ==========================================================
# CONFIGURATION
# ==========================================================
UPLOAD_FOLDER = 'uploads'          # Main folder for uploaded files
TEMP_FOLDER = 'uploads/temp'       # Temporary folder for files before final upload
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure main upload folder exists at startup
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==========================================================
# FILE DATA FUNCTION
# ==========================================================
def get_file_data(filename, file_path, is_temp=False):
    """
    Extracts details about a file for display.
    Returns a dictionary containing file metadata (name, type, color, size, etc.)
    """

    # Extract extension and assign a color based on file type
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    icons = {
        'pdf': '#FF5050', 'zip': '#F1C40F', 'doc': '#3498DB', 'docx': '#3498DB',
        'xls': '#2ECC71', 'xlsx': '#2ECC71', 'ppt': '#E67E22', 'pptx': '#E67E22',
        'txt': '#95A5A6', 'png': '#1ABC9C', 'jpg': '#1ABC9C', 'jpeg': '#1ABC9C', 'gif': '#1ABC9C'
    }
    color = icons.get(ext, 'BDC3C9')
    is_image = ext in ['png', 'jpg', 'jpeg', 'gif']

    # File size in KB (rounded)
    file_size_kb = round(os.path.getsize(file_path) / 1024, 2)

    # Build preview URL — decides which folder to serve from
    if is_temp:
        url = url_for('preview_file', file_path=filename, temp='true')
    else:
        url = url_for('preview_file', file_path=filename)

    return {
        'name': filename,
        'type': ext.upper(),
        'color': color,
        'is_image': is_image,
        'size': f"{file_size_kb} KB",
        'path': url
    }


# ==========================================================
# ROUTES
# ==========================================================

@app.route('/')
def index():
    """Home route — enables upload session and loads main page."""
    session["upload"] = True
    return render_template('index.html')


@app.route('/show_files')
def show_files():
    """Displays all permanently uploaded files."""
    file_details = []

    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file_info = get_file_data(filename, file_path)

            # Remove color code if no match found
            if file_info['color'] == 'BDC3C9':
                file_info['color'] = False

            file_details.append(file_info)

    return render_template("show_files.html", files=file_details)


@app.route('/upload', methods=['GET', 'POST'])
def files_page():
    """
    Handles temporary upload preview.
    POST → saves uploaded files to temp folder.
    GET → loads current temp files (if any).
    """
    if not session.get("upload"):
        return redirect("/")  # Prevent direct/back access if session expired

    if request.method == 'POST':
        uploaded_files = request.files.getlist('files')
        file_details = []

        os.makedirs(TEMP_FOLDER, exist_ok=True)

        for file in uploaded_files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                temp_path = os.path.join(TEMP_FOLDER, filename)
                file.save(temp_path)

                file_info = get_file_data(filename, temp_path, True)
                file_details.append(file_info)

        return render_template("upload.html", files=file_details)

    return render_template("upload.html", files=[])


@app.route('/uploads/<file_path>')
def preview_file(file_path):
    """
    Serves file previews from either temp or permanent folder.
    Uses ?temp=true to determine source folder.
    """
    temp = request.args.get('temp', 'false').lower() == 'true'
    folder = TEMP_FOLDER if temp else UPLOAD_FOLDER
    return send_from_directory(folder, file_path)


@app.route('/upload_files', methods=['POST'])
def upload_file():
    """
    Moves files from temp folder → main upload folder.
    Deletes temp folder after successful upload.
    """
    upload_path = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_path, exist_ok=True)

    if os.path.exists(TEMP_FOLDER) and len(os.listdir(TEMP_FOLDER)) != 0:
        for filename in os.listdir(TEMP_FOLDER):
            temp_file_path = os.path.join(TEMP_FOLDER, filename)
            final_path = os.path.join(upload_path, filename)
            shutil.move(temp_file_path, final_path)

        shutil.rmtree(TEMP_FOLDER)
        flash("✅ Files uploaded successfully!", "success")
    else:
        flash("⚠️ No files found to upload!", "warning")

    # End upload session to block back-button access
    session.pop("upload", None)

    return redirect('/')


@app.route('/delete_files')
def delete_files():
    """
    Deletes file from either temp or permanent folder.
    Controlled via query param ?temp=true
    """
    filename = request.args.get('filename')
    temp = request.args.get('temp', 'false').lower() == 'true'

    folder = TEMP_FOLDER if temp else UPLOAD_FOLDER
    file_path = os.path.join(folder, filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    # Redirect user to appropriate page
    if temp:
        return redirect('/upload')
    else:
        return redirect('/files_page')


@app.after_request
def add_no_cache_headers(response):
    """
    Prevents browser caching for upload routes.
    Ensures user can't access upload page via back button after session ends.
    """
    if request.path.startswith('/upload') or request.path.startswith('/upload_files'):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# ==========================================================
# RUN
# ==========================================================
if __name__ == '__main__':
    app.run(debug=True)