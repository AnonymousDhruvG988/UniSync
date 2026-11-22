from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, g
from extensions import db
from models.users import User, StudentProfile, TeacherProfile
from auth_helpers import log_audit, validate_csrf

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    if session.get('user_id'):
        if session.get('user_role') == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        return redirect(url_for('student.dashboard'))
    return render_template('landing.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        if session.get('user_role') == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        return redirect(url_for('student.dashboard'))

    next_url = request.args.get('next', '')

    if request.method == 'POST':
        if not validate_csrf():
            return redirect(url_for('auth.login', next=next_url))

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both your university email and password.', 'error')
            return render_template('login.html', email=email, next=next_url)

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Invalid university email or password. Please try again.', 'error')
            return render_template('login.html', email=email, next=next_url)

        if not user.is_active:
            flash('Your account has been deactivated. Please contact academic administration.', 'error')
            return render_template('login.html', email=email, next=next_url)

        # Establish session
        session.clear()
        session['user_id'] = user.id
        session['user_role'] = user.role
        session['user_name'] = user.full_name
        session['user_email'] = user.email

        log_audit('USER_LOGIN', 'User', user.id, f'Login successful as {user.role}')

        flash(f'Welcome back, {user.full_name}.', 'success')

        # Prevent open redirect
        if next_url and next_url.startswith('/') and not next_url.startswith('//'):
            return redirect(next_url)

        if user.is_teacher:
            return redirect(url_for('teacher.dashboard'))
        return redirect(url_for('student.dashboard'))

    return render_template('login.html', next=next_url)

@auth_bp.route('/signup', methods=['GET'])
def signup():
    # Unified or default to student signup page
    role = request.args.get('role', 'student')
    return render_template('signup.html', default_role=role)

@auth_bp.route('/signup/student', methods=['POST'])
def signup_student():
    if not validate_csrf():
        return redirect(url_for('auth.signup', role='student'))

    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    roll_number = request.form.get('roll_number', '').strip().upper()
    programme = request.form.get('programme', '').strip()
    semester = request.form.get('semester', '').strip()
    section = request.form.get('section', '').strip().upper()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    # Validations
    if not all([full_name, email, roll_number, programme, semester, section, password, confirm_password]):
        flash('All fields are required for student registration.', 'error')
        return render_template('signup.html', default_role='student', form_data=request.form)

    try:
        semester_int = int(semester)
        if semester_int < 1 or semester_int > 12:
            raise ValueError()
    except ValueError:
        flash('Semester must be a valid number between 1 and 12.', 'error')
        return render_template('signup.html', default_role='student', form_data=request.form)

    if len(password) < 8:
        flash('Password must be at least 8 characters long.', 'error')
        return render_template('signup.html', default_role='student', form_data=request.form)

    if password != confirm_password:
        flash('Passwords do not match.', 'error')
        return render_template('signup.html', default_role='student', form_data=request.form)

    # Check duplicates
    if User.query.filter_by(email=email).first():
        flash('An account with this university email already exists.', 'error')
        return render_template('signup.html', default_role='student', form_data=request.form)

    if StudentProfile.query.filter_by(roll_number=roll_number).first():
        flash('A student profile with this roll number already exists.', 'error')
        return render_template('signup.html', default_role='student', form_data=request.form)

    # Create student account
    try:
        user = User(
            email=email,
            role='student',
            full_name=full_name
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        profile = StudentProfile(
            user_id=user.id,
            roll_number=roll_number,
            programme=programme,
            semester=semester_int,
            section=section
        )
        db.session.add(profile)
        db.session.commit()

        log_audit('STUDENT_REGISTER', 'User', user.id, f'Registered student roll {roll_number}')

        # Log in automatically
        session.clear()
        session['user_id'] = user.id
        session['user_role'] = user.role
        session['user_name'] = user.full_name
        session['user_email'] = user.email

        flash(f'Account created successfully. Welcome to UniSync, {user.full_name}!', 'success')
        return redirect(url_for('student.dashboard'))

    except Exception as e:
        db.session.rollback()
        flash('An unexpected error occurred during registration. Please try again.', 'error')
        return render_template('signup.html', default_role='student', form_data=request.form)

@auth_bp.route('/signup/teacher', methods=['POST'])
def signup_teacher():
    if not validate_csrf():
        return redirect(url_for('auth.signup', role='teacher'))

    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    faculty_id = request.form.get('faculty_id', '').strip().upper()
    department = request.form.get('department', '').strip()
    verification_key = request.form.get('verification_key', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    # Validations
    if not all([full_name, email, faculty_id, department, verification_key, password, confirm_password]):
        flash('All fields are required for faculty registration.', 'error')
        return render_template('signup.html', default_role='teacher', form_data=request.form)

    expected_key = current_app.config.get('FACULTY_VERIFICATION_KEY', 'FACULTY2026')
    if verification_key != expected_key:
        flash('Invalid Faculty Verification Key. Please consult your department chair or use demo key FACULTY2026.', 'error')
        return render_template('signup.html', default_role='teacher', form_data=request.form)

    if len(password) < 8:
        flash('Password must be at least 8 characters long.', 'error')
        return render_template('signup.html', default_role='teacher', form_data=request.form)

    if password != confirm_password:
        flash('Passwords do not match.', 'error')
        return render_template('signup.html', default_role='teacher', form_data=request.form)

    # Check duplicates
    if User.query.filter_by(email=email).first():
        flash('An account with this university faculty email already exists.', 'error')
        return render_template('signup.html', default_role='teacher', form_data=request.form)

    if TeacherProfile.query.filter_by(faculty_id=faculty_id).first():
        flash('A faculty profile with this Faculty ID already exists.', 'error')
        return render_template('signup.html', default_role='teacher', form_data=request.form)

    # Create faculty account
    try:
        user = User(
            email=email,
            role='teacher',
            full_name=full_name
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        profile = TeacherProfile(
            user_id=user.id,
            faculty_id=faculty_id,
            department=department
        )
        db.session.add(profile)
        db.session.commit()

        log_audit('TEACHER_REGISTER', 'User', user.id, f'Registered faculty {faculty_id}')

        # Log in automatically
        session.clear()
        session['user_id'] = user.id
        session['user_role'] = user.role
        session['user_name'] = user.full_name
        session['user_email'] = user.email

        flash(f'Faculty account verified and created. Welcome to UniSync, {user.full_name}!', 'success')
        return redirect(url_for('teacher.dashboard'))

    except Exception as e:
        db.session.rollback()
        flash('An unexpected error occurred during faculty registration. Please try again.', 'error')
        return render_template('signup.html', default_role='teacher', form_data=request.form)

@auth_bp.route('/demo-login/<role>')
def demo_login(role):
    """Convenient demo sign-in for evaluation and testing."""
    if role == 'teacher':
        user = User.query.filter_by(email='dr.sharma@university.edu').first()
    elif role == 'teacher2':
        user = User.query.filter_by(email='prof.kapoor@university.edu').first()
    elif role == 'student2':
        user = User.query.filter_by(email='riya.v@student.university.edu').first()
    else:
        user = User.query.filter_by(email='aarav.s@student.university.edu').first()

    if not user:
        flash('Demo database not seeded yet. Initializing demo accounts...', 'warning')
        from seed.seed_data import seed_database
        seed_database()
        return redirect(url_for('auth.demo_login', role=role))

    session.clear()
    session['user_id'] = user.id
    session['user_role'] = user.role
    session['user_name'] = user.full_name
    session['user_email'] = user.email

    flash(f'Signed in as demo account: {user.full_name} ({user.role.title()}).', 'success')
    next_url = request.args.get('next', '')
    if next_url and next_url.startswith('/') and not next_url.startswith('//'):
        return redirect(next_url)

    if user.is_teacher:
        return redirect(url_for('teacher.dashboard'))
    return redirect(url_for('student.dashboard'))

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    user_id = session.get('user_id')
    if user_id:
        log_audit('USER_LOGOUT', 'User', user_id, 'User logged out')
    session.clear()
    flash('You have been securely signed out.', 'success')
    return redirect(url_for('auth.landing'))

@auth_bp.route('/landing')
def landing():
    return render_template('landing.html')
