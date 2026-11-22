/**
 * UniSync - Dynamic 45-Second QR Feedback Countdown & Real-Time Polling Engine
 * Synchronizes client countdown with server timestamp and automatically transitions
 * to the verified results screen upon session closure.
 */

document.addEventListener('DOMContentLoaded', () => {
  const timerContainer = document.getElementById('qrLiveSession');
  if (!timerContainer) return;

  const sessionToken = timerContainer.getAttribute('data-session-token');
  const serverRemainingSeconds = parseInt(timerContainer.getAttribute('data-remaining-seconds') || '45', 10);
  const totalDuration = 45; // 45 seconds strict window
  const resultsUrl = timerContainer.getAttribute('data-results-url');

  const numberDisplay = document.getElementById('timerNumberDisplay');
  const progressCircle = document.getElementById('timerProgressCircle');
  const responseCountBadge = document.getElementById('liveResponseCount');
  const statusNotice = document.getElementById('sessionStatusNotice');

  // SVG circle calculation
  const circleRadius = 100;
  const circumference = 2 * Math.PI * circleRadius; // ~628.3

  if (progressCircle) {
    progressCircle.style.strokeDasharray = `${circumference}`;
  }

  // Calculate local end time based on server remaining seconds
  const endTime = Date.now() + (serverRemainingSeconds * 1000);
  let isClosed = false;

  function updateVisuals(remainingSec) {
    if (numberDisplay) {
      numberDisplay.textContent = Math.max(0, Math.ceil(remainingSec));
    }

    if (progressCircle) {
      const progress = Math.max(0, Math.min(1, remainingSec / totalDuration));
      const offset = circumference * (1 - progress);
      progressCircle.style.strokeDashoffset = offset;

      // Color transition from Terracotta to Warning to Error as timer nears 0
      if (remainingSec <= 10) {
        progressCircle.style.stroke = 'var(--error)';
      } else if (remainingSec <= 20) {
        progressCircle.style.stroke = 'var(--warning)';
      } else {
        progressCircle.style.stroke = 'var(--muted-terracotta)';
      }
    }
  }

  // 1-second interval tick for smooth countdown
  const timerInterval = setInterval(() => {
    const now = Date.now();
    const remainingMs = endTime - now;
    const remainingSec = remainingMs / 1000;

    if (remainingSec <= 0) {
      clearInterval(timerInterval);
      clearInterval(pollInterval);
      handleSessionCompletion();
    } else {
      updateVisuals(remainingSec);
    }
  }, 250);

  // Poll backend status every 1.5 seconds for live participant updates and authoritative expiration
  const pollInterval = setInterval(() => {
    if (isClosed) return;

    fetch(`/feedback/api/session/${sessionToken}/status`)
      .then(res => res.json())
      .then(data => {
        // Update response count badge
        if (responseCountBadge && data.response_count !== undefined) {
          responseCountBadge.textContent = data.response_count;
        }

        // Check if server closed session
        if (data.is_expired || data.status === 'closed') {
          clearInterval(timerInterval);
          clearInterval(pollInterval);
          handleSessionCompletion(data.results_url || resultsUrl);
        }
      })
      .catch(err => {
        console.error('UniSync polling error:', err);
      });
  }, 1500);

  function handleSessionCompletion(targetUrl = resultsUrl) {
    if (isClosed) return;
    isClosed = true;

    updateVisuals(0);

    if (statusNotice) {
      statusNotice.innerHTML = `
        <div class="alert alert-info" style="margin-top: 16px; font-weight: 600;">
          Feedback window concluded. Loading student submission analytics...
        </div>
      `;
    }

    // Smooth transition to results page
    setTimeout(() => {
      window.location.href = targetUrl;
    }, 1200);
  }

  // Initial draw
  updateVisuals(serverRemainingSeconds);
});
