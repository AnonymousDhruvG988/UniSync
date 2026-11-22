# UniSync &mdash; Comprehensive User Guide

> **Official Guide:** Student &amp; Faculty Operations Manual  
> **Platform Version:** 1.0.0 (French Café Edition)  

---

## Part 1: Faculty / Teacher User Guide

### 1.1 Accessing the Faculty Workspace
1. Navigate to `http://127.0.0.1:5000/login` (or click **Sign In** on the landing page).
2. Enter your faculty email (e.g. `dr.sharma@university.edu`) and password (`Faculty@123`).
3. Or use the **Quick Demo: Faculty** shortcut button on the sign-in page.

### 1.2 Managing Class Offerings
- **Dashboard Overview:** Displays your key teaching metrics: total assigned classes, total enrolled students, total collected feedback responses, and pending student questions.
- **Separate Class Cards:** Every assigned course-section appears as an independent card (e.g. `CS101 CSE-A`, `CS101 CSE-B`, `CS201 CSE-A`). Data from different sections is never commingled.
- **Creating a New Class Offering:**
  1. Click **Add Class Offering** on the dashboard or classes page.
  2. Enter the Course Code (e.g. `CS301`), Title (e.g. `Operating Systems`), Section (e.g. `CSE-A`), and Semester (`4`).
  3. Click **Generate Class Offering**.
  4. UniSync immediately synthesizes an exclusive alphanumeric join code (e.g. `OPSYS-A`). Share this join code with students in that specific section.

### 1.3 Running the Dynamic 45-Second QR Feedback Session
1. In your classroom page or from any class card on the dashboard, click **Start 45s Feedback Session**.
2. The system initiates an authoritative server session expiring at exactly $\text{current\_time} + 45\text{ seconds}$.
3. Project your screen or show the large circular timer to your students. The page renders:
   - Dynamic scannable QR Code.
   - Large animated countdown timer starting at 45 seconds.
   - Live pulse counter displaying submitted responses in real time.
4. **Automatic Transition:** You do not need to refresh the page. As soon as the countdown reaches 0 seconds, the server closes the session and the browser automatically redirects to the **Verified Results Dashboard**.

### 1.4 Reviewing Identified Student Feedback, Weekly Bar Graphs & CSV Reports
1. **Weekly Satisfaction & Comprehension Bar Graph:**
   - Displayed prominently across the Faculty Dashboard, Class Workspace (under Feedback History tab), and Results View.
   - A vertical bar chart visualizes satisfactory scores (scale 1.0 to 5.0) per teaching week (e.g., Week 1, Week 2, Week 3, Week 4) with exact score callouts (e.g. `4.6/5.0`).
   - A cohort comprehension rate stacked meter shows the percentage breakdown of students who understood, partially understood, or needed further explanation for each session.
   - Highlights overall term satisfaction score, total in-class evaluations, and the highest-rated teaching session.
2. **Identified Submission Table:** Review every participating student's name, roll number, exact submission timestamp, understanding selection, and satisfaction rating.
3. **Filtering & Search:**
   - Type in the search box to filter instantly by roll number or student name.
   - Click the filter pills (**All**, **Understood**, **Partially**, **Needs Help**) to isolate students requiring academic intervention.
4. **CSV Export:** Click **Export CSV Report** to download a formatted spreadsheet (`.csv`) containing the verified submission roster for departmental records.

### 1.5 Managing and Answering Student Doubts
1. Open the **Questions** tab inside a classroom or click **Questions** in the top navigation bar.
2. View pending questions with student roll number, question title, and detailed explanation.
3. Opening an unanswered question automatically transitions its status from `New` to `Viewed`.
4. Type an authoritative explanation in the reply composer and click **Send Reply**.
5. The question automatically transitions to `Answered`, and the student receives an instant in-app notification.
6. When the student indicates comprehension, mark the question as `Resolved`.

---

## Part 2: Student User Guide

### 2.1 Student Registration & Sign-In
1. Click **Create Account** on the landing page and select **University Student**.
2. Provide your Full Name, University Email, Roll Number (e.g. `24CSE001`), Programme, Semester, Section, and Password.
3. Or use the **Quick Demo: Student** button on the sign-in page to log in as Aarav Sharma (`24CSE001`).

### 2.2 Joining a Teacher’s Class
1. On your Student Dashboard, click **Join Class with Code**.
2. Enter the 6-character code announced by your instructor (e.g. `PROG-A`, `DATA-A`, or `PHYS-A`).
3. Click **Join Class**. You will immediately be enrolled in that course-section and the card will appear under **My Enrolled Classes**.

### 2.3 Participating in Classroom Feedback Check-ins (Dual Options: QR or In-App)
Students can participate in in-class feedback through two natural methods:

- **Option A (In-App Live Alert & Class Tab — No QR Code Needed):**
  1. As soon as the teacher clicks "Start Feedback Session", an in-app notification is sent to your notification drawer: *"Live Class Feedback: [Teacher Name] is taking feedback of today's class"*.
  2. If you are browsing your Student Dashboard or any page on UniSync, a real-time alert banner automatically pops down stating:  
     `[PULSE DOT] LIVE SURVEY IN PROGRESS: [Course Name] (Section [Sec]) — [Teacher Name] is taking feedback of today's class • [X]s remaining`
  3. Inside your class workspace, the **Lecture Feedback & Survey** tab dynamically pulses with a **SURVEY IS GOING ON** badge, and a prominent survey card appears.
  4. Simply click **Give Short Feedback Now** to open the 3-question form directly in your browser without scanning any QR code.

- **Option B (Phone Camera QR Scan):**
  1. If you are using a mobile phone, scan the dynamic QR code projected on the classroom screen.
  2. The camera link immediately authenticates your student profile and opens the feedback questionnaire.

### 2.4 Completing the Short Feedback Questionnaire
1. The form confirms your identity: *Authenticated Student Check-in: [Your Name] ([Your Roll Number])*.
2. Answer the 3 concise questions:
   - **Q1:** Understanding level (*I understood the topic* / *I partially understood* / *I need further explanation*).
   - **Q2:** Satisfaction rating (Select numeric pill 1 to 5).
   - **Q3:** Concept clarification request (Optional written note).
3. Click **Submit Classroom Feedback** before the countdown reaches zero.

### 2.4 Asking Doubts & Receiving Instructor Replies
1. Open any enrolled class workspace.
2. Click **Ask a Question**.
3. Enter a clear headline and description of your doubt.
4. When your teacher answers, your top navigation notification bell will display an unread alert pill.
5. Click the notification to read the teacher's reply, ask follow-up questions, or mark the doubt as `Resolved`.
