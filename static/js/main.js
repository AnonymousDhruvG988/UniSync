/**
 * UniSync - Main Application Scripts
 * French Café visual interaction engine & Apple iOS 26 micro-interactions
 */

// Theme Management
function initTheme() {
  const savedTheme = localStorage.getItem('unisync_theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  const target = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', target);
  localStorage.setItem('unisync_theme', target);
}

// Modal Helpers with Smooth Scale & Backdrop Fade
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    const firstInput = modal.querySelector('input:not([type="hidden"]), select, textarea');
    if (firstInput) {
      setTimeout(() => firstInput.focus(), 150);
    }
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
}

// Mobile Menu with Backdrop Overlay & Accessible State
function toggleMobileMenu() {
  const drawer = document.getElementById('mobileMenuDrawer');
  const backdrop = document.getElementById('mobileMenuBackdrop');
  const menuBtn = document.querySelector('.mobile-menu-btn');
  
  if (drawer) {
    const isActive = drawer.classList.toggle('active');
    if (backdrop) backdrop.classList.toggle('active', isActive);
    if (menuBtn) {
      menuBtn.setAttribute('aria-expanded', isActive);
      menuBtn.classList.toggle('active', isActive);
    }
    document.body.style.overflow = isActive ? 'hidden' : '';
  }
}

function closeMobileMenu() {
  const drawer = document.getElementById('mobileMenuDrawer');
  const backdrop = document.getElementById('mobileMenuBackdrop');
  const menuBtn = document.querySelector('.mobile-menu-btn');
  
  if (drawer && drawer.classList.contains('active')) {
    drawer.classList.remove('active');
    if (backdrop) backdrop.classList.remove('active');
    if (menuBtn) {
      menuBtn.setAttribute('aria-expanded', 'false');
      menuBtn.classList.remove('active');
    }
    document.body.style.overflow = '';
  }
}

// Toast Notifications
function showToast(message, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `alert alert-${type} toast-item`;
  toast.innerText = message;

  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('toast-exit');
    setTimeout(() => toast.remove(), 350);
  }, 4000);
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initTheme();

  // Close modals when clicking backdrop
  document.querySelectorAll('.modal-backdrop').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal(modal.id);
      }
    });
  });

  // Close mobile drawer on link click
  const drawer = document.getElementById('mobileMenuDrawer');
  if (drawer) {
    drawer.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        closeMobileMenu();
      });
    });
  }

  // Keyboard accessibility: Escape key closes active modals & mobile menu
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-backdrop.active').forEach(m => closeModal(m.id));
      closeMobileMenu();
    }
  });

  // Smooth dismiss for flash alerts
  document.querySelectorAll('.alert button[data-dismiss]').forEach(btn => {
    btn.addEventListener('click', () => {
      const alertEl = btn.closest('.alert');
      if (alertEl) {
        alertEl.style.opacity = '0';
        alertEl.style.transform = 'translateY(-6px)';
        alertEl.style.transition = 'all 0.25s ease';
        setTimeout(() => alertEl.remove(), 260);
      }
    });
  });

  // Start real-time student survey poller
  initStudentSurveyPoller();
});

// Student Live Survey Polling & Alert System
function initStudentSurveyPoller() {
  const role = document.body.getAttribute('data-role');
  if (role !== 'student') return;

  const alertContainer = document.getElementById('globalStudentSurveyAlert');
  let currentSessionToken = null;

  function checkActiveSurveys() {
    fetch('/student/api/active-feedback-check')
      .then(res => {
        if (!res.ok) throw new Error('Network error');
        return res.json();
      })
      .then(data => {
        if (data.has_active && data.active_sessions.length > 0) {
          const sess = data.active_sessions[0];
          if (alertContainer) {
            alertContainer.style.display = 'block';

            // Only rebuild HTML when active session token changes to prevent UI flickering
            if (currentSessionToken !== sess.session_token) {
              currentSessionToken = sess.session_token;
              alertContainer.innerHTML = `
                <div class="student-live-survey-banner">
                  <div style="display: flex; align-items: center; gap: 14px; flex-wrap: wrap;">
                    <span class="survey-in-progress-pill">
                      <span class="pulse-dot"></span>
                      Live Survey in Progress
                    </span>
                    <div>
                      <strong style="color: var(--text-primary); font-size: 0.95rem;">${sess.course_name} (${sess.section_name})</strong>
                      <div style="font-size: 0.825rem; color: var(--text-secondary); margin-top: 2px;">
                        ${sess.teacher_name} is taking feedback of today's class &bull; <strong id="globalBannerTimer" style="color: var(--primary-button); font-variant-numeric: tabular-nums;">${sess.remaining_seconds}s remaining</strong>
                      </div>
                    </div>
                  </div>
                  <div style="display: flex; gap: 10px; align-items: center;">
                    <a href="${sess.feedback_url}" class="btn btn-primary btn-sm">
                      <span>Give Feedback</span>
                      <svg class="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                    </a>
                  </div>
                </div>
              `;
            } else {
              // Smooth in-place timer decrement without DOM flash
              const timerEl = document.getElementById('globalBannerTimer');
              if (timerEl) {
                timerEl.textContent = `${sess.remaining_seconds}s remaining`;
              }
            }
          }

          // In class detail workspace, dynamically update the feedback tab badge
          const tabFeedbackBtn = document.getElementById('tabFeedbackBtn');
          if (tabFeedbackBtn && !tabFeedbackBtn.querySelector('.live-survey-dot')) {
            const dot = document.createElement('span');
            dot.className = 'live-survey-dot';
            dot.style.cssText = 'display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--error); margin-left:6px; animation: pulseAnimation 1.5s infinite;';
            tabFeedbackBtn.appendChild(dot);
          }
        } else {
          currentSessionToken = null;
          if (alertContainer) {
            alertContainer.style.display = 'none';
            alertContainer.innerHTML = '';
          }
          const liveDot = document.querySelector('.live-survey-dot');
          if (liveDot) liveDot.remove();
        }
      })
      .catch(err => {
        // Silent catch for network hiccups
      });
  }

  // Initial check & interval every 2.5 seconds
  checkActiveSurveys();
  setInterval(checkActiveSurveys, 2500);
}
