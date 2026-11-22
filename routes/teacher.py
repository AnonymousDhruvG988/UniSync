from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g, jsonify
from extensions import db
from models.users import TeacherProfile
from models.academic import ClassOffering, Enrollment, Course, Section
from models.feedback import FeedbackSession, FeedbackResponse
from models.doubts import Doubt, Notification
from utils.analytics import compute_weekly_feedback_analytics
from auth_helpers import teacher_required, log_audit

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

@teacher_bp.route('/dashboard')
@teacher_required
def dashboard():
    teacher = g.teacher
    if not teacher:
        flash('Faculty profile not found. Please log in again.', 'error')
        return redirect(url_for('auth.login'))

    classes = ClassOffering.query.filter_by(teacher_id=teacher.id, is_active=True).all()
    class_ids = [c.id for c in classes]

    # Metrics calculation
    total_classes = len(classes)
    
    # Total unique or aggregated enrollments
    total_enrollments = Enrollment.query.filter(Enrollment.class_offering_id.in_(class_ids)).count() if class_ids else 0
    
    # Feedback sessions and responses
    sessions = FeedbackSession.query.filter(FeedbackSession.class_offering_id.in_(class_ids)).all() if class_ids else []
    session_ids = [s.id for s in sessions]
    
    total_responses = FeedbackResponse.query.filter(FeedbackResponse.session_id.in_(session_ids)).count() if session_ids else 0
    
    # Active feedback sessions right now
    active_sessions = []
    for s in sessions:
        if s.is_active_now:
            active_sessions.append(s)
        else:
            s.close_if_expired()
    db.session.commit()

    # Doubts / questions
    total_doubts = Doubt.query.filter(Doubt.class_offering_id.in_(class_ids)).count() if class_ids else 0
    unanswered_doubts = Doubt.query.filter(
        Doubt.class_offering_id.in_(class_ids),
        Doubt.status.in_(['new', 'viewed'])
    ).count() if class_ids else 0
    
    recent_doubts = Doubt.query.filter(Doubt.class_offering_id.in_(class_ids)).order_by(Doubt.created_at.desc()).limit(6).all() if class_ids else []

    # Build detailed statistics per class card
    class_cards_data = []
    for c in classes:
        c_sess_ids = [s.id for s in c.feedback_sessions]
        c_responses_count = FeedbackResponse.query.filter(FeedbackResponse.session_id.in_(c_sess_ids)).count() if c_sess_ids else 0
        c_unanswered = Doubt.query.filter(Doubt.class_offering_id == c.id, Doubt.status.in_(['new', 'viewed'])).count()
        class_cards_data.append({
            'offering': c,
            'enrolled_count': len(c.enrollments),
            'feedback_count': c_responses_count,
            'unanswered_count': c_unanswered,
            'active_session': next((s for s in c.feedback_sessions if s.is_active_now), None)
        })

    # Compute weekly satisfaction trends across all taught sessions
    weekly_analytics = compute_weekly_feedback_analytics(sessions)

    return render_template(
        'teacher_dashboard.html',
        teacher=teacher,
        classes_data=class_cards_data,
        total_classes=total_classes,
        total_enrollments=total_enrollments,
        total_responses=total_responses,
        unanswered_doubts=unanswered_doubts,
        active_sessions=active_sessions,
        recent_doubts=recent_doubts,
        weekly_analytics=weekly_analytics
    )

@teacher_bp.route('/classes')
@teacher_required
def classes():
    teacher = g.teacher
    classes = ClassOffering.query.filter_by(teacher_id=teacher.id, is_active=True).all()
    
    class_cards_data = []
    for c in classes:
        c_sess_ids = [s.id for s in c.feedback_sessions]
        c_responses_count = FeedbackResponse.query.filter(FeedbackResponse.session_id.in_(c_sess_ids)).count() if c_sess_ids else 0
        c_unanswered = Doubt.query.filter(Doubt.class_offering_id == c.id, Doubt.status.in_(['new', 'viewed'])).count()
        class_cards_data.append({
            'offering': c,
            'enrolled_count': len(c.enrollments),
            'feedback_count': c_responses_count,
            'unanswered_count': c_unanswered,
            'active_session': next((s for s in c.feedback_sessions if s.is_active_now), None)
        })

    # Also list available courses and sections for new class modal
    all_courses = Course.query.order_by(Course.code).all()
    all_sections = Section.query.order_by(Section.name).all()

    return render_template(
        'teacher_classes.html',
        teacher=teacher,
        classes_data=class_cards_data,
        all_courses=all_courses,
        all_sections=all_sections
    )

@teacher_bp.route('/questions')
@teacher_required
def questions():
    teacher = g.teacher
    status_filter = request.args.get('status', 'all')
    class_filter = request.args.get('class_id', 'all')

    classes = ClassOffering.query.filter_by(teacher_id=teacher.id, is_active=True).all()
    class_ids = [c.id for c in classes]

    if not class_ids:
        return render_template('questions.html', is_teacher=True, doubts=[], status_filter=status_filter, teacher_classes=[])

    query = Doubt.query.filter(Doubt.class_offering_id.in_(class_ids))

    if status_filter != 'all':
        query = query.filter(Doubt.status == status_filter)

    if class_filter != 'all':
        try:
            cid = int(class_filter)
            if cid in class_ids:
                query = query.filter(Doubt.class_offering_id == cid)
        except ValueError:
            pass

    doubts = query.order_by(Doubt.created_at.desc()).all()

    return render_template(
        'questions.html',
        is_teacher=True,
        doubts=doubts,
        status_filter=status_filter,
        class_filter=class_filter,
        teacher_classes=classes
    )

@teacher_bp.route('/feedback-results')
@teacher_required
def feedback_history():
    teacher = g.teacher
    classes = ClassOffering.query.filter_by(teacher_id=teacher.id).all()
    class_ids = [c.id for c in classes]

    sessions = []
    if class_ids:
        sessions = FeedbackSession.query.filter(
            FeedbackSession.class_offering_id.in_(class_ids)
        ).order_by(FeedbackSession.created_at.desc()).all()

    weekly_analytics = compute_weekly_feedback_analytics(sessions)

    return render_template('teacher_feedback_history.html', sessions=sessions, teacher=teacher, weekly_analytics=weekly_analytics)

@teacher_bp.route('/profile')
@teacher_required
def profile():
    return render_template('profile.html', role='teacher', teacher=g.teacher, user=g.user)
