import pytest
from extensions import db
from models.academic import ClassOffering, Enrollment, Course
from models.users import User
from tests.conftest import login_as

def test_teacher_multiple_classes_mapping(app):
    with app.app_context():
        dr_sharma = User.query.filter_by(email='dr.sharma@university.edu').first()
        offerings = ClassOffering.query.filter_by(teacher_id=dr_sharma.teacher_profile.id).all()
        # Dr. Sharma teaches CS101 CSE-A, CS101 CSE-B, and CS201 CSE-A
        assert len(offerings) == 3
        codes = [o.course.code for o in offerings]
        assert 'CS101' in codes
        assert 'CS201' in codes

def test_student_multiple_subjects_mapping(app):
    with app.app_context():
        aarav = User.query.filter_by(email='aarav.s@student.university.edu').first()
        enrollments = Enrollment.query.filter_by(student_id=aarav.student_profile.id).all()
        # Aarav is enrolled in PROG-A, DATA-A, and PHYS-A
        assert len(enrollments) == 3
        course_codes = [e.class_offering.course.code for e in enrollments]
        assert 'CS101' in course_codes
        assert 'CS201' in course_codes
        assert 'PH101' in course_codes

def test_student_joins_class_with_code(client, app):
    # Student Diya (Sec B) is not enrolled in DATA-A (join code DATA-A)
    login_as(client, 'diya.p@student.university.edu', 'Student@123')
    
    response = client.post('/classes/join', data={
        'join_code': 'DATA-A'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Successfully enrolled' in response.data

    with app.app_context():
        diya = User.query.filter_by(email='diya.p@student.university.edu').first()
        data_a = ClassOffering.query.filter_by(join_code='DATA-A').first()
        enr = Enrollment.query.filter_by(student_id=diya.student_profile.id, class_offering_id=data_a.id).first()
        assert enr is not None

def test_duplicate_class_join_handled(client):
    login_as(client, 'aarav.s@student.university.edu', 'Student@123')
    # Aarav already enrolled in PROG-A
    response = client.post('/classes/join', data={
        'join_code': 'PROG-A'
    }, follow_redirects=True)

    assert b'already enrolled' in response.data

def test_teacher_cannot_access_unassigned_class(client, app):
    # Log in as Prof. Kapoor
    login_as(client, 'prof.kapoor@university.edu', 'Faculty@123')

    with app.app_context():
        # Get Dr. Sharma's class
        prog_a = ClassOffering.query.filter_by(join_code='PROG-A').first()
        target_id = prog_a.id

    response = client.get(f'/classes/{target_id}', follow_redirects=True)
    assert b'Access restricted. You are not assigned to instruct this course-section' in response.data

def test_student_cannot_access_unenrolled_class(client, app):
    # Log in as Diya (only enrolled in Sec B classes initially)
    login_as(client, 'diya.p@student.university.edu', 'Student@123')

    with app.app_context():
        prog_a = ClassOffering.query.filter_by(join_code='PROG-A').first()
        target_id = prog_a.id

    response = client.get(f'/classes/{target_id}', follow_redirects=True)
    assert b'Access restricted. You are not currently enrolled in this class' in response.data
