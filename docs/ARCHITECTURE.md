# UniSync &mdash; System Architecture & Technical Specifications

> **System Name:** UniSync Academic Platform  
> **Architecture Paradigm:** Monolithic Python Flask with Decoupled Vanilla Frontend  
> **Security Grade:** Role-Based Access Control (RBAC) with Server-Authoritative Timing  

---

## 1. High-Level Architecture

UniSync is structured around a resilient, self-contained architecture with zero external runtime dependencies on Node.js or frontend compiler toolchains. All routing, business logic, session security, and data validation are centralized in Python Flask, while the user interface operates through standards-compliant HTML5, custom CSS3, and ES6+ Vanilla JavaScript.

```
+-------------------------------------------------------------------------------+
|                             CLIENT APPLICATION                                |
|  +-------------------------------------------------------------------------+  |
|  |  French Café UI Engine (Apple iOS 26 Refined Surface Aesthetics)        |  |
|  |  - Vanilla ES6+ State & Modals (main.js)                                |  |
|  |  - 45s Synchronized Real-Time Countdown & Poller (qr_timer.js)            |  |
|  |  - Dynamic Identified Table Filter & Search Engine (questions.js)       |  |
|  |  - Interactive Touch-Friendly Rating & Understanding (feedback.js)      |  |
|  +-------------------------------------------------------------------------+  |
+---------------------------------------|---------------------------------------+
                                        | HTTPS / REST / Session Cookies
+---------------------------------------v---------------------------------------+
|                              PYTHON FLASK BACKEND                             |
|  +-------------------+  +-------------------+  +---------------------------+  |
|  |   Auth & Security |  |  Class Workspace  |  |   45s QR Feedback Engine  |  |
|  |   - RBAC Guards   |  |   - Multi-Section |  |   - Dynamic Session Token |  |
|  |   - CSRF Verifier |  |   - Join Codes    |  |   - Server Expiry Check   |  |
|  |   - Audit Logger  |  |   - Isolation     |  |   - QR Image Synthesis    |  |
|  +-------------------+  +-------------------+  +---------------------------+  |
|  +-------------------------------------------------------------------------+  |
|  |                    Question & Doubt Management Engine                   |  |
|  |                    - Status FSM (New -> Viewed -> Answered -> Resolved)  |  |
|  |                    - In-App Notification Dispatcher                     |  |
|  +-------------------------------------------------------------------------+  |
+---------------------------------------|---------------------------------------+
                                        | SQLAlchemy ORM
+---------------------------------------v---------------------------------------+
|                            RELATIONAL DATABASE                                |
|  - Users, Profiles, Courses, Sections, Class Offerings, Enrollments           |
|  - Feedback Sessions, Feedback Responses (Identified, Roll-Mapped)            |
|  - Doubts, Doubt Replies, Status History, Notifications, Audit Logs           |
+-------------------------------------------------------------------------------+
```

---

## 2. Security Architecture & Threat Modeling

### 2.1 Role-Based Access Control (RBAC)
UniSync strictly enforces two academic roles:
- `student`
- `teacher`

Access control is implemented via Python function decorators (`@student_required`, `@teacher_required`, `@login_required`). Route guards check authenticated user identity and role stored in server-managed session cookies:
```python
# Server-side guard prevents students from accessing teacher actions
@teacher_bp.route('/dashboard')
@teacher_required
def dashboard(): ...
```

### 2.2 Course-Section Data Isolation
University professors often manage multiple sections of the same subject (e.g. `CS101 CSE-A` and `CS101 CSE-B`). UniSync prevents cross-contamination of academic data through relational ownership checks:
- A faculty member can only start feedback sessions, view identified results, or answer questions for class offerings where `offering.teacher_id == g.teacher.id`.
- A student can only view class materials, submit feedback, or post questions for offerings where a verified `Enrollment` record exists.
- Any attempt to access unauthorized classes yields an HTTP 403 or immediate redirect with a security flash notice.

### 2.3 Student Identity Integrity
In lecture feedback, student identity cannot be forged or entered manually:
- Student identity (`user_id`, `full_name`, `roll_number`) is derived exclusively from the authenticated session context (`g.student`).
- The feedback form locks student identity and notifies them that their assigned teacher will identify them, but fellow students cannot access other responses.

### 2.4 CSRF Protection
All mutating HTTP requests (`POST`, `PUT`, `DELETE`) require a cryptographically secure token generated per session via `secrets.token_hex(32)`. Tokens are transmitted via form fields (`csrf_token`) or request headers (`X-CSRFToken`).

---

## 3. Dynamic 45-Second QR Feedback Mechanics

The 45-second feedback workflow is engineered to eliminate link-forwarding and preserve authentic, immediate in-class participation.

### 3.1 Session Creation & Expiry Derivation
1. Teacher selects a class and triggers `POST /feedback/start/<class_id>`.
2. The server records:
   $$\text{started\_at} = \text{now()}$$
   $$\text{expires\_at} = \text{started\_at} + 45\text{ seconds}$$
   $$\text{status} = \text{'active'}$$
   $$\text{session\_token} = \text{uuid4().hex}$$
3. Any prior active sessions for that course section are systematically transitioned to `'closed'`.

### 3.2 Dynamic QR Synthesis
The QR code is dynamically rendered on-the-fly using the Python `qrcode` and `Pillow` libraries at `GET /feedback/qr/<session_token>.png`. The image encodes:
$$\text{URL} = \text{https://<host>/feedback/scan/<session\_token>}$$
Colors are customized to Deep Espresso (`#514139`) and Vanilla White (`#FFFCF8`).

### 3.3 Server-Authoritative Expiration Enforcement
Client-side JavaScript countdown is merely a visual aid. The server authoritatively validates the timestamp on submission:
```python
if datetime.utcnow() > session.expires_at or session.status == 'closed':
    session.status = 'closed'
    db.session.commit()
    return render_template('feedback_error.html', message='Submission window expired.')
```
Late submissions arriving at $t > 45.0\text{s}$ are permanently rejected.

### 3.4 Real-Time State Synchronization & Transition
The teacher’s browser polls `GET /feedback/api/session/<session_token>/status` every 1.5 seconds. When:
$$\text{remaining\_seconds} \le 0 \quad \lor \quad \text{status} == \text{'closed'}$$
the teacher’s browser automatically redirects to `GET /feedback/results/<session_token>` without requiring manual refresh.

---

## 4. Frontend Design System & Accessibility

- **Palette:** Warm Cream (`#F4EEE5`), Deep Espresso (`#514139`), Muted Terracotta (`#A66D57`), Latte Beige (`#C7A68B`).
- **Typography:** `Inter`, `SF Pro Display`, `system-ui`.
- **Zero Emojis:** Strict adherence to professional inline SVG icons.
- **Glassmorphism:** Subtly frosted navigation with `backdrop-filter: blur(20px)`.
- **Theme Engine:** Pure CSS Custom Properties with light and warm dark mode toggle.
