import os
from datetime import datetime
from flask import Flask, render_template, g, session, request
from config import Config
from extensions import db, utcnow
from auth_helpers import init_user_context, generate_csrf_token
from routes import register_blueprints
from models.doubts import Notification

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    register_blueprints(app)

    # Set up user context and CSRF
    @app.before_request
    def before_request_hook():
        init_user_context()

    # Context processors for templates
    @app.context_processor
    def inject_context():
        unread_count = 0
        if getattr(g, 'user', None):
            unread_count = Notification.query.filter_by(
                user_id=g.user.id,
                is_read=False
            ).count()

        return {
            'csrf_token': generate_csrf_token,
            'current_user': getattr(g, 'user', None),
            'current_student': getattr(g, 'student', None),
            'current_teacher': getattr(g, 'teacher', None),
            'unread_notifications_count': unread_count,
            'now': utcnow()
        }

    # Template filters
    @app.template_filter('format_datetime')
    def format_datetime(value, fmt='%d %b %Y, %H:%M'):
        if not value:
            return ''
        if hasattr(value, 'tzinfo') and value.tzinfo is not None:
            value = value.replace(tzinfo=None)
        return value.strftime(fmt)

    @app.template_filter('format_time')
    def format_time(value, fmt='%H:%M:%S'):
        if not value:
            return ''
        if hasattr(value, 'tzinfo') and value.tzinfo is not None:
            value = value.replace(tzinfo=None)
        return value.strftime(fmt)

    @app.template_filter('time_ago')
    def time_ago(value):
        if not value:
            return ''
        if hasattr(value, 'tzinfo') and value.tzinfo is not None:
            value = value.replace(tzinfo=None)
        diff = utcnow() - value
        seconds = int(diff.total_seconds())
        if seconds < 0:
            return 'Just now'
        elif seconds < 60:
            return 'Just now'
        elif seconds < 3600:
            m = seconds // 60
            return f"{m}m ago"
        elif seconds < 86400:
            h = seconds // 3600
            return f"{h}h ago"
        else:
            d = seconds // 86400
            return f"{d}d ago"

    # Error handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('error.html', code=403, title='Access Forbidden', message='You do not possess the required academic authorization to view this resource.'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html', code=404, title='Page Not Found', message='The requested academic resource or classroom could not be located.'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('error.html', code=500, title='System Error', message='An unexpected server error occurred. Academic data integrity remains secured.'), 500

    # Ensure database tables exist within app context
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # Auto-seed if database is empty
        from models.users import User
        if not User.query.first():
            print("Database empty. Initializing academic catalog and demo users...")
            from seed.seed_data import seed_database
            seed_database()
            print("Database seeded successfully.")

    print("\n" + "="*60)
    print("UniSync Server starting at http://127.0.0.1:5000")
    print("French Café Aesthetic University Classroom System")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
