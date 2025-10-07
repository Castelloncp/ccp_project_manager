from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from models import AuditLog, User

audit_bp = Blueprint('audit', __name__)

def is_admin():
    return current_user.role == 'admin'

@audit_bp.route('/audit')
@login_required
def view_audit():
    if not is_admin():
        flash('Not authorized', 'warning')
        return redirect(url_for('projects.dashboard'))
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    users = {u.id: u.username for u in User.query.all()}
    return render_template('audit_log.html', logs=logs, users=users)
