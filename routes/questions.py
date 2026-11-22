from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g, jsonify, abort
from extensions import db
from models.academic import ClassOffering, Enrollment
from models.doubts import Doubt, DoubtReply, DoubtStatusHistory, Notification
from models.feedback import FeedbackSession
from auth_helpers import login_required, student_required, teacher_required, validate_csrf, log_audit, create_notification

questions_bp = Blueprint('questions', __name__, url_prefix='/questions')

@questions_bp.route('/create', methods=['POST'])
@student_required
def create():
    if not validate_csrf():
        return redirect(url_for('student.questions'))

    class_id = request.form.get('class_offering_id')
    title = request.form.get('title', '').strip()
    explanation = request.form.get('explanation', '').strip()
    session_id = request.form.get('feedback_session_id')

    if not class_id or not title or not explanation:
        flash('Please provide both a title and a detailed explanation for your question.', 'error')
        return redirect(url_for('student.questions'))

    offering = db.session.get(ClassOffering, int(class_id))
    if not offering:
        abort(404)
    student = g.student

    # Verify enrollment
    enrollment = Enrollment.query.filter_by(
        student_id=student.id,
        class_offering_id=offering.id
    ).first()
    if not enrollment:
        flash('You can only ask questions in classes you are enrolled in.', 'error')
        return redirect(url_for('student.dashboard'))

    # Optional feedback session verification
    valid_session_id = None
    if session_id:
        try:
            sess = FeedbackSession.query.filter_by(id=int(session_id), class_offering_id=offering.id).first()
            if sess:
                valid_session_id = sess.id
        except ValueError:
            pass

    doubt = Doubt(
        class_offering_id=offering.id,
        student_id=student.id,
        feedback_session_id=valid_session_id,
        title=title,
        explanation=explanation,
        status='new'
    )
    db.session.add(doubt)
    db.session.flush()

    # Record initial history
    history = DoubtStatusHistory(
        doubt_id=doubt.id,
        changed_by_id=g.user.id,
        old_status=None,
        new_status='new',
        note='Question submitted by student'
    )
    db.session.add(history)
    db.session.commit()

    log_audit('QUESTION_CREATE', 'Doubt', doubt.id, f'Student {student.roll_number} asked: {title[:40]}')
    flash('Your question has been submitted to your instructor.', 'success')
    return redirect(url_for('questions.detail', doubt_id=doubt.id))

@questions_bp.route('/<int:doubt_id>')
@login_required
def detail(doubt_id):
    doubt = db.session.get(Doubt, doubt_id)
    if not doubt:
        abort(404)
    offering = doubt.class_offering
    user = g.user

    is_teacher_owner = user.is_teacher and offering.teacher_id == getattr(g.teacher, 'id', None)
    is_author_student = user.is_student and doubt.student_id == getattr(g.student, 'id', None)

    # Strict privacy check
    if not is_teacher_owner and not is_author_student:
        flash('Access restricted. You cannot view private questions of other students.', 'error')
        return redirect(url_for('auth.index'))

    # If teacher views a 'new' question, update status to 'viewed'
    if is_teacher_owner and doubt.status == 'new':
        doubt.status = 'viewed'
        history = DoubtStatusHistory(
            doubt_id=doubt.id,
            changed_by_id=user.id,
            old_status='new',
            new_status='viewed',
            note='Instructor opened question'
        )
        db.session.add(history)
        db.session.commit()

    return render_template(
        'question_detail.html',
        doubt=doubt,
        offering=offering,
        is_teacher=is_teacher_owner,
        is_student=is_author_student
    )

