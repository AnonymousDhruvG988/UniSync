/**
 * UniSync - Student Feedback Form Interaction
 * Handles rating buttons, understanding selection, remaining window awareness,
 * and double-submission protection.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Rating Selector (1 to 5) with tactile visual feedback
  const ratingButtons = document.querySelectorAll('.rating-btn');
  const ratingInput = document.getElementById('satisfactionInput');

  ratingButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const val = btn.getAttribute('data-value');
      if (ratingInput) {
        ratingInput.value = val;
      }
      ratingButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  // 2. Choice Cards (Understanding selection)
  const choiceCards = document.querySelectorAll('.choice-card');
  choiceCards.forEach(card => {
    card.addEventListener('click', () => {
      const radio = card.querySelector('input[type="radio"]');
      if (radio) {
        radio.checked = true;
      }
      choiceCards.forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
    });
  });

  // 3. Student-Side Remaining Window Countdown
  const countdownEl = document.getElementById('studentTimeRemaining');
  if (countdownEl) {
    let secondsLeft = parseInt(countdownEl.getAttribute('data-seconds') || '45', 10);
    const interval = setInterval(() => {
      secondsLeft -= 1;
      if (secondsLeft <= 0) {
        clearInterval(interval);
        countdownEl.textContent = '0s (Window Closing)';
        countdownEl.style.color = 'var(--error)';
      } else {
        countdownEl.textContent = `${secondsLeft}s remaining`;
        if (secondsLeft <= 10) {
          countdownEl.style.color = 'var(--error)';
        }
      }
    }, 1000);
  }

  // 4. Form Submit Guard & Double-Click Prevention
  const form = document.getElementById('studentFeedbackForm');
  if (form) {
    form.addEventListener('submit', (e) => {
      const satisfaction = ratingInput ? ratingInput.value : '';
      const understanding = form.querySelector('input[name="understanding"]:checked');

      if (!understanding) {
        e.preventDefault();
        alert('Please indicate your level of understanding for today\'s class.');
        return false;
      }

      if (!satisfaction) {
        e.preventDefault();
        alert('Please select a satisfaction rating between 1 and 5.');
        return false;
      }

      // Disable submit button to prevent double-post
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.style.opacity = '0.75';
        submitBtn.innerHTML = `<span>Recording Feedback...</span>`;
      }
    });
  }
});
