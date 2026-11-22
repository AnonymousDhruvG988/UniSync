from routes.auth import auth_bp
from routes.student import student_bp
from routes.teacher import teacher_bp
from routes.classes import classes_bp
from routes.feedback import feedback_bp
from routes.questions import questions_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(classes_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(questions_bp)
