import io
import csv
from datetime import datetime, timedelta
import qrcode
from PIL import Image
from flask import (
    Blueprint, render_template, request, redirect, url_for, session,
    flash, g, jsonify, abort, Response, current_app
)
from extensions import db, utcnow
from models.academic import ClassOffering, Enrollment
from models.feedback import FeedbackSession, FeedbackResponse
from models.doubts import Doubt
from auth_helpers import login_required, student_required, teacher_required, validate_csrf, log_audit, create_notification
from utils.analytics import compute_weekly_feedback_analytics

feedback_bp = Blueprint('feedback', __name__, url_prefix='/feedback')

@feedback_bp.route('/start/<int:class_id>', methods=['POST'])
@teacher_required
def start_session(class_id):
    if not validate_csrf():
        return redirect(url_for('classes.detail', class_id=class_id))

    offering = db.session.get(ClassOffering, class_id)
    if not offering:
        abort(404)

    # Security check: Teacher must own this class
    if offering.teacher_id != g.teacher.id:
        flash('Unauthorized. You can only initiate feedback for classes you teach.', 'error')
        return redirect(url_for('teacher.dashboard'))

    # Close any existing active sessions for this class offering
    for existing in offering.feedback_sessions:
        if existing.status == 'active':
            existing.status = 'closed'
    db.session.commit()

    # Exact duration configuration
    duration_sec = current_app.config.get('QR_FEEDBACK_DURATION_SECONDS', 45)
    now = utcnow()
    expires_at = now + timedelta(seconds=duration_sec)

    new_session = FeedbackSession(
        class_offering_id=offering.id,
        started_at=now,
        expires_at=expires_at,
        status='active'
    )
    db.session.add(new_session)
    db.session.commit()

    # Dispatch in-app notification to all enrolled students in this section
    enrollments = Enrollment.query.filter_by(class_offering_id=offering.id).all()
    for enr in enrollments:
        create_notification(
            user_id=enr.student.user_id,
            title=f"Live Class Feedback: {offering.course.code}",
            message=f"{offering.teacher.user.full_name} is taking feedback of today's class for {offering.course.name} ({offering.section.name}). Check in now before the 45-second timer ends.",
            link=url_for('feedback.scan_feedback', session_token=new_session.session_token)
        )

    log_audit('FEEDBACK_SESSION_START', 'FeedbackSession', new_session.id, f'Started 45s session for {offering.display_title}')
    return redirect(url_for('feedback.live_session', session_token=new_session.session_token))

@feedback_bp.route('/live/<session_token>')
@teacher_required
def live_session(session_token):
    sess = FeedbackSession.query.filter_by(session_token=session_token).first_or_404()
    offering = sess.class_offering

    # Security check: Teacher must own this class
    if offering.teacher_id != g.teacher.id:
        flash('Unauthorized. You cannot monitor this feedback session.', 'error')
        return redirect(url_for('teacher.dashboard'))

    # If already expired, redirect directly to results
    if sess.close_if_expired():
        db.session.commit()
        return redirect(url_for('feedback.results', session_token=sess.session_token))

    if sess.status == 'closed':
        return redirect(url_for('feedback.results', session_token=sess.session_token))

    # Calculate remaining seconds from server clock
    remaining = sess.remaining_seconds
    total_enrolled = len(offering.enrollments)
    responses_count = len(sess.responses)

    # Generate student scan URL
    scan_url = url_for('feedback.scan_feedback', session_token=sess.session_token, _external=True)

    return render_template(
        'feedback_live.html',
        session=sess,
        feedback_session=sess,
        offering=offering,
        remaining_seconds=remaining,
        total_enrolled=total_enrolled,
        responses_count=responses_count,
        scan_url=scan_url
    )

@feedback_bp.route('/qr/<session_token>.png')
def generate_qr(session_token):
    sess = FeedbackSession.query.filter_by(session_token=session_token).first_or_404()
    
    # Target URL encoded into QR
    scan_url = url_for('feedback.scan_feedback', session_token=sess.session_token, _external=True)

    # Build QR code with French Café aesthetic colors (Deep Espresso on Vanilla Cream)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=3,
    )
    qr.add_data(scan_url)
    qr.make(fit=True)

    # Deep Espresso: #514139 (RGB: 81, 65, 57), Vanilla White: #FFFCF8 (RGB: 255, 252, 248)
    img = qr.make_image(fill_color="#514139", back_color="#FFFCF8")

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    return Response(buf.getvalue(), mimetype='image/png')

