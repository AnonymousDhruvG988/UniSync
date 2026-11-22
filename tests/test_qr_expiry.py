from datetime import timedelta
import pytest
from extensions import db, utcnow
from models.academic import ClassOffering
from models.feedback import FeedbackSession, FeedbackResponse
from tests.conftest import login_as

def test_exact_45_second_expiry_logic(app):
    with app.app_context():
        prog_a = ClassOffering.query.filter_by(join_code='PROG-A').first()
        now = utcnow()
        sess = FeedbackSession(
            class_offering_id=prog_a.id,
            started_at=now,
            expires_at=now + timedelta(seconds=45),
            status='active'
        )
        db.session.add(sess)
        db.session.commit()

        # Currently active
        assert sess.is_active_now is True
        assert sess.remaining_seconds > 0

        # Simulate time moving past 45 seconds
        sess.expires_at = now - timedelta(seconds=1)
        assert sess.is_active_now is False
        assert sess.remaining_seconds == 0
        assert sess.close_if_expired() is True
        assert sess.status == 'closed'

def test_rejection_after_45_second_expiry(client, app):
    with app.app_context():
        prog_a = ClassOffering.query.filter_by(join_code='PROG-A').first()
        now = utcnow()
        # Session expired 10 seconds ago
        sess = FeedbackSession(
            class_offering_id=prog_a.id,
            started_at=now - timedelta(seconds=55),
            expires_at=now - timedelta(seconds=10),
            status='active'
        )
        db.session.add(sess)
        db.session.commit()
        token = sess.session_token

    login_as(client, 'aarav.s@student.university.edu', 'Student@123')

    # Student tries to submit form
    response = client.post(f'/feedback/submit/{token}', data={
        'understanding': 'understood',
        'satisfaction': '5'
    }, follow_redirects=True)

    assert b'Expired' in response.data or b'concluded' in response.data

    with app.app_context():
        # Ensure no response recorded
        sess_db = FeedbackSession.query.filter_by(session_token=token).first()
        assert len(sess_db.responses) == 0
        assert sess_db.status == 'closed'

def test_polling_api_reports_expiration(client, app):
    with app.app_context():
        prog_a = ClassOffering.query.filter_by(join_code='PROG-A').first()
        now = utcnow()
        sess = FeedbackSession(
            class_offering_id=prog_a.id,
            started_at=now - timedelta(seconds=50),
            expires_at=now - timedelta(seconds=5),
            status='active'
        )
        db.session.add(sess)
        db.session.commit()
        token = sess.session_token

    response = client.get(f'/feedback/api/session/{token}/status')
    assert response.status_code == 200
    data = response.get_json()
    assert data['is_expired'] is True
    assert data['remaining_seconds'] == 0
    assert data['status'] == 'closed'
