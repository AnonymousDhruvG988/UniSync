from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, utcnow

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'teacher'
    full_name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    # One-to-one relationships with profile tables
    student_profile = db.relationship('StudentProfile', back_populates='user', uselist=False, cascade='all, delete-orphan')
    teacher_profile = db.relationship('TeacherProfile', back_populates='user', uselist=False, cascade='all, delete-orphan')
    
    # Associated user logs and notifications
    notifications = db.relationship('Notification', back_populates='user', cascade='all, delete-orphan', order_by='Notification.created_at.desc()')
    audit_logs = db.relationship('AuditLog', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def is_teacher(self):
        return self.role == 'teacher'

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    roll_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    programme = db.Column(db.String(80), nullable=False)  # e.g., 'B.Tech CSE'
    semester = db.Column(db.Integer, nullable=False)     # e.g., 4
    section = db.Column(db.String(10), nullable=False)    # e.g., 'A'
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship('User', back_populates='student_profile')
    enrollments = db.relationship('Enrollment', back_populates='student', cascade='all, delete-orphan')
    feedback_responses = db.relationship('FeedbackResponse', back_populates='student', cascade='all, delete-orphan')
    doubts = db.relationship('Doubt', back_populates='student', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<StudentProfile {self.roll_number} - {self.programme}>'


class TeacherProfile(db.Model):
    __tablename__ = 'teacher_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    faculty_id = db.Column(db.String(30), unique=True, nullable=False, index=True)
    department = db.Column(db.String(80), nullable=False)  # e.g., 'Computer Science & Engineering'
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship('User', back_populates='teacher_profile')
    class_offerings = db.relationship('ClassOffering', back_populates='teacher', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<TeacherProfile {self.faculty_id} - {self.department}>'