@feedback_bp.route('/scan/<session_token>')
def scan_feedback(session_token):
    """The entry point for students who scan the QR code."""
    sess = FeedbackSession.query.filter_by(session_token=session_token).first_or_404()
    offering = sess.class_offering

    # 1. Authentication check: Must be signed in as a student
    if not session.get('user_id'):
        flash('Please sign in with your student university account to submit feedback.', 'info')
        return redirect(url_for('auth.login', next=request.full_path))

    if session.get('user_role') != 'student':
        flash('Faculty members cannot submit classroom feedback.', 'error')
        if offering.teacher_id == getattr(g.teacher, 'id', None):
            return redirect(url_for('feedback.live_session', session_token=session_token))
        return redirect(url_for('teacher.dashboard'))

    student = g.student
    if not student:
        flash('Student profile not found. Please log in again.', 'error')
        return redirect(url_for('auth.login'))

    # 2. Enrollment check: Student MUST be enrolled in this class offering
    enrollment = Enrollment.query.filter_by(
        student_id=student.id,
        class_offering_id=offering.id
    ).first()

    if not enrollment:
        return render_template(
            'feedback_error.html',
            title='Enrollment Required',
            heading='Not Enrolled in This Class',
            message=f'You are not currently enrolled in {offering.course.name} ({offering.section.name}). Please join this class using the join code provided by your instructor ({offering.join_code}) before participating in feedback.',
            back_url=url_for('student.dashboard'),
            join_code=offering.join_code
        )

    # 3. Expiration check: Server-side validation
    if sess.close_if_expired():
        db.session.commit()

    if not sess.is_active_now or sess.status == 'closed':
        return render_template(
            'feedback_error.html',
            title='Feedback Window Closed',
            heading='Session Expired',
            message=f'The 45-second feedback window for {offering.course.name} has concluded. Late submissions cannot be accepted to ensure authentic in-class timing.',
            back_url=url_for('classes.detail', class_id=offering.id)
        )

    # 4. Duplicate submission check
    already_submitted = FeedbackResponse.query.filter_by(
        session_id=sess.id,
        student_id=student.id
    ).first()

    if already_submitted:
        return render_template(
            'feedback_success.html',
            title='Feedback Already Recorded',
            heading='Thank You!',
            message=f'Your response for {offering.course.name} has already been registered at {already_submitted.submitted_at.strftime("%H:%M:%S")}. Each student may submit once per QR session.',
            response=already_submitted,
            class_id=offering.id
        )

    # 5. Display the form
    remaining_sec = sess.remaining_seconds
    return render_template(
        'feedback_form.html',
        session=sess,
        feedback_session=sess,
        offering=offering,
        student=student,
        remaining_seconds=remaining_sec
    )

@feedback_bp.route('/submit/<session_token>', methods=['POST'])
@student_required
def submit_feedback(session_token):
    sess = FeedbackSession.query.filter_by(session_token=session_token).first_or_404()
    offering = sess.class_offering
    student = g.student

    # Verify CSRF
    if not validate_csrf():
        return redirect(url_for('feedback.scan_feedback', session_token=session_token))

    # STRICT SERVER TIMER VALIDATION
    now = utcnow()
    if now > sess.expires_at or sess.status == 'closed':
        sess.status = 'closed'
        db.session.commit()
        if request.is_json:
            return jsonify({'success': False, 'error': 'Session expired. Response rejected.'}), 400
        return render_template(
            'feedback_error.html',
            title='Submission Window Expired',
            heading='Submission Window Expired',
            message='Your response was submitted after the strict 45-second server cutoff. The feedback window has closed.',
            back_url=url_for('classes.detail', class_id=offering.id)
        )

    # Verify enrollment
    enrollment = Enrollment.query.filter_by(
        student_id=student.id,
        class_offering_id=offering.id
    ).first()
    if not enrollment:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Student not enrolled.'}), 403
        flash('You must be enrolled in this class to submit feedback.', 'error')
        return redirect(url_for('student.dashboard'))

    # Verify duplicate submission
    existing = FeedbackResponse.query.filter_by(
        session_id=sess.id,
        student_id=student.id
    ).first()
    if existing:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Feedback already recorded.'}), 400
        flash('You have already submitted feedback for this session.', 'info')
        return redirect(url_for('classes.detail', class_id=offering.id))

    # Extract answers
    understanding = request.form.get('understanding', '').strip()
    satisfaction_raw = request.form.get('satisfaction', '').strip()
    concept_feedback = request.form.get('concept_feedback', '').strip()

    valid_understandings = ['understood', 'partially', 'needs_help']
    if understanding not in valid_understandings:
        flash('Please select an understanding level.', 'error')
        return redirect(url_for('feedback.scan_feedback', session_token=session_token))

    try:
        satisfaction = int(satisfaction_raw)
        if satisfaction < 1 or satisfaction > 5:
            raise ValueError()
    except ValueError:
        flash('Please select a valid satisfaction rating from 1 to 5.', 'error')
        return redirect(url_for('feedback.scan_feedback', session_token=session_token))

    try:
        response = FeedbackResponse(
            session_id=sess.id,
            student_id=student.id,
            understanding=understanding,
            satisfaction=satisfaction,
            concept_feedback=concept_feedback if concept_feedback else None,
            submitted_at=now
        )
        db.session.add(response)
        db.session.commit()

        log_audit(
            'FEEDBACK_SUBMIT',
            'FeedbackResponse',
            response.id,
            f'Student {student.roll_number} submitted feedback for Session {sess.id}'
        )

        if request.is_json:
            return jsonify({'success': True, 'response_id': response.id})

        return render_template(
            'feedback_success.html',
            title='Feedback Submitted Successfully',
            heading='Thank You, Feedback Recorded!',
            message=f'Your understanding feedback for {offering.course.name} ({offering.section.name}) has been delivered securely to {offering.teacher.user.full_name}.',
            response=response,
            class_id=offering.id
        )

    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'error': 'Database write failed.'}), 500
        flash('Failed to save your feedback. Please try again.', 'error')
        return redirect(url_for('feedback.scan_feedback', session_token=session_token))

