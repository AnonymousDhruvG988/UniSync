from datetime import timedelta
import pytest
from extensions import db, utcnow
from models.academic import ClassOffering
from models.feedback import FeedbackSession, FeedbackResponse
from models.doubts import Notification
from models.users import User
from utils.analytics import compute_weekly_feedback_analytics
from tests.conftest import login_as

def test_teacher_starts_feedback_session(client, app):
    login_as(client, 'dr.sharma@university.edu', 'Faculty@123')
    
    with app.app_context():
        prog_a = ClassOffering.query.filter_by(join_code='PROG-A').first()
        class_id = prog_a.id

    response = client.post(f'/feedback/start/{class_id}', follow_redirects=False)
    assert response.status_code == 302
    assert '/feedback/live/' in response.location

    token = response.location.split('/')[-1]
    with app.app_context():
        sess = FeedbackSession.query.filter_by(session_token=token).first()
        assert sess is not None
        assert sess.status == 'active'
        diff = (sess.expires_at - sess.started_at).total_seconds()
        assert diff == 45

def test_qr_image_generation(client, app):
    with app.app_context():
        prog_a = ClassOffering.query.filter_by(join_code='PROG-A').first()
        sess = FeedbackSession(
            class_offering_id=prog_a.id,
            started_at=utcnow(),
            expires_at=utcnow() + timedelta(seconds=45),
            status='active'
        )
        db.session.add(sess)
        db.session.commit()
        token = sess.session_token

    response = client.get(f'/feedback/qr/{token}.png')
    assert response.status_code == 200
    assert response.content_type == 'image/png'
    assert len(response.data) > 100

def test_student_valid_feedback_submission(client, app):
    with app.app_context():
        prog_a = ClassOffering.query.filter_by(join_code='PROG-A').first()
        sess = FeedbackSession(
            class_offering_id=prog_a.id,
            started_at=utcnow(),
            expires_at=utcnow() + timedelta(seconds=45),
            status='active'
        )
        db.session.add(sess)
        db.session.commit()
        token = sess.session_token

    # Aarav is enrolled in PROG-A
    login_as(client, 'aarav.s@student.university.edu', 'Student@123')

    # Student opens form
    form_resp = client.get(f'/feedback/scan/{token}')
    assert form_resp.status_code == 200
    assert b'24CSE001' in form_resp.data

    # Submit feedback
    sub_resp = client.post(f'/feedback/submit/{token}', data={
        'understanding': 'understood',
        'satisfaction': '5',
        'concept_feedback': 'Recursion depth was explained clearly.'
    }, follow_redirects=True)

    assert sub_resp.status_code == 200
    assert b'Feedback Recorded' in sub_resp.data or b'Thank You' in sub_resp.data

    # Verify database
    with app.app_context():
        sess_db = FeedbackSession.query.filter_by(session_token=token).first()
        assert len(sess_db.responses) == 1
        resp = sess_db.responses[0]
        assert resp.student_roll_number == '24CSE001'
        assert resp.student_name == 'Aarav Sharma'
        assert resp.understanding == 'understood'
        assert resp.satisfaction == 5

def test_duplicate_submission_rejected(client, app):
    with app.app_context():
        prog_a = ClassOffering.query.filter_by(join_code='PROG-A').first()
        sess = FeedbackSession(
            class_offering_id=prog_a.id,
            started_at=utcnow(),
            expires_at=utcnow() + timedelta(seconds=45),
            status='active'
        )
        db.session.add(sess)
        db.session.commit()
        token = sess.session_token

    login_as(client, 'aarav.s@student.university.edu', 'Student@123')

    # First submission
    client.post(f'/feedback/submit/{token}', data={
        'understanding': 'understood',
        'satisfaction': '5'
    })

    # Second submission
    second_resp = client.post(f'/feedback/submit/{token}', data={
        'understanding': 'partially',
        'satisfaction': '3'
    }, follow_redirects=True)

    assert b'already submitted' in second_resp.data

