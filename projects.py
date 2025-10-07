from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
from models import db, Project, AuditLog, File
import pandas as pd
import os
import io

projects_bp = Blueprint('projects', __name__)

def log_action(user_id, action):
    db.session.add(AuditLog(user_id=user_id, action=action))
    db.session.commit()

def is_admin():
    return current_user.role == 'admin'

def can_edit_project():
    return current_user.role in ['admin', 'pm']

@projects_bp.route('/dashboard')
@login_required
def dashboard():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('dashboard.html', projects=projects)

@projects_bp.route('/<int:project_id>', methods=['GET','POST'])
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    if request.method == 'POST':
        # adding note (allowed for all roles)
        note = request.form.get('note')
        if note:
            project.notes = (project.notes or '') + f"\n[{current_user.username}] {note}"
            db.session.commit()
            log_action(current_user.id, f"Added note to project {project.project_name}")
            flash('Note added', 'success')
        return redirect(url_for('projects.project_detail', project_id=project_id))
    # fetch files for project
    files = File.query.filter_by(project_id=project.id).all()
    return render_template('project_detail.html', project=project, files=files, is_admin=is_admin())

@projects_bp.route('/add', methods=['GET','POST'])
@login_required
def add_project():
    if not can_edit_project():
        flash('Not authorized', 'warning')
        return redirect(url_for('projects.dashboard'))
    if request.method == 'POST':
        price_val = request.form.get('price') if is_admin() else None
        price = float(price_val) if price_val else None
        project = Project(
            project_name=request.form.get('project_name'),
            status=request.form.get('status'),
            poc=request.form.get('poc'),
            quote_number=request.form.get('quote_number'),
            po_number=request.form.get('po_number'),
            price=price,
            created_by=current_user.id
        )
        db.session.add(project)
        db.session.commit()
        log_action(current_user.id, f"Created project {project.project_name}")
        flash('Project created', 'success')
        return redirect(url_for('projects.dashboard'))
    return render_template('new_project.html', is_admin=is_admin())

@projects_bp.route('/export')
@login_required
def export_projects():
    if current_user.role not in ['admin','pm']:
        flash('Not authorized', 'warning')
        return redirect(url_for('projects.dashboard'))
    projects = Project.query.order_by(Project.project_name).all()
    rows = []
    for p in projects:
        row = {
            'project_name': p.project_name,
            'status': p.status or '',
            'notes': p.notes or '',
            'poc': p.poc or '',
            'quote_number': p.quote_number or '',
            'po_number': p.po_number or ''
        }
        if is_admin():
            row['price'] = p.price if p.price is not None else ''
        rows.append(row)
    df = pd.DataFrame(rows)
    mem = io.BytesIO()
    df.to_csv(mem, index=False)
    mem.seek(0)
    log_action(current_user.id, 'Exported projects to CSV')
    return send_file(mem, download_name='projects_export.csv', as_attachment=True, mimetype='text/csv')

@projects_bp.route('/import', methods=['GET','POST'])
@login_required
def import_projects():
    if current_user.role not in ['admin','pm']:
        flash('Not authorized', 'warning')
        return redirect(url_for('projects.dashboard'))
    if request.method == 'POST':
        f = request.files.get('csv_file')
        if not f:
            flash('No file uploaded', 'warning')
            return redirect(url_for('projects.import_projects'))
        content = f.read().decode('utf-8-sig')
        df = pd.read_csv(io.StringIO(content))
        created = 0
        updated = 0
        for idx, row in df.iterrows():
            name = str(row.get('project_name') or '').strip()
            if not name:
                continue
            # simple matching by project_name
            existing = Project.query.filter_by(project_name=name).first()
            if existing:
                existing.status = row.get('status') or existing.status
                existing.notes = row.get('notes') or existing.notes
                existing.poc = row.get('poc') or existing.poc
                existing.quote_number = row.get('quote_number') or existing.quote_number
                existing.po_number = row.get('po_number') or existing.po_number
                # only admin can update price
                if is_admin() and 'price' in row:
                    try:
                        existing.price = float(row.get('price'))
                    except Exception:
                        pass
                updated += 1
            else:
                price_val = None
                if is_admin() and 'price' in row:
                    try:
                        price_val = float(row.get('price'))
                    except Exception:
                        price_val = None
                p = Project(
                    project_name=name,
                    status=row.get('status'),
                    notes=row.get('notes'),
                    poc=row.get('poc'),
                    quote_number=row.get('quote_number'),
                    po_number=row.get('po_number'),
                    price=price_val,
                    created_by=current_user.id
                )
                db.session.add(p)
                created += 1
        db.session.commit()
        log_action(current_user.id, f'Imported CSV (created={created}, updated={updated})')
        flash(f'Import complete. Created: {created}. Updated: {updated}.', 'success')
        return redirect(url_for('projects.dashboard'))
    return render_template('import_projects.html', is_admin=is_admin())
