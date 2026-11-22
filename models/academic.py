import secrets
import string
from extensions import db, utcnow

def generate_join_code(length=6):
    """Generate a clean, uppercase alphanumeric code without easily confused characters."""
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(secrets.choice(chars) for _ in range(length))

class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)  # e.g., 'CS101'
    name = db.Column(db.String(120), nullable=False)                         # e.g., 'Programming Fundamentals'
    description = db.Column(db.Text, nullable=True)
    credits = db.Column(db.Integer, default=3, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    class_offerings = db.relationship('ClassOffering', back_populates='course', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Course {self.code}: {self.name}>'


class Section(db.Model):
    __tablename__ = 'sections'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)         # e.g., 'CSE-A', 'CSE-B'
    programme = db.Column(db.String(80), nullable=False)    # e.g., 'B.Tech CSE'
    semester = db.Column(db.Integer, nullable=False)       # e.g., 4
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    class_offerings = db.relationship('ClassOffering', back_populates='section', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Section {self.name} ({self.programme} Sem {self.semester})>'


class ClassOffering(db.Model):
    __tablename__ = 'class_offerings'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher_profiles.id'), nullable=False)
    join_code = db.Column(db.String(16), unique=True, nullable=False, index=True, default=generate_join_code)
    semester = db.Column(db.Integer, nullable=False)
    academic_year = db.Column(db.String(20), default='2026-2027', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    # Relationships
    course = db.relationship('Course', back_populates='class_offerings')
    section = db.relationship('Section', back_populates='class_offerings')
    teacher = db.relationship('TeacherProfile', back_populates='class_offerings')
    enrollments = db.relationship('Enrollment', back_populates='class_offering', cascade='all, delete-orphan')
    feedback_sessions = db.relationship('FeedbackSession', back_populates='class_offering', cascade='all, delete-orphan', order_by='FeedbackSession.created_at.desc()')
    doubts = db.relationship('Doubt', back_populates='class_offering', cascade='all, delete-orphan', order_by='Doubt.created_at.desc()')

    @property
    def display_title(self):
        return f"{self.course.name} ({self.section.name})"

    @property
    def student_count(self):
        return len(self.enrollments)

    def __repr__(self):
        return f'<ClassOffering {self.course.code if self.course else self.course_id} - {self.section.name if self.section else self.section_id}>'


class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id', ondelete='CASCADE'), nullable=False)
    class_offering_id = db.Column(db.Integer, db.ForeignKey('class_offerings.id', ondelete='CASCADE'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'class_offering_id', name='uq_student_class_offering'),
    )

    student = db.relationship('StudentProfile', back_populates='enrollments')
    class_offering = db.relationship('ClassOffering', back_populates='enrollments')

    def __repr__(self):
        return f'<Enrollment Student:{self.student_id} Class:{self.class_offering_id}>'
