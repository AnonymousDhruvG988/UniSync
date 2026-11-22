from extensions import db, utcnow

class Doubt(db.Model):
    __tablename__ = 'doubts'

    id = db.Column(db.Integer, primary_key=True)
    class_offering_id = db.Column(db.Integer, db.ForeignKey('class_offerings.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id', ondelete='CASCADE'), nullable=False)
    feedback_session_id = db.Column(db.Integer, db.ForeignKey('feedback_sessions.id', ondelete='SET NULL'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='new', nullable=False)  # 'new', 'viewed', 'answered', 'resolved'
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    class_offering = db.relationship('ClassOffering', back_populates='doubts')
    student = db.relationship('StudentProfile', back_populates='doubts')
    session = db.relationship('FeedbackSession', back_populates='linked_doubts')
    replies = db.relationship('DoubtReply', back_populates='doubt', cascade='all, delete-orphan', order_by='DoubtReply.created_at.asc()')
    status_history = db.relationship('DoubtStatusHistory', back_populates='doubt', cascade='all, delete-orphan', order_by='DoubtStatusHistory.changed_at.desc()')

    @property
    def latest_reply(self):
        return self.replies[-1] if self.replies else None

    @property
    def reply_count(self):
        return len(self.replies)

    def __repr__(self):
        return f'<Doubt {self.id}: {self.title[:30]} ({self.status})>'


class DoubtReply(db.Model):
    __tablename__ = 'doubt_replies'

    id = db.Column(db.Integer, primary_key=True)
    doubt_id = db.Column(db.Integer, db.ForeignKey('doubts.id', ondelete='CASCADE'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    doubt = db.relationship('Doubt', back_populates='replies')
    author = db.relationship('User')

    def __repr__(self):
        return f'<DoubtReply {self.id} for Doubt {self.doubt_id}>'


class DoubtStatusHistory(db.Model):
    __tablename__ = 'doubt_status_history'

    id = db.Column(db.Integer, primary_key=True)
    doubt_id = db.Column(db.Integer, db.ForeignKey('doubts.id', ondelete='CASCADE'), nullable=False)
    changed_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    old_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=False)
    note = db.Column(db.String(255), nullable=True)
    changed_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    doubt = db.relationship('Doubt', back_populates='status_history')
    changed_by = db.relationship('User')

    def __repr__(self):
        return f'<DoubtStatusHistory Doubt:{self.doubt_id} {self.old_status}->{self.new_status}>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship('User', back_populates='notifications')

    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id} (Read: {self.is_read})>'


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(80), nullable=False)  # e.g., 'FEEDBACK_SUBMISSION', 'QR_SESSION_START'
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship('User', back_populates='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.action} on {self.entity_type}:{self.entity_id}>'