@questions_bp.route('/<int:doubt_id>/reply', methods=['POST'])
@login_required
def reply(doubt_id):
    if not validate_csrf():
        return redirect(url_for('questions.detail', doubt_id=doubt_id))

    doubt = db.session.get(Doubt, doubt_id)
    if not doubt:
        abort(404)
    offering = doubt.class_offering
    user = g.user

    is_teacher_owner = user.is_teacher and offering.teacher_id == getattr(g.teacher, 'id', None)
    is_author_student = user.is_student and doubt.student_id == getattr(g.student, 'id', None)

    if not is_teacher_owner and not is_author_student:
        abort(403)

    message = request.form.get('message', '').strip()
    if not message:
        flash('Reply message cannot be empty.', 'error')
        return redirect(url_for('questions.detail', doubt_id=doubt_id))

    new_reply = DoubtReply(
        doubt_id=doubt.id,
        author_id=user.id,
        message=message
    )
    db.session.add(new_reply)

    # Status transition logic
    old_status = doubt.status
    if is_teacher_owner:
        doubt.status = 'answered'
        # Notify the student
        create_notification(
            user_id=doubt.student.user_id,
            title='Teacher Answered Your Question',
            message=f"{offering.teacher.user.full_name} answered your question: \"{doubt.title[:40]}\"",
            link=url_for('questions.detail', doubt_id=doubt.id)
        )
        log_audit('QUESTION_ANSWER', 'Doubt', doubt.id, f'Teacher replied to doubt {doubt.id}')
    else:
        # If student replies to already answered question, mark as active discussion
        if doubt.status == 'resolved':
            doubt.status = 'answered'

    if doubt.status != old_status:
        history = DoubtStatusHistory(
            doubt_id=doubt.id,
            changed_by_id=user.id,
            old_status=old_status,
            new_status=doubt.status,
            note=f"Status updated following reply by {user.role}"
        )
        db.session.add(history)

    db.session.commit()
    flash('Your reply has been posted.', 'success')
    return redirect(url_for('questions.detail', doubt_id=doubt_id))

@questions_bp.route('/<int:doubt_id>/status', methods=['POST'])
@login_required
def update_status(doubt_id):
    if not validate_csrf():
        return redirect(url_for('questions.detail', doubt_id=doubt_id))

    doubt = db.session.get(Doubt, doubt_id)
    if not doubt:
        abort(404)
    offering = doubt.class_offering
    user = g.user

    is_teacher_owner = user.is_teacher and offering.teacher_id == getattr(g.teacher, 'id', None)
    is_author_student = user.is_student and doubt.student_id == getattr(g.student, 'id', None)

    if not is_teacher_owner and not is_author_student:
        abort(403)

    new_status = request.form.get('status', '').strip()
    note = request.form.get('note', '').strip()

    valid_statuses = ['new', 'viewed', 'answered', 'resolved']
    if new_status not in valid_statuses:
        flash('Invalid question status.', 'error')
        return redirect(url_for('questions.detail', doubt_id=doubt_id))

    # Students can only mark their own questions as resolved or reopen them
    if is_author_student and not is_teacher_owner:
        if new_status not in ['resolved', 'answered']:
            flash('Students can only mark questions as resolved or reopen them.', 'error')
            return redirect(url_for('questions.detail', doubt_id=doubt_id))

    old_status = doubt.status
    if old_status != new_status:
        doubt.status = new_status
        history = DoubtStatusHistory(
            doubt_id=doubt.id,
            changed_by_id=user.id,
            old_status=old_status,
            new_status=new_status,
            note=note or f"Status changed to {new_status} by {user.full_name}"
        )
        db.session.add(history)

        # Notify student if teacher marked resolved
        if is_teacher_owner and new_status == 'resolved':
            create_notification(
                user_id=doubt.student.user_id,
                title='Question Marked as Resolved',
                message=f"Your question \"{doubt.title[:40]}\" was marked resolved by {user.full_name}.",
                link=url_for('questions.detail', doubt_id=doubt.id)
            )

        db.session.commit()
        flash(f'Question status updated to {new_status.title()}.', 'success')

    return redirect(url_for('questions.detail', doubt_id=doubt_id))