@feedback_bp.route('/results/<session_token>')
@teacher_required
def results(session_token):
    sess = FeedbackSession.query.filter_by(session_token=session_token).first_or_404()
    offering = sess.class_offering

    # Security check: Teacher must own this class
    if offering.teacher_id != g.teacher.id:
        flash('Access denied. You can only view feedback analytics for your assigned classes.', 'error')
        return redirect(url_for('teacher.dashboard'))

    # Ensure status is closed
    if sess.status != 'closed':
        sess.status = 'closed'
        db.session.commit()

    total_enrolled = len(offering.enrollments)
    responses = sess.responses
    total_responses = len(responses)
    
    completion_pct = round((total_responses / total_enrolled * 100), 1) if total_enrolled > 0 else 0
    avg_satisfaction = sess.average_satisfaction
    breakdown = sess.understanding_breakdown

    # Compute weekly satisfaction trends for this class offering
    weekly_analytics = compute_weekly_feedback_analytics(offering.feedback_sessions)

    return render_template(
        'feedback_results.html',
        session=sess,
        feedback_session=sess,
        offering=offering,
        total_enrolled=total_enrolled,
        total_responses=total_responses,
        completion_pct=completion_pct,
        avg_satisfaction=avg_satisfaction,
        breakdown=breakdown,
        responses=responses,
        weekly_analytics=weekly_analytics
    )

@feedback_bp.route('/api/session/<session_token>/status')
def api_session_status(session_token):
    """Real-time polling endpoint for the teacher timer and participant count."""
    sess = FeedbackSession.query.filter_by(session_token=session_token).first_or_404()
    
    # Check if expired on server
    expired = sess.close_if_expired()
    if expired:
        db.session.commit()

    remaining = sess.remaining_seconds
    is_closed = sess.status == 'closed' or remaining <= 0

    return jsonify({
        'session_token': sess.session_token,
        'status': sess.status,
        'remaining_seconds': remaining,
        'response_count': len(sess.responses),
        'is_expired': is_closed,
        'results_url': url_for('feedback.results', session_token=sess.session_token)
    })

@feedback_bp.route('/export-csv/<session_token>')
@teacher_required
def export_csv(session_token):
    sess = FeedbackSession.query.filter_by(session_token=session_token).first_or_404()
    offering = sess.class_offering

    if offering.teacher_id != g.teacher.id:
        abort(403)

    output = io.StringIO()
    writer = csv.writer(output)

    # CSV Header
    writer.writerow([
        'Serial No',
        'Student Name',
        'Roll Number',
        'Course Code',
        'Course Name',
        'Section',
        'Submission Timestamp (UTC)',
        'Understanding Level',
        'Satisfaction Rating (1-5)',
        'Concept Feedback'
    ])

    # Rows of real submitted students
    for idx, resp in enumerate(sess.responses, start=1):
        writer.writerow([
            idx,
            resp.student_name,
            resp.student_roll_number,
            offering.course.code,
            offering.course.name,
            offering.section.name,
            resp.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
            resp.understanding.replace('_', ' ').title(),
            f"{resp.satisfaction}/5",
            resp.concept_feedback or ''
        ])

    csv_data = output.getvalue()
    filename = f"UniSync_Feedback_{offering.course.code}_{offering.section.name}_{sess.started_at.strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )
