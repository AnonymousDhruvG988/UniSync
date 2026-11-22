import pytest
from extensions import db
from models.academic import ClassOffering
from models.doubts import Doubt, DoubtReply, Notification
from models.users import User
from tests.conftest import login_as

def test_student_creates_question(client, app):
    login_as(client, 'aarav.s@student.university.edu', 'Student@123')

    with app.app_context():
        prog_a = ClassOffering.query.filter_by(join_code='PROG-A').first()
        class_id = prog_a.id

    response = client.post('/questions/create', data={
        'class_offering_id': class_id,
        'title': 'Binary tree traversal iterative versus recursive',
        'explanation': 'How does stack frame allocation impact memory consumption in depth-first search?'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'submitted to your instructor' in response.data

    with app.app_context():
        doubt = Doubt.query.filter_by(title='Binary tree traversal iterative versus recursive').first()
        assert doubt is not None
        assert doubt.status == 'new'
        assert doubt.student.roll_number == '24CSE001'

def test_assigned_teacher_views_and_answers_question(client, app):
    with app.app_context():
        # Retrieve doubt2 created in seed by Kabir (status 'new')
        doubt = Doubt.query.filter_by(title='Identifying base condition in recursive permutations').first()
        doubt_id = doubt.id
        assert doubt.status == 'new'

    # Dr. Sharma is the assigned teacher for this class
    login_as(client, 'dr.sharma@university.edu', 'Faculty@123')

    # Viewing the question moves status from 'new' to 'viewed'
    detail_resp = client.get(f'/questions/{doubt_id}')
    assert detail_resp.status_code == 200
    assert b'Identifying base condition in recursive permutations' in detail_resp.data

    with app.app_context():
        d_after = db.session.get(Doubt, doubt_id)
        assert d_after.status == 'viewed'

    # Teacher replies
    reply_resp = client.post(f'/questions/{doubt_id}/reply', data={
        'message': 'Prune permutations by sorting first and skipping identical adjacent elements.'
    }, follow_redirects=True)

    assert reply_resp.status_code == 200
    assert b'reply has been posted' in reply_resp.data

    with app.app_context():
        d_replied = db.session.get(Doubt, doubt_id)
        assert d_replied.status == 'answered'
        assert len(d_replied.replies) == 1
        assert d_replied.replies[0].message.startswith('Prune permutations')

        # Check in-app notification sent to Kabir
        kabir_user = User.query.filter_by(email='kabir.m@student.university.edu').first()
        notif = Notification.query.filter_by(user_id=kabir_user.id).order_by(Notification.created_at.desc()).first()
        assert notif is not None
        assert 'answered your question' in notif.message

def test_student_cannot_view_another_students_doubt(client, app):
    with app.app_context():
        # Doubt by Kabir
        doubt = Doubt.query.filter_by(title='Identifying base condition in recursive permutations').first()
        doubt_id = doubt.id

    # Log in as Diya
    login_as(client, 'diya.p@student.university.edu', 'Student@123')

    response = client.get(f'/questions/{doubt_id}', follow_redirects=True)
    assert b'Access restricted. You cannot view private questions' in response.data

def test_status_update_to_resolved(client, app):
    with app.app_context():
        # Doubt1 by Aarav is 'answered'
        doubt = Doubt.query.filter_by(title='Time complexity comparison between memoization and tabulation').first()
        doubt_id = doubt.id

    login_as(client, 'aarav.s@student.university.edu', 'Student@123')

    response = client.post(f'/questions/{doubt_id}/status', data={
        'status': 'resolved',
        'note': 'Concept understood after review'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        d_res = db.session.get(Doubt, doubt_id)
        assert d_res.status == 'resolved'
