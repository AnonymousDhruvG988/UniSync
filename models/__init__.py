from extensions import db
from models.users import User, StudentProfile, TeacherProfile
from models.academic import Course, Section, ClassOffering, Enrollment, generate_join_code
from models.feedback import FeedbackSession, FeedbackResponse
from models.doubts import Doubt, DoubtReply, DoubtStatusHistory, Notification, AuditLog

__all__ = [
    'db',
    'User',
    'StudentProfile',
    'TeacherProfile',
    'Course',
    'Section',
    'ClassOffering',
    'Enrollment',
    'generate_join_code',
    'FeedbackSession',
    'FeedbackResponse',
    'Doubt',
    'DoubtReply',
    'DoubtStatusHistory',
    'Notification',
    'AuditLog',
]
