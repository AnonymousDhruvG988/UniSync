import uuid
from datetime import timedelta
from extensions import db, utcnow

class FeedbackSession(db.Model):
    __tablename__ = 'feedback_sessions'

    id = db.Column(db.Integer, primary_key=True)
    class_offering_id = db.Column(db.Integer, db.ForeignKey('class_offerings.id', ondelete='CASCADE'), nullable=False)
    session_token = db.Column(db.String(64), unique=True, nullable=False, index=True, default=lambda: uuid.uuid4().hex)
    started_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active' or 'closed'
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    # Relationships
    class_offering = db.relationship('ClassOffering', back_populates='feedback_sessions')
    responses = db.relationship('FeedbackResponse', back_populates='session', cascade='all, delete-orphan', order_by='FeedbackResponse.submitted_at.asc()')
    linked_doubts = db.relationship('Doubt', back_populates='session')

    @property
    def is_active_now(self):
        if self.status != 'active':
            return False
        return utcnow() <= self.expires_at

    @property
    def remaining_seconds(self):
        if self.status != 'active':
            return 0
        rem = (self.expires_at - utcnow()).total_seconds()
        return max(0, int(rem))

    def close_if_expired(self):
        if self.status == 'active' and utcnow() > self.expires_at:
            self.status = 'closed'
            return True
        return False

    @property
    def response_count(self):
        return len(self.responses)

    @property
    def average_satisfaction(self):
        if not self.responses:
            return 0.0
        total = sum(r.satisfaction for r in self.responses)
        return round(total / len(self.responses), 1)

    @property
    def understanding_breakdown(self):
        counts = {'understood': 0, 'partially': 0, 'needs_help': 0}
        for r in self.responses:
            if r.understanding in counts:
                counts[r.understanding] += 1
        total = len(self.responses)
        percentages = {
            k: round((v / total * 100), 1) if total > 0 else 0
            for k, v in counts.items()
        }
        return {'counts': counts, 'percentages': percentages, 'total': total}

    def __repr__(self):
        return f'<FeedbackSession {self.session_token[:8]} (Class:{self.class_offering_id}, Status:{self.status})>'


class FeedbackResponse(db.Model):
    __tablename__ = 'feedback_responses'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('feedback_sessions.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id', ondelete='CASCADE'), nullable=False)
    understanding = db.Column(db.String(30), nullable=False)  # 'understood', 'partially', 'needs_help'
    satisfaction = db.Column(db.Integer, nullable=False)     # 1 to 5
    concept_feedback = db.Column(db.Text, nullable=True)     # Concept to explain again
    submitted_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('session_id', 'student_id', name='uq_feedback_session_student'),
    )

    session = db.relationship('FeedbackSession', back_populates='responses')
    student = db.relationship('StudentProfile', back_populates='feedback_responses')

    @property
    def student_name(self):
        return self.student.user.full_name if self.student and self.student.user else "Unknown Student"

    @property
    def student_roll_number(self):
        return self.student.roll_number if self.student else "N/A"

    def __repr__(self):
        return f'<FeedbackResponse Session:{self.session_id} Student:{self.student_roll_number}>'
