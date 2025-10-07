from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, User, AuditLog

users_bp = Blueprint('users', __name__)

def log_action(user_id, action):
    db.session.add(AuditLog(user_id=user_id, action=action))
    db.session.commit()

def is_admin():
    return current_user.role == 'admin'

@users_bp.route('/users')
@login_required
def manage_users():
    if not is_admin():
        flash('Not authorized', 'warning')
        return redirect(url_for('projects.dashboard'))
    users = User.query.order_by(User.username).all()
    return render_template('users.html', users=users)

@users_bp.route('/users/add', methods=['POST'])
@login_required
def add_user():
    if not is_admin():
        flash('Not authorized', 'warning')
        return redirect(url_for('projects.dashboard'))
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'warning')
    else:
        user = User(username=username, password_hash=generate_password_hash(password), role=role)
        db.session.add(user)
        db.session.commit()
        log_action(current_user.id, f'Added user {username} ({role})')
        flash('User added', 'success')
    return redirect(url_for('users.manage_users'))

@users_bp.route('/users/reset/<int:user_id>', methods=['POST'])
@login_required
def reset_password(user_id):
    if not is_admin():
        flash('Not authorized', 'warning')
        return redirect(url_for('projects.dashboard'))
    user = User.query.get_or_404(user_id)
    new_password = request.form['password']
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    log_action(current_user.id, f'Reset password for {user.username}')
    flash(f'Password reset for {user.username}', 'success')
    return redirect(url_for('users.manage_users'))
