from flask import Blueprint, request, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_required, current_user
from models import db, Project, File, AuditLog
from werkzeug.utils import secure_filename
import os

files_bp = Blueprint('files', __name__)

ALLOWED_EXTENSIONS = {'png','jpg','jpeg','gif','pdf','docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def log_action(user_id, action):
    db.session.add(AuditLog(user_id=user_id, action=action))
    db.session.commit()

@files_bp.route('/project/<int:project_id>/upload', methods=['POST'])
@login_required
def upload_file(project_id):
    project = Project.query.get_or_404(project_id)
    if 'file' not in request.files:
        flash('No file part', 'warning')
        return redirect(url_for('projects.project_detail', project_id=project_id))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'warning')
        return redirect(url_for('projects.project_detail', project_id=project_id))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        project_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], f'project_{project_id}')
        os.makedirs(project_folder, exist_ok=True)
        filepath = os.path.join(project_folder, filename)
        file.save(filepath)
        db.session.add(File(project_id=project_id, filename=filename, filepath=filepath, uploaded_by=current_user.id))
        db.session.commit()
        log_action(current_user.id, f'Uploaded file {filename} to project {project.project_name}')
        flash('File uploaded successfully', 'success')
    else:
        flash('File type not allowed', 'warning')
    return redirect(url_for('projects.project_detail', project_id=project_id))

@files_bp.route('/uploads/<int:project_id>/<filename>')
@login_required
def download_file(project_id, filename):
    project_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], f'project_{project_id}')
    return send_from_directory(project_folder, filename, as_attachment=True)
