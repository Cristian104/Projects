// Track selected swap per meal
const mealVariants = {};

function selectSwap(btn, mealId, variant) {
  // Toggle selection in this meal's swap group
  const card = btn.closest('.nutr-meal-card');
  card.querySelectorAll('.nutr-swap-pill').forEach(p => p.classList.remove('selected'));
  btn.classList.add('selected');
  mealVariants[mealId] = variant;
}

async function toggleMeal(mealId, btn) {
  const variant = mealVariants[mealId] || null;
  try {
    const res = await fetch('/nutrition/api/toggle_meal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ meal_id: mealId, variant })
    });
    const data = await res.json();
    if (data.success) {
      const card = btn.closest('.nutr-meal-card');
      if (data.done) {
        card.classList.add('done');
        btn.classList.add('active');
        btn.innerHTML = '<i class="fas fa-check-circle"></i> Done';
      } else {
        card.classList.remove('done');
        btn.classList.remove('active');
        btn.innerHTML = '<i class="far fa-circle"></i> Mark Done';
      }
    }
  } catch (e) {
    console.error('Toggle meal failed', e);
  }
}

async function addWater(amount) {
  try {
    const res = await fetch('/nutrition/api/water', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount_ml: amount })
    });
    const data = await res.json();
    if (data.success) {
      const total = data.amount_ml;
      document.getElementById('water-amount').textContent = total;
      const pct = Math.min((total / 3000) * 100, 100);
      document.getElementById('water-bar').style.width = pct + '%';
    }
  } catch (e) {
    console.error('Water log failed', e);
  }
}

async function toggleSupplement(supId, row) {
  try {
    const res = await fetch('/nutrition/api/toggle_supplement', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ supplement_id: supId })
    });
    const data = await res.json();
    if (data.success) {
      const icon = row.querySelector('i');
      if (data.done) {
        row.classList.add('done');
        icon.className = 'fas fa-check-circle';
        icon.style.color = 'var(--accent)';
      } else {
        row.classList.remove('done');
        icon.className = 'far fa-circle';
        icon.style.color = '#555';
      }
    }
  } catch (e) {
    console.error('Toggle supplement failed', e);
  }
}
