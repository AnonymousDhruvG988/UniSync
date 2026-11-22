/**
 * UniSync - Results Search, Filter & Question Workspace Utilities
 * Client-side search and filtering for identified student submission tables and question feeds.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Feedback Results Table Filtering & Search
  const searchInput = document.getElementById('studentTableSearch');
  const filterPills = document.querySelectorAll('.filter-pill');
  const tableBody = document.getElementById('submissionTableBody');
  const tableRows = tableBody ? tableBody.querySelectorAll('tr:not(.empty-state-row)') : [];

  let currentFilter = 'all';
  let searchQuery = '';

  function filterTable() {
    if (!tableBody || tableRows.length === 0) return;

    let visibleCount = 0;
    tableRows.forEach(row => {
      const roll = (row.getAttribute('data-roll') || '').toLowerCase();
      const name = (row.getAttribute('data-name') || '').toLowerCase();
      const understanding = (row.getAttribute('data-understanding') || '').toLowerCase();

      const matchesSearch = !searchQuery || roll.includes(searchQuery) || name.includes(searchQuery);
      const matchesFilter = (currentFilter === 'all') || (understanding === currentFilter);

      if (matchesSearch && matchesFilter) {
        row.style.display = '';
        visibleCount++;
      } else {
        row.style.display = 'none';
      }
    });

    // Handle empty state row
    let emptyRow = document.getElementById('tableNoMatchesRow');
    if (visibleCount === 0) {
      if (!emptyRow) {
        emptyRow = document.createElement('tr');
        emptyRow.id = 'tableNoMatchesRow';
        emptyRow.className = 'empty-state-row';
        emptyRow.innerHTML = `<td colspan="7" style="text-align: center; padding: 32px 16px; color: var(--text-muted); font-size: 0.9rem;">No students found matching "${searchQuery}" in ${currentFilter === 'all' ? 'any category' : currentFilter}.</td>`;
        tableBody.appendChild(emptyRow);
      } else {
        emptyRow.style.display = '';
        emptyRow.querySelector('td').textContent = `No students found matching "${searchQuery}" in ${currentFilter === 'all' ? 'any category' : currentFilter}.`;
      }
    } else if (emptyRow) {
      emptyRow.style.display = 'none';
    }
  }

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value.toLowerCase().trim();
      filterTable();
    });
  }

  filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      filterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      currentFilter = pill.getAttribute('data-filter') || 'all';
      filterTable();
    });
  });

  // 2. Question Search & Filter on Questions Page
  const qSearchInput = document.getElementById('questionSearchInput');
  const qCards = document.querySelectorAll('.question-item');
  const qContainer = qCards.length > 0 ? qCards[0].parentElement : null;

  if (qSearchInput && qCards.length > 0) {
    qSearchInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      let matchCount = 0;

      qCards.forEach(card => {
        const title = (card.querySelector('.question-title')?.textContent || '').toLowerCase();
        const text = (card.textContent || '').toLowerCase();
        if (!q || title.includes(q) || text.includes(q)) {
          card.style.display = '';
          matchCount++;
        } else {
          card.style.display = 'none';
        }
      });

      let noMatchNotice = document.getElementById('noQuestionsMatchNotice');
      if (matchCount === 0) {
        if (!noMatchNotice && qContainer) {
          noMatchNotice = document.createElement('div');
          noMatchNotice.id = 'noQuestionsMatchNotice';
          noMatchNotice.className = 'card';
          noMatchNotice.style.cssText = 'text-align: center; padding: 36px 20px; color: var(--text-muted);';
          noMatchNotice.textContent = `No questions found matching "${q}".`;
          qContainer.appendChild(noMatchNotice);
        } else if (noMatchNotice) {
          noMatchNotice.style.display = '';
          noMatchNotice.textContent = `No questions found matching "${q}".`;
        }
      } else if (noMatchNotice) {
        noMatchNotice.style.display = 'none';
      }
    });
  }
});
