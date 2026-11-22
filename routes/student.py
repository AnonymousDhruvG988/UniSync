from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g, jsonify
from extensions import db
from models.users import User, StudentProfile
from models.academic import ClassOffering, Enrollment, Course, Section
from models.feedback import FeedbackSession, FeedbackResponse
from models.doubts import Doubt, DoubtReply, Notification
from auth_helpers import student_required, log_audit

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@student_required
def dashboard():
    student = g.student
    if not student:
        flash('Student profile not found. Please log in again.', 'error')
        return redirect(url_for('auth.login'))

    # Retrieve enrollments
    enrollments = Enrollment.query.filter_by(student_id=student.id).all()
    class_ids = [e.class_offering_id for e in enrollments]
    
    classes = ClassOffering.query.filter(ClassOffering.id.in_(class_ids)).all() if class_ids else []

    # Check for any currently active feedback sessions in enrolled classes
    active_sessions = []
    if class_ids:
        potential_sessions = FeedbackSession.query.filter(
            FeedbackSession.class_offering_id.in_(class_ids),
            FeedbackSession.status == 'active'
        ).all()
        for sess in potential_sessions:
            if sess.is_active_now:
                # Check if student already submitted
                already_submitted = FeedbackResponse.query.filter_by(
                    session_id=sess.id,
                    student_id=student.id
                ).first()
                if not already_submitted:
                    active_sessions.append(sess)
            else:
                sess.close_if_expired()
        db.session.commit()

    # Questions asked by this student
    my_questions = Doubt.query.filter_by(student_id=student.id).order_by(Doubt.created_at.desc()).limit(10).all()
    pending_questions_count = Doubt.query.filter(
        Doubt.student_id == student.id,
        Doubt.status.in_(['new', 'viewed'])
    ).count()

    # Recent answers from teachers
    answered_questions = Doubt.query.filter(
        Doubt.student_id == student.id,
        Doubt.status.in_(['answered', 'resolved'])
    ).order_by(Doubt.updated_at.desc()).limit(5).all()

    # Past submitted feedback count
    past_feedback_count = FeedbackResponse.query.filter_by(student_id=student.id).count()

    return render_template(
        'student_dashboard.html',
        student=student,
        classes=classes,
        active_sessions=active_sessions,
        my_questions=my_questions,
        pending_questions_count=pending_questions_count,
        answered_questions=answered_questions,
        past_feedback_count=past_feedback_count
    )

@student_bp.route('/classes')
@student_required
def classes():
    student = g.student
    enrollments = Enrollment.query.filter_by(student_id=student.id).all()
    class_ids = [e.class_offering_id for e in enrollments]
    classes = ClassOffering.query.filter(ClassOffering.id.in_(class_ids)).all() if class_ids else []
    return render_template('student_classes.html', student=student, classes=classes)

@student_bp.route('/questions')
@student_required
def questions():
    student = g.student
    status_filter = request.args.get('status', 'all')
    
    query = Doubt.query.filter_by(student_id=student.id)
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
        
    doubts = query.order_by(Doubt.created_at.desc()).all()
    
    # Also get enrolled classes for the 'Ask Question' modal
    enrollments = Enrollment.query.filter_by(student_id=student.id).all()
    class_ids = [e.class_offering_id for e in enrollments]
    enrolled_classes = ClassOffering.query.filter(ClassOffering.id.in_(class_ids)).all() if class_ids else []

    return render_template(
        'questions.html',
        is_teacher=False,
        doubts=doubts,
        status_filter=status_filter,
        enrolled_classes=enrolled_classes
    )

@student_bp.route('/profile')
@student_required
def profile():
    return render_template('profile.html', role='student', student=g.student, user=g.user)

@student_bp.route('/notifications')
@student_required
def notifications():
    user = g.user
    notifs = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(30).all()
    return render_template('notifications.html', notifications=notifs)

@student_bp.route('/api/notifications/mark-read/<int:notif_id>', methods=['POST'])
@student_required
def mark_notification_read(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=g.user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@student_bp.route('/api/active-feedback-check')
@student_required
def active_feedback_check():
    student = g.student
    if not student:
        return jsonify({'has_active': False, 'active_sessions': []})

    enrollments = Enrollment.query.filter_by(student_id=student.id).all()
    class_ids = [e.class_offering_id for e in enrollments]

    active_sessions = []
    if class_ids:
        sessions = FeedbackSession.query.filter(
            FeedbackSession.class_offering_id.in_(class_ids),
            FeedbackSession.status == 'active'
        ).all()
        for s in sessions:
            if s.is_active_now:
                # Check if student already submitted
                already = FeedbackResponse.query.filter_by(session_id=s.id, student_id=student.id).first()
                if not already:
                    active_sessions.append({
                        'session_token': s.session_token,
                        'class_id': s.class_offering_id,
                        'course_code': s.class_offering.course.code,
                        'course_name': s.class_offering.course.name,
                        'section_name': s.class_offering.section.name,
                        'teacher_name': s.class_offering.teacher.user.full_name,
                        'remaining_seconds': s.remaining_seconds,
                        'feedback_url': url_for('feedback.scan_feedback', session_token=s.session_token)
                    })
            else:
                s.close_if_expired()
        db.session.commit()

    return jsonify({
        'has_active': len(active_sessions) > 0,
        'active_sessions': active_sessions
    })

