import pytest
from extensions import db
from models.users import User, StudentProfile, TeacherProfile
from tests.conftest import login_as

def test_student_signup_success(client, app):
    response = client.post('/signup/student', data={
        'full_name': 'Devansh Singhania',
        'email': 'devansh.s@student.university.edu',
        'roll_number': '24CSE099',
        'programme': 'B.Tech Computer Science',
        'semester': '4',
        'section': 'A',
        'password': 'SecurePassword@123',
        'confirm_password': 'SecurePassword@123'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email='devansh.s@student.university.edu').first()
        assert user is not None
        assert user.is_student
        assert user.student_profile.roll_number == '24CSE099'

def test_teacher_signup_success(client, app):
    response = client.post('/signup/teacher', data={
        'full_name': 'Dr. Rohan Verma',
        'email': 'rohan.v@university.edu',
        'faculty_id': 'FAC-CS-88',
        'department': 'Computer Science & Engineering',
        'verification_key': 'FACULTY2026',
        'password': 'SecurePassword@123',
        'confirm_password': 'SecurePassword@123'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email='rohan.v@university.edu').first()
        assert user is not None
        assert user.is_teacher
        assert user.teacher_profile.faculty_id == 'FAC-CS-88'

def test_teacher_signup_invalid_key_fails(client, app):
    response = client.post('/signup/teacher', data={
        'full_name': 'Impostor User',
        'email': 'fake.teacher@university.edu',
        'faculty_id': 'FAC-FAKE-01',
        'department': 'Computer Science',
        'verification_key': 'WRONGKEY',
        'password': 'SecurePassword@123',
        'confirm_password': 'SecurePassword@123'
    }, follow_redirects=True)

    assert b'Invalid Faculty Verification Key' in response.data
    with app.app_context():
        assert User.query.filter_by(email='fake.teacher@university.edu').first() is None

def test_duplicate_email_rejected(client, app):
    response = client.post('/signup/student', data={
        'full_name': 'Duplicate User',
        'email': 'aarav.s@student.university.edu',  # Already exists in seed
        'roll_number': '24CSE888',
        'programme': 'B.Tech CSE',
        'semester': '4',
        'section': 'A',
        'password': 'SecurePassword@123',
        'confirm_password': 'SecurePassword@123'
    }, follow_redirects=True)

    assert b'already exists' in response.data

def test_duplicate_roll_number_rejected(client, app):
    response = client.post('/signup/student', data={
        'full_name': 'Duplicate Roll User',
        'email': 'unique.new@student.university.edu',
        'roll_number': '24CSE001',  # Already belongs to Aarav
        'programme': 'B.Tech CSE',
        'semester': '4',
        'section': 'A',
        'password': 'SecurePassword@123',
        'confirm_password': 'SecurePassword@123'
    }, follow_redirects=True)

    assert b'roll number already exists' in response.data

def test_invalid_login_credentials(client):
    response = login_as(client, 'aarav.s@student.university.edu', 'WrongPassword!')
    assert b'Invalid university email or password' in response.data

def test_student_login_redirect(client):
    response = login_as(client, 'aarav.s@student.university.edu', 'Student@123')
    assert response.status_code == 200
    assert b'Student Workspace' in response.data
    assert b'24CSE001' in response.data

def test_teacher_login_redirect(client):
    response = login_as(client, 'dr.sharma@university.edu', 'Faculty@123')
    assert response.status_code == 200
    assert b'Faculty Dashboard' in response.data
    assert b'FAC-CSE-01' in response.data

def test_logout_clears_session(client):
    login_as(client, 'aarav.s@student.university.edu', 'Student@123')
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been securely signed out' in response.data
    # Dashboard should redirect to login
    dash_resp = client.get('/student/dashboard', follow_redirects=False)
    assert dash_resp.status_code == 302
