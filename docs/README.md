# UniSync &mdash; Academic Classroom Platform

> **Tagline:** A better way to learn. A better way to connect.  
> **Official Visual Identity:** French Café Aesthetic &bull; Apple iOS 26 Refined Visual Language  
> **Project Scope:** Digital Artefact for BU100 SDG 4 Action Lab  

---

## 1. Executive Summary

**UniSync** is a single integrated university web application designed to connect university students and faculty members. It addresses the critical disconnect between classroom lecture delivery and real-time student comprehension. UniSync provides two tightly integrated core capabilities:
1. **Dynamic 45-Second QR Classroom Feedback:** Teachers initiate an in-class understanding pulse at the end of a lecture topic. An automated server-side 45-second timer displays a dynamically generated QR code. When the countdown finishes, the session terminates immediately, and the teacher’s screen automatically displays an identified student comprehension table and analytics.
2. **Integrated Doubt & Question Workspace:** Students ask focused academic doubts tied directly to their course section and lecture sessions. Teachers review, prioritize, reply authoritatively, and track status (`new`, `viewed`, `answered`, `resolved`), with real-time in-app notifications for students.

Strict role isolation ensures that **only two user roles** exist:
- **Student**
- **Teacher / Faculty**

No administrator dashboards, campus staff logins, maintenance modules, timetables, or attendance tools clutter the workspace.

---

## 2. Technology Stack & Architecture

- **Backend:** Python 3.10+ &bull; Flask &bull; SQLAlchemy ORM &bull; SQLite initially
- **Security:** Werkzeug password hashing &bull; Session-based CSRF protection &bull; Server-enforced authorization decorators &bull; Faculty verification passkey
- **Dynamic Assets:** `qrcode` &amp; `Pillow` for dynamic SVG/PNG QR image generation
- **Frontend:** Vanilla HTML5, CSS3, and ES6+ JavaScript. **Zero frontend frameworks** (No React, Vue, Angular, Bootstrap, or Tailwind).
- **Design System:** French Café aesthetic (`#F4EEE5` Warm Cream, `#514139` Deep Espresso, `#8B5544` Terracotta, `#C7A68B` Latte Beige). Zero emojis. Refined inline SVG icons.
- **Testing:** `pytest` automated test suite covering authentication, class mapping, 45-second timer expiry, feedback collection, and question management.

---

## 3. Demonstration & Pre-Seeded Accounts

UniSync includes a complete set of pre-seeded demonstration accounts and course offerings:

### Faculty Accounts (Password: `Faculty@123`)
| Faculty Name | Email | Faculty ID | Department | Assigned Classes |
| :--- | :--- | :--- | :--- | :--- |
| **Dr. Aarav Sharma** | `dr.sharma@university.edu` | `FAC-CSE-01` | Computer Science & Eng. | CS101 (CSE-A), CS101 (CSE-B), CS201 (CSE-A) |
| **Prof. Ananya Kapoor** | `prof.kapoor@university.edu` | `FAC-PHY-02` | Applied Sciences & Physics | PH101 (CSE-A), PH101 (CSE-B) |

*Faculty Registration Verification Passkey:* `FACULTY2026`

### Student Accounts (Password: `Student@123`)
| Student Name | Email | Roll Number | Programme | Section | Enrolled Classes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Aarav Sharma** | `aarav.s@student.university.edu` | `24CSE001` | B.Tech CSE | A | CS101 (CSE-A), CS201 (CSE-A), PH101 (CSE-A) |
| **Riya Verma** | `riya.v@student.university.edu` | `24CSE002` | B.Tech CSE | A | CS101 (CSE-A), CS201 (CSE-A), PH101 (CSE-A) |
| **Kabir Mehta** | `kabir.m@student.university.edu` | `24CSE003` | B.Tech CSE | A | CS101 (CSE-A), CS201 (CSE-A), PH101 (CSE-A) |
| **Diya Patel** | `diya.p@student.university.edu` | `24CSE004` | B.Tech CSE | B | CS101 (CSE-B), PH101 (CSE-B) |

---

## 4. Installation & Local Setup

### Step 1: Clone or Navigate to Directory
```bash
cd c:\Users\dhruv\Desktop\UNIDOUBT
```

### Step 2: Set Up Virtual Environment (Recommended)
```bash
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Seed Database
```bash
python seed/seed_data.py
```
This initializes `instance/database.db` with courses, sections, faculty, students, class enrollments, and demo questions.

### Step 5: Run the UniSync Application
```bash
python app.py
```
The server will start on: **`http://127.0.0.1:5000`**

---

## 5. Mobile & Local Network QR Testing Setup

To test scanning the QR code with a physical mobile phone on the same Wi-Fi network:

1. Determine your computer's local IPv4 address (e.g. `192.168.1.45`) using `ipconfig` (Windows) or `ifconfig` (macOS/Linux).
2. Set the environment variable `SERVER_NAME` or access the website in your browser via `http://192.168.1.45:5000`.
3. When the teacher launches a 45-second feedback session, the QR code encodes `http://192.168.1.45:5000/feedback/scan/<token>`.
4. Point your mobile phone camera at the screen to open the feedback check-in immediately.
5. *Desktop Evaluator Shortcut:* The teacher screen also includes a **Direct Evaluation Link** (`Open Student Form in New Tab`) allowing full testing in an incognito or secondary browser window without needing a phone.

---

## 6. Automated Testing Instructions

Execute the complete test suite using `pytest`:
```bash
pytest -v
```

Test coverage includes:
- `tests/test_auth.py`: Student & teacher signup, password strength, duplicate roll number/email prevention, faculty verification key enforcement, login/logout.
- `tests/test_classes.py`: Multiple course-section mapping, cross-section data isolation, student class code enrollment.
- `tests/test_feedback.py`: Dynamic session creation, QR image generation, student submission, duplicate rejection, CSV export.
- `tests/test_qr_expiry.py`: Strict 45-second server-side cutoff, late submission rejection, auto-closure.
- `tests/test_questions.py`: Question creation, instructor replies, notification dispatch, status history, student privacy protection.

---

## 7. Project Documentation

Comprehensive architectural and project documentation is provided in the `docs/` directory:
- [ARCHITECTURE.md](file:///c:/Users/dhruv/Desktop/UNIDOUBT/docs/ARCHITECTURE.md): System architecture, security model, and real-time polling mechanics.
- [DATABASE.md](file:///c:/Users/dhruv/Desktop/UNIDOUBT/docs/DATABASE.md): Detailed schema specifications, data dictionary, and Entity-Relationship diagram.
- [USER_GUIDE.md](file:///c:/Users/dhruv/Desktop/UNIDOUBT/docs/USER_GUIDE.md): Operational manual for students and faculty.
- [TREP_DOCUMENTATION.md](file:///c:/Users/dhruv/Desktop/UNIDOUBT/docs/TREP_DOCUMENTATION.md): BU100 SDG 4 Action Lab dossier, problem hypothesis, survey templates, interview templates, pilot evaluation, and presentation script.
