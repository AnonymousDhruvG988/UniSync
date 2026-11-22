import functools
import secrets
from flask import session, redirect, url_for, flash, request, abort, g, jsonify, current_app, make_response
from extensions import db
from models.users import User
from models.doubts import Notification, AuditLog

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return db.session.get(User, user_id)

def init_user_context():
    """Populate flask.g with current authenticated user and profile."""
    g.user = get_current_user()
    if g.user:
        g.student = g.user.student_profile if g.user.is_student else None
        g.teacher = g.user.teacher_profile if g.user.is_teacher else None
    else:
        g.student = None
        g.teacher = None

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('user_id') is None:
            # Preserve next destination
            next_url = request.full_path if request.method == 'GET' else request.path
            return redirect(url_for('auth.login', next=next_url))
        return view(**kwargs)
    return wrapped_view

def student_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('user_id') is None:
            next_url = request.full_path if request.method == 'GET' else request.path
            return redirect(url_for('auth.login', next=next_url))
        if session.get('user_role') != 'student':
            flash('Access restricted to university students.', 'error')
            return redirect(url_for('teacher.dashboard'))
        return view(**kwargs)
    return wrapped_view

def teacher_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('user_id') is None:
            next_url = request.full_path if request.method == 'GET' else request.path
            return redirect(url_for('auth.login', next=next_url))
        if session.get('user_role') != 'teacher':
            flash('Access restricted to university faculty members.', 'error')
            return redirect(url_for('student.dashboard'))
        return view(**kwargs)
    return wrapped_view

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

def validate_csrf():
    """Verify CSRF token for state-changing requests."""
    if current_app.config.get('TESTING') or not current_app.config.get('WTF_CSRF_ENABLED', True):
        return True
    
    if request.method in ('GET', 'HEAD', 'OPTIONS'):
        return True

    token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')
    expected_token = session.get('_csrf_token')

    if not expected_token or not token or not secrets.compare_digest(token, expected_token):
        if request.is_json or request.path.startswith('/api/'):
            abort(make_response(jsonify({'error': 'Invalid or expired security token (CSRF).'}), 400))
        flash('Security validation expired. Please resubmit the form.', 'error')
        return False
    return True

def log_audit(action, entity_type=None, entity_id=None, details=None):
    try:
        user_id = session.get('user_id')
        ip_addr = request.remote_addr if request else None
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()

def create_notification(user_id, title, message, link=None):
    try:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            link=link
        )
        db.session.add(notif)
        db.session.commit()
        return notif
    except Exception:
        db.session.rollback()
        return None
