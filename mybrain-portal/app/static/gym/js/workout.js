// Set counter per exercise
const setCounters = {};

async function logSet(btn, exerciseId, sessionId) {
  const card = btn.closest('.workout-exercise-card');
  const weightInput = card.querySelector('.weight-input');
  const repsInput = card.querySelector('.reps-input');

  const weight = weightInput.value || null;
  const reps = repsInput.value || null;

  if (!reps) {
    repsInput.focus();
    return;
  }

  if (!setCounters[exerciseId]) setCounters[exerciseId] = 0;
  setCounters[exerciseId]++;
  const setNum = setCounters[exerciseId];

  btn.disabled = true;
  btn.textContent = '...';

  try {
    const res = await fetch('/gym/api/log_set', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        exercise_id: exerciseId,
        session_id: sessionId,
        set_number: setNum,
        weight_used: weight ? parseFloat(weight) : null,
        reps_done: reps ? parseInt(reps) : null
      })
    });
    const data = await res.json();
    if (data.success) {
      appendSetRow(card, data.log_id, setNum, weight, reps, data.is_pr);
      weightInput.value = '';
      repsInput.value = '';
      weightInput.focus();
      if (data.is_pr) showPRFlash();
    }
  } finally {
    btn.disabled = false;
    btn.textContent = 'Log Set';
  }
}

function appendSetRow(card, logId, setNum, weight, reps, isPR) {
  const tbody = card.querySelector('.sets-tbody');
  const row = document.createElement('tr');
  row.setAttribute('data-log-id', logId);
  const weightDisplay = weight ? `${weight}kg` : '—';
  const prBadge = isPR ? '<span class="pr-badge">PR</span>' : '';
  row.innerHTML = `
    <td>${setNum}</td>
    <td>${weightDisplay}</td>
    <td>${reps || '—'}</td>
    <td>${prBadge}</td>
    <td><button class="btn-delete-set" onclick="deleteSet(this, ${logId})"><i class="fas fa-times"></i></button></td>
  `;
  tbody.appendChild(row);
}

function showPRFlash() {
  const existing = document.querySelector('.pr-flash');
  if (existing) existing.remove();

  const flash = document.createElement('div');
  flash.className = 'pr-flash';
  flash.innerHTML = '🏆 NEW PERSONAL RECORD!';
  document.body.appendChild(flash);
  setTimeout(() => flash.remove(), 2600);
}

async function deleteSet(btn, logId) {
  const row = btn.closest('tr');
  try {
    const res = await fetch(`/gym/api/delete_log_set/${logId}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) row.remove();
  } catch (e) {
    console.error('Delete failed', e);
  }
}

async function completeWorkout(routineId) {
  if (!confirm('Mark workout as complete and advance to next day?')) return;
  try {
    const res = await fetch(`/gym/routine/${routineId}/complete`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      window.location.href = '/gym/';
    }
  } catch (e) {
    window.location.href = '/gym/';
  }
}
