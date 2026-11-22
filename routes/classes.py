from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g, abort
from extensions import db
from models.users import User, StudentProfile, TeacherProfile
from models.academic import ClassOffering, Course, Section, Enrollment, generate_join_code
from models.feedback import FeedbackSession, FeedbackResponse
from models.doubts import Doubt, Notification
from auth_helpers import login_required, student_required, teacher_required, validate_csrf, log_audit
from utils.analytics import compute_weekly_feedback_analytics

classes_bp = Blueprint('classes', __name__, url_prefix='/classes')

@classes_bp.route('/<int:class_id>')
@login_required
def detail(class_id):
    offering = db.session.get(ClassOffering, class_id)
    if not offering:
        abort(404)
    user = g.user

    # Strict authorization check
    is_teacher_owner = False
    is_enrolled_student = False

    if user.is_teacher:
        if not g.teacher or offering.teacher_id != g.teacher.id:
            flash('Access restricted. You are not assigned to instruct this course-section.', 'error')
            return redirect(url_for('teacher.dashboard'))
        is_teacher_owner = True
    elif user.is_student:
        enrollment = Enrollment.query.filter_by(
            student_id=g.student.id,
            class_offering_id=offering.id
        ).first()
        if not enrollment:
            flash('Access restricted. You are not currently enrolled in this class.', 'error')
            return redirect(url_for('student.dashboard'))
        is_enrolled_student = True
    else:
        abort(403)

    # Check active feedback session
    active_session = None
    for sess in offering.feedback_sessions:
        if sess.is_active_now:
            active_session = sess
            break
        else:
            sess.close_if_expired()
    db.session.commit()

    # Student specific submission status for active session
    has_submitted_active = False
    if is_enrolled_student and active_session:
        has_submitted_active = FeedbackResponse.query.filter_by(
            session_id=active_session.id,
            student_id=g.student.id
        ).first() is not None

    # Load questions
    if is_teacher_owner:
        # Teacher sees all student questions for this class
        doubts = Doubt.query.filter_by(class_offering_id=offering.id).order_by(Doubt.created_at.desc()).all()
    else:
        # Student sees only their own questions for this class (privacy rule)
        doubts = Doubt.query.filter_by(
            class_offering_id=offering.id,
            student_id=g.student.id
        ).order_by(Doubt.created_at.desc()).all()

    # Load feedback history
    past_sessions = FeedbackSession.query.filter(
        FeedbackSession.class_offering_id == offering.id,
        FeedbackSession.status == 'closed'
    ).order_by(FeedbackSession.created_at.desc()).all()

    # Student's past responses
    my_responses = []
    if is_enrolled_student:
        my_responses = FeedbackResponse.query.join(FeedbackSession).filter(
            FeedbackSession.class_offering_id == offering.id,
            FeedbackResponse.student_id == g.student.id
        ).order_by(FeedbackResponse.submitted_at.desc()).all()

    # Enrolled students for teacher view
    enrolled_students = []
    if is_teacher_owner:
        enrollments = Enrollment.query.filter_by(class_offering_id=offering.id).all()
        enrolled_students = [e.student for e in enrollments]

    # Compute weekly satisfaction trends for this class offering
    weekly_analytics = compute_weekly_feedback_analytics(offering.feedback_sessions)

    return render_template(
        'class_detail.html',
        offering=offering,
        is_teacher=is_teacher_owner,
        is_student=is_enrolled_student,
        active_session=active_session,
        has_submitted_active=has_submitted_active,
        doubts=doubts,
        past_sessions=past_sessions,
        my_responses=my_responses,
        enrolled_students=enrolled_students,
        weekly_analytics=weekly_analytics
    )

@classes_bp.route('/join', methods=['POST'])
@student_required
def join():
    if not validate_csrf():
        return redirect(url_for('student.dashboard'))

    join_code = request.form.get('join_code', '').strip().upper()
    if not join_code:
        flash('Please enter a valid class join code.', 'error')
        return redirect(url_for('student.dashboard'))

    offering = ClassOffering.query.filter_by(join_code=join_code, is_active=True).first()
    if not offering:
        flash(f'Class code "{join_code}" is invalid or inactive. Please confirm with your teacher.', 'error')
        return redirect(url_for('student.dashboard'))

    # Check if already enrolled
    existing = Enrollment.query.filter_by(
        student_id=g.student.id,
        class_offering_id=offering.id
    ).first()

    if existing:
        flash(f'You are already enrolled in {offering.course.name} ({offering.section.name}).', 'info')
        return redirect(url_for('classes.detail', class_id=offering.id))

    # Enroll
    enrollment = Enrollment(
        student_id=g.student.id,
        class_offering_id=offering.id
    )
    db.session.add(enrollment)
    db.session.commit()

    log_audit('CLASS_JOIN', 'ClassOffering', offering.id, f'Student {g.student.roll_number} joined with code {join_code}')
    flash(f'Successfully enrolled in {offering.course.name} ({offering.section.name})!', 'success')
    return redirect(url_for('classes.detail', class_id=offering.id))

@classes_bp.route('/create', methods=['POST'])
@teacher_required
def create():
    if not validate_csrf():
        return redirect(url_for('teacher.classes'))

    course_id = request.form.get('course_id')
    new_course_code = request.form.get('new_course_code', '').strip().upper()
    new_course_name = request.form.get('new_course_name', '').strip()
    
    section_id = request.form.get('section_id')
    new_section_name = request.form.get('new_section_name', '').strip().upper()
    programme = request.form.get('programme', '').strip()
    semester = request.form.get('semester', '').strip()
    academic_year = request.form.get('academic_year', '2026-2027').strip()

    try:
        # Determine course
        if course_id and course_id != 'new':
            course = db.session.get(Course, int(course_id))
        elif new_course_code and new_course_name:
            course = Course.query.filter_by(code=new_course_code).first()
            if not course:
                course = Course(code=new_course_code, name=new_course_name)
                db.session.add(course)
                db.session.flush()
        else:
            flash('Please select or specify a valid course.', 'error')
            return redirect(url_for('teacher.classes'))

        # Determine section
        semester_int = int(semester) if semester else 1
        if section_id and section_id != 'new':
            section = db.session.get(Section, int(section_id))
        elif new_section_name:
            section = Section.query.filter_by(name=new_section_name, semester=semester_int).first()
            if not section:
                section = Section(name=new_section_name, programme=programme or 'Engineering', semester=semester_int)
                db.session.add(section)
                db.session.flush()
        else:
            flash('Please select or specify a valid section.', 'error')
            return redirect(url_for('teacher.classes'))

        # Generate unique join code
        unique_code = generate_join_code()
        while ClassOffering.query.filter_by(join_code=unique_code).first():
            unique_code = generate_join_code()

        offering = ClassOffering(
            course_id=course.id,
            section_id=section.id,
            teacher_id=g.teacher.id,
            join_code=unique_code,
            semester=semester_int,
            academic_year=academic_year
        )
        db.session.add(offering)
        db.session.commit()

        log_audit('CLASS_CREATE', 'ClassOffering', offering.id, f'Faculty created class {offering.display_title} code {unique_code}')
        flash(f'Class "{offering.display_title}" created with join code: {unique_code}', 'success')
        return redirect(url_for('classes.detail', class_id=offering.id))

    except Exception as e:
        db.session.rollback()
        flash('An error occurred while creating the class offering.', 'error')
        return redirect(url_for('teacher.classes'))
