import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import timedelta
from extensions import db, utcnow
from models.users import User, StudentProfile, TeacherProfile
from models.academic import Course, Section, ClassOffering, Enrollment
from models.feedback import FeedbackSession, FeedbackResponse
from models.doubts import Doubt, DoubtReply, DoubtStatusHistory, Notification

def seed_database(reset=True):
    """Seed comprehensive university academic records, faculty, students, classes, and interactions."""
    if reset:
        db.drop_all()
        db.create_all()

    # 1. Create Courses
    c_prog = Course(
        code='CS101',
        name='Programming Fundamentals',
        description='Core principles of algorithms, data structures, and procedural programming in Python and C.',
        credits=4
    )
    c_db = Course(
        code='CS201',
        name='Database Systems',
        description='Relational schema design, normalization, ACID transactions, and SQL query optimization.',
        credits=4
    )
    c_phy = Course(
        code='PH101',
        name='Applied Physics',
        description='Wave mechanics, electromagnetism, semiconductor physics, and quantum fundamentals.',
        credits=3
    )
    db.session.add_all([c_prog, c_db, c_phy])
    db.session.flush()

    # 2. Create Sections
    sec_a = Section(
        name='CSE-A',
        programme='B.Tech Computer Science & Engineering',
        semester=4
    )
    sec_b = Section(
        name='CSE-B',
        programme='B.Tech Computer Science & Engineering',
        semester=4
    )
    db.session.add_all([sec_a, sec_b])
    db.session.flush()

    # 3. Create Teachers
    # Teacher 1: Dr. Aarav Sharma
    u_t1 = User(
        email='dr.sharma@university.edu',
        role='teacher',
        full_name='Dr. Aarav Sharma'
    )
    u_t1.set_password('Faculty@123')
    db.session.add(u_t1)
    db.session.flush()

    p_t1 = TeacherProfile(
        user_id=u_t1.id,
        faculty_id='FAC-CSE-01',
        department='Computer Science & Engineering'
    )
    db.session.add(p_t1)

    # Teacher 2: Prof. Ananya Kapoor
    u_t2 = User(
        email='prof.kapoor@university.edu',
        role='teacher',
        full_name='Prof. Ananya Kapoor'
    )
    u_t2.set_password('Faculty@123')
    db.session.add(u_t2)
    db.session.flush()

    p_t2 = TeacherProfile(
        user_id=u_t2.id,
        faculty_id='FAC-PHY-02',
        department='Applied Sciences & Physics'
    )
    db.session.add(p_t2)
    db.session.flush()

    # 4. Create Students
    students_info = [
        ('aarav.s@student.university.edu', 'Aarav Sharma', '24CSE001', 'B.Tech CSE', 4, 'A'),
        ('riya.v@student.university.edu', 'Riya Verma', '24CSE002', 'B.Tech CSE', 4, 'A'),
        ('kabir.m@student.university.edu', 'Kabir Mehta', '24CSE003', 'B.Tech CSE', 4, 'A'),
        ('diya.p@student.university.edu', 'Diya Patel', '24CSE004', 'B.Tech CSE', 4, 'B'),
    ]

    student_profiles_map = {}
    for email, name, roll, prog, sem, sec in students_info:
        user = User(
            email=email,
            role='student',
            full_name=name
        )
        user.set_password('Student@123')
        db.session.add(user)
        db.session.flush()

        profile = StudentProfile(
            user_id=user.id,
            roll_number=roll,
            programme=prog,
            semester=sem,
            section=sec
        )
        db.session.add(profile)
        db.session.flush()
        student_profiles_map[roll] = profile

    # 5. Create Class Offerings
    # Teacher 1 classes
    cls_prog_a = ClassOffering(
        course_id=c_prog.id,
        section_id=sec_a.id,
        teacher_id=p_t1.id,
        join_code='PROG-A',
        semester=4,
        academic_year='2026-2027'
    )
    cls_prog_b = ClassOffering(
        course_id=c_prog.id,
        section_id=sec_b.id,
        teacher_id=p_t1.id,
        join_code='PROG-B',
        semester=4,
        academic_year='2026-2027'
    )
    cls_db_a = ClassOffering(
        course_id=c_db.id,
        section_id=sec_a.id,
        teacher_id=p_t1.id,
        join_code='DATA-A',
        semester=4,
        academic_year='2026-2027'
    )

    # Teacher 2 classes
    cls_phy_a = ClassOffering(
        course_id=c_phy.id,
        section_id=sec_a.id,
        teacher_id=p_t2.id,
        join_code='PHYS-A',
        semester=4,
        academic_year='2026-2027'
    )
    cls_phy_b = ClassOffering(
        course_id=c_phy.id,
        section_id=sec_b.id,
        teacher_id=p_t2.id,
        join_code='PHYS-B',
        semester=4,
        academic_year='2026-2027'
    )

    db.session.add_all([cls_prog_a, cls_prog_b, cls_db_a, cls_phy_a, cls_phy_b])
    db.session.flush()

    # 6. Enroll Students
    # Section A students (Aarav, Riya, Kabir) enrolled in PROG-A, DATA-A, PHYS-A
    sec_a_students = [student_profiles_map['24CSE001'], student_profiles_map['24CSE002'], student_profiles_map['24CSE003']]
    sec_a_classes = [cls_prog_a, cls_db_a, cls_phy_a]

    for st in sec_a_students:
        for cl in sec_a_classes:
            enr = Enrollment(student_id=st.id, class_offering_id=cl.id)
            db.session.add(enr)

    # Section B student (Diya) enrolled in PROG-B, PHYS-B
    diya = student_profiles_map['24CSE004']
    for cl in [cls_prog_b, cls_phy_b]:
        enr = Enrollment(student_id=diya.id, class_offering_id=cl.id)
        db.session.add(enr)

    db.session.flush()

    # 7. Create Historical Weekly Feedback Sessions for Long-Term Analytics
    now = utcnow()

    # Week 1 Session (21 days ago)
    w1_session = FeedbackSession(
        class_offering_id=cls_prog_a.id,
        session_token='demo-session-w1-intro',
        started_at=now - timedelta(days=21),
        expires_at=now - timedelta(days=21) + timedelta(seconds=45),
        status='closed'
    )
    db.session.add(w1_session)
    db.session.flush()
    db.session.add_all([
        FeedbackResponse(session_id=w1_session.id, student_id=student_profiles_map['24CSE001'].id, understanding='understood', satisfaction=4, concept_feedback='Good introduction to pointer concepts in memory.', submitted_at=w1_session.started_at + timedelta(seconds=12)),
        FeedbackResponse(session_id=w1_session.id, student_id=student_profiles_map['24CSE002'].id, understanding='understood', satisfaction=5, concept_feedback='Crystal clear pacing.', submitted_at=w1_session.started_at + timedelta(seconds=21)),
        FeedbackResponse(session_id=w1_session.id, student_id=student_profiles_map['24CSE003'].id, understanding='partially', satisfaction=4, concept_feedback='Would like extra practice problems on nested loops.', submitted_at=w1_session.started_at + timedelta(seconds=33))
    ])

    # Week 2 Session (14 days ago)
    w2_session = FeedbackSession(
        class_offering_id=cls_prog_a.id,
        session_token='demo-session-w2-oop',
        started_at=now - timedelta(days=14),
        expires_at=now - timedelta(days=14) + timedelta(seconds=45),
        status='closed'
    )
    db.session.add(w2_session)
    db.session.flush()
    db.session.add_all([
        FeedbackResponse(session_id=w2_session.id, student_id=student_profiles_map['24CSE001'].id, understanding='understood', satisfaction=5, concept_feedback='Polymorphism demo was phenomenal.', submitted_at=w2_session.started_at + timedelta(seconds=15)),
        FeedbackResponse(session_id=w2_session.id, student_id=student_profiles_map['24CSE002'].id, understanding='understood', satisfaction=5, concept_feedback='Loved the live coding demonstration.', submitted_at=w2_session.started_at + timedelta(seconds=24)),
        FeedbackResponse(session_id=w2_session.id, student_id=student_profiles_map['24CSE003'].id, understanding='understood', satisfaction=4, concept_feedback='Abstract classes made sense.', submitted_at=w2_session.started_at + timedelta(seconds=39))
    ])

    # Week 3 Session (7 days ago)
    w3_session = FeedbackSession(
        class_offering_id=cls_prog_a.id,
        session_token='demo-session-w3-algo',
        started_at=now - timedelta(days=7),
        expires_at=now - timedelta(days=7) + timedelta(seconds=45),
        status='closed'
    )
    db.session.add(w3_session)
    db.session.flush()
    db.session.add_all([
        FeedbackResponse(session_id=w3_session.id, student_id=student_profiles_map['24CSE001'].id, understanding='understood', satisfaction=4, concept_feedback='Big-O upper bounds notation.', submitted_at=w3_session.started_at + timedelta(seconds=18)),
        FeedbackResponse(session_id=w3_session.id, student_id=student_profiles_map['24CSE002'].id, understanding='partially', satisfaction=4, concept_feedback='Amortized analysis needs another review.', submitted_at=w3_session.started_at + timedelta(seconds=28)),
        FeedbackResponse(session_id=w3_session.id, student_id=student_profiles_map['24CSE003'].id, understanding='needs_help', satisfaction=3, concept_feedback='Struggling with Master Theorem cases.', submitted_at=w3_session.started_at + timedelta(seconds=41))
    ])

    # Week 4 / Current Week Session (Today, 2 hours ago)
    past_session = FeedbackSession(
        class_offering_id=cls_prog_a.id,
        session_token='demo-session-prog-fundamentals-cse-a',
        started_at=now - timedelta(hours=2),
        expires_at=now - timedelta(hours=2) + timedelta(seconds=45),
        status='closed'
    )
    db.session.add(past_session)
    db.session.flush()

    # Responses from students in Section A
    resp1 = FeedbackResponse(
        session_id=past_session.id,
        student_id=student_profiles_map['24CSE001'].id,
        understanding='understood',
        satisfaction=5,
        concept_feedback='The recursive tree breakdown on recursion depth made it crystal clear.',
        submitted_at=past_session.started_at + timedelta(seconds=14)
    )
    resp2 = FeedbackResponse(
        session_id=past_session.id,
        student_id=student_profiles_map['24CSE002'].id,
        understanding='partially',
        satisfaction=4,
        concept_feedback='Could we review tail-call elimination and stack frames once more?',
        submitted_at=past_session.started_at + timedelta(seconds=27)
    )
    resp3 = FeedbackResponse(
        session_id=past_session.id,
        student_id=student_profiles_map['24CSE003'].id,
        understanding='needs_help',
        satisfaction=3,
        concept_feedback='Need more examples on base cases in divide-and-conquer algorithms.',
        submitted_at=past_session.started_at + timedelta(seconds=38)
    )
    db.session.add_all([resp1, resp2, resp3])

    # 8. Sample Doubts / Questions
    doubt1 = Doubt(
        class_offering_id=cls_prog_a.id,
        student_id=student_profiles_map['24CSE001'].id,
        feedback_session_id=past_session.id,
        title='Time complexity comparison between memoization and tabulation',
        explanation="In today's class, we discussed memoized Fibonacci versus bottom-up DP. While both achieve O(N) time complexity, does bottom-up tabulation always guarantee better cache spatial locality in Python?",
        status='answered',
        created_at=now - timedelta(hours=1, minutes=45)
    )
    db.session.add(doubt1)
    db.session.flush()

    reply1 = DoubtReply(
        doubt_id=doubt1.id,
        author_id=u_t1.id,
        message='Excellent observation, Aarav. In Python, while both are asymptotically O(N), iterative tabulation avoids call-stack frame allocation overhead and yields superior memory locality for continuous array traversals.',
        created_at=now - timedelta(hours=1, minutes=10)
    )
    db.session.add(reply1)

    notif1 = Notification(
        user_id=student_profiles_map['24CSE001'].user_id,
        title='Teacher Answered Your Question',
        message=f'Dr. Aarav Sharma answered your question on "Time complexity comparison between memoization and tabulation".',
        link=f'/questions/{doubt1.id}',
        is_read=True
    )
    db.session.add(notif1)

    # Second doubt from Kabir (pending / new)
    doubt2 = Doubt(
        class_offering_id=cls_prog_a.id,
        student_id=student_profiles_map['24CSE003'].id,
        feedback_session_id=past_session.id,
        title='Identifying base condition in recursive permutations',
        explanation='When generating permutations of an array with duplicates, how do we prevent redundant subtrees before reaching the recursion base condition?',
        status='new',
        created_at=now - timedelta(minutes=30)
    )
    db.session.add(doubt2)

    db.session.commit()
    print("Database seeding completed successfully.")

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        seed_database()