def test_unenrolled_student_cannot_submit(client, app):
    with app.app_context():
        prog_a = ClassOffering.query.filter_by(join_code='PROG-A').first()
        sess = FeedbackSession(
            class_offering_id=prog_a.id,
            started_at=utcnow(),
            expires_at=utcnow() + timedelta(seconds=45),
            status='active'
        )
        db.session.add(sess)
        db.session.commit()
        token = sess.session_token

    # Diya is in Section B, not enrolled in PROG-A
    login_as(client, 'diya.p@student.university.edu', 'Student@123')

    scan_resp = client.get(f'/feedback/scan/{token}')
    assert b'Not Enrolled in This Class' in scan_resp.data

def test_csv_export_endpoint(client, app):
    # Log in as Dr. Sharma (assigned teacher for demo session in seed)
    login_as(client, 'dr.sharma@university.edu', 'Faculty@123')

    token = 'demo-session-prog-fundamentals-cse-a'
    response = client.get(f'/feedback/export-csv/{token}')
    assert response.status_code == 200
    assert response.content_type == 'text/csv; charset=utf-8'
    assert b'24CSE001' in response.data
    assert b'Aarav Sharma' in response.data
    assert b'Serial No' in response.data

def test_student_cannot_view_results_analytics(client):
    login_as(client, 'aarav.s@student.university.edu', 'Student@123')
    token = 'demo-session-prog-fundamentals-cse-a'
    response = client.get(f'/feedback/results/{token}', follow_redirects=True)
    assert b'Access restricted to university faculty members' in response.data

def test_enrolled_students_receive_notification_on_session_start(client, app):
    login_as(client, 'dr.sharma@university.edu', 'Faculty@123')

    with app.app_context():
        prog_a = ClassOffering.query.filter_by(join_code='PROG-A').first()
        class_id = prog_a.id

    client.post(f'/feedback/start/{class_id}', follow_redirects=False)

    with app.app_context():
        # Aarav, Riya, Kabir are enrolled in PROG-A
        aarav = User.query.filter_by(email='aarav.s@student.university.edu').first()
        notif = Notification.query.filter_by(user_id=aarav.id).order_by(Notification.created_at.desc()).first()
        assert notif is not None
        assert 'Live Class Feedback' in notif.title
        assert 'CS101' in notif.title

def test_student_active_feedback_check_api(client, app):
    with app.app_context():
        prog_a = ClassOffering.query.filter_by(join_code='PROG-A').first()
        sess = FeedbackSession(
            class_offering_id=prog_a.id,
            started_at=utcnow(),
            expires_at=utcnow() + timedelta(seconds=45),
            status='active'
        )
        db.session.add(sess)
        db.session.commit()

    # Aarav is enrolled in PROG-A
    login_as(client, 'aarav.s@student.university.edu', 'Student@123')
    resp = client.get('/student/api/active-feedback-check')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['has_active'] is True
    assert len(data['active_sessions']) > 0
    assert data['active_sessions'][0]['course_code'] == 'CS101'
    assert data['active_sessions'][0]['remaining_seconds'] > 0

def test_weekly_feedback_analytics_computation(app):
    with app.app_context():
        prog_a = ClassOffering.query.filter_by(join_code='PROG-A').first()
        analytics = compute_weekly_feedback_analytics(prog_a.feedback_sessions)

        assert analytics['has_data'] is True
        assert len(analytics['weekly_bars']) >= 1
        summary = analytics['summary']
        assert summary['overall_avg'] > 0.0
        assert summary['total_responses'] > 0
        # Check weekly bar fields
        first_bar = analytics['weekly_bars'][0]
        assert 'avg_satisfaction' in first_bar
        assert 'height_pct' in first_bar
        assert 'week_label' in first_bar
        assert 'und_pcts' in first_bar

