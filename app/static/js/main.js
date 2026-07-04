/**
 * main.js - LibraTrack Frontend Logic
 * Save at: LMS/app/static/js/main.js
 */

'use strict';

/* ── Confirm dangerous actions ─────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {

  // Confirm before submitting delete/return forms
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', e => {
      const msg = el.dataset.confirm || 'Are you sure?';
      if (!confirm(msg)) e.preventDefault();
    });
  });

  /* ── Member search autocomplete (issue book modal) ─────────── */
  const memberSearch = document.getElementById('memberSearch');
  const memberResults = document.getElementById('memberResults');
  const memberIdInput = document.getElementById('selectedMemberId');

  if (memberSearch) {
    let debounce;
    memberSearch.addEventListener('input', () => {
      clearTimeout(debounce);
      const q = memberSearch.value.trim();
      if (q.length < 2) { memberResults.innerHTML = ''; return; }
      debounce = setTimeout(() => fetchMembers(q), 280);
    });
  }

  function fetchMembers(q) {
    fetch(`/borrow/search-members?q=${encodeURIComponent(q)}`)
      .then(r => r.json())
      .then(data => {
        if (!memberResults) return;
        memberResults.innerHTML = '';
        if (!data.length) {
          memberResults.innerHTML = '<li class="list-group-item text-muted">No members found</li>';
          return;
        }
        data.forEach(m => {
          const li = document.createElement('li');
          li.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
          li.innerHTML = `
            <div>
              <strong>${m.name}</strong>
              <small class="text-muted ms-2">${m.member_id}</small>
            </div>
            <small class="text-muted">${m.active_borrows} active</small>`;
          li.style.cursor = 'pointer';
          li.addEventListener('click', () => {
            memberSearch.value = `${m.name} (${m.member_id})`;
            if (memberIdInput) memberIdInput.value = m.id;
            memberResults.innerHTML = '';
          });
          memberResults.appendChild(li);
        });
      })
      .catch(() => {});
  }

  /* ── Auto-init Bootstrap tooltips ──────────────────────────── */
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    new bootstrap.Tooltip(el, { trigger: 'hover' });
  });

  /* ── Toast auto-dismiss already handled in base.html ────────── */

  /* ── Sidebar active link highlight ─────────────────────────── */
  const path = window.location.pathname;
  document.querySelectorAll('.sidebar-link').forEach(link => {
    if (link.getAttribute('href') && path.startsWith(link.getAttribute('href'))) {
      link.classList.add('active');
    }
  });

  /* ── Preview uploaded image ─────────────────────────────────── */
  const coverInput = document.getElementById('cover_image');
  const coverPreview = document.getElementById('coverPreview');
  if (coverInput && coverPreview) {
    coverInput.addEventListener('change', () => {
      const file = coverInput.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = e => {
          coverPreview.src = e.target.result;
          coverPreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
      }
    });
  }

  /* ── Print page ─────────────────────────────────────────────── */
  document.querySelectorAll('[data-print]').forEach(btn => {
    btn.addEventListener('click', () => window.print());
  });

  /* ── Filter form auto-submit on select change ────────────────── */
  document.querySelectorAll('[data-autosubmit]').forEach(el => {
    el.addEventListener('change', () => el.closest('form').submit());
  });

});

/* ── Chart helpers ──────────────────────────────────────────────── */
window.LMS = {
  /**
   * Render a Bar chart.
   * @param {string} canvasId
   * @param {string[]} labels
   * @param {number[]} data
   * @param {string} label
   */
  barChart(canvasId, labels, data, label = 'Count') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label,
          data,
          backgroundColor: 'rgba(26,58,92,0.75)',
          borderColor: '#1a3a5c',
          borderWidth: 1,
          borderRadius: 4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
      }
    });
  },

  /**
   * Render a Doughnut chart.
   */
  doughnutChart(canvasId, labels, data, colors) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{ data, backgroundColor: colors, borderWidth: 2 }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } }
      }
    });
  },

  lineChart(canvasId, labels, data, label = 'Count') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label,
          data,
          borderColor: '#c8922a',
          backgroundColor: 'rgba(200,146,42,0.12)',
          tension: 0.35,
          fill: true,
          pointRadius: 4,
          pointBackgroundColor: '#c8922a',
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
      }
    });
  }
};
