let currentJobs = [];
let currentLang = localStorage.getItem('cvManager_lang') || 'pl';
let currentScope = 'all';
let currentWorkMode = 'all';
let currentStatusFilter = 'active';
let selectedJobIndex = null;

document.addEventListener('DOMContentLoaded', () => {
  setLanguage(currentLang, false);
  loadProfile();
  loadJobs();
});

function setLanguage(lang, reload = true) {
  currentLang = lang;
  localStorage.setItem('cvManager_lang', lang);

  if(document.getElementById('langPlBtn')) document.getElementById('langPlBtn').classList.toggle('active', lang === 'pl');
  if(document.getElementById('langEnBtn')) document.getElementById('langEnBtn').classList.toggle('active', lang === 'en');

  const isEn = (lang === 'en');
  if(document.getElementById('statusLabel')) document.getElementById('statusLabel').textContent = isEn ? 'View:' : 'Widok:';
  if(document.getElementById('btnActiveTab')) document.getElementById('btnActiveTab').textContent = isEn ? '📋 Active Offers' : '📋 Oferty (Active)';
  if(document.getElementById('btnAppliedTab')) document.getElementById('btnAppliedTab').textContent = isEn ? '✅ Applied Jobs' : '✅ Aplikowane (Applied)';

  if(document.getElementById('scopeLabel')) document.getElementById('scopeLabel').textContent = isEn ? 'Scope:' : 'Zasięg:';
  if(document.getElementById('scopeAllBtn')) document.getElementById('scopeAllBtn').textContent = isEn ? '🌐 All Locations' : '🌐 Wszystkie';
  if(document.getElementById('scopeLocalBtn')) document.getElementById('scopeLocalBtn').textContent = isEn ? '📍 Częstochowa' : '📍 Częstochowa';
  if(document.getElementById('scopeCountryBtn')) document.getElementById('scopeCountryBtn').textContent = isEn ? '🇵🇱 All Poland' : '🇵🇱 Cała Polska';

  if(document.getElementById('modeLabel')) document.getElementById('modeLabel').textContent = isEn ? 'Mode:' : 'Tryb:';
  if(document.getElementById('modeAllBtn')) document.getElementById('modeAllBtn').textContent = isEn ? 'All' : 'Wszystkie';
  if(document.getElementById('modeHybridBtn')) document.getElementById('modeHybridBtn').textContent = isEn ? '⚡ Hybrid' : '⚡ Hybrid';
  if(document.getElementById('modeOnsiteBtn')) document.getElementById('modeOnsiteBtn').textContent = isEn ? '🏢 On-site' : '🏢 On-site';

  if(document.getElementById('btnExportCsv')) document.getElementById('btnExportCsv').innerHTML = isEn ? '<span>📥 Export CSV</span>' : '<span>📥 Pobierz CSV</span>';
  if(document.getElementById('btnExtendSearch')) document.getElementById('btnExtendSearch').innerHTML = isEn ? '<span>🔍 Extend Search</span>' : '<span>🔍 Rozszerz wyszukiwanie</span>';
  if(document.getElementById('btnCustomJob')) document.getElementById('btnCustomJob').innerHTML = isEn ? '<span>✨ Analyze Custom Job</span>' : '<span>✨ Analizuj własną ofertę</span>';

  if(document.getElementById('lblSalaryEstimatorHeader')) document.getElementById('lblSalaryEstimatorHeader').textContent = isEn ? '💰 AI Salary Range Estimator & Advice:' : '💰 Rynkowy Estymator Wynagrodzenia (AI Salary Estimator):';
  if(document.getElementById('lblEstRange')) document.getElementById('lblEstRange').textContent = isEn ? 'Estimated Range:' : 'Szacowany przedział:';
  if(document.getElementById('lblRecAsk')) document.getElementById('lblRecAsk').textContent = isEn ? 'Recommended Target Ask:' : 'Rekomendowana stawka (Target):';

  if(document.getElementById('lblDownloadZipHeader')) document.getElementById('lblDownloadZipHeader').textContent = isEn ? '📦 Download Application Package (.ZIP)' : '📦 Pobierz Paczkę Aplikacyjną (.ZIP)';
  if(document.getElementById('lblZipDetails')) document.getElementById('lblZipDetails').textContent = isEn ? 'Includes: Cover Letter (.DOCX + .PDF) & Candidate CV (.PDF)' : 'Zawiera: List Motywacyjny (.DOCX + .PDF) oraz CV kandydata (.PDF)';
  if(document.getElementById('lblIncludeCv')) document.getElementById('lblIncludeCv').textContent = isEn ? 'Include Candidate CV PDF' : 'Dołącz moje CV PDF';
  if(document.getElementById('btnDownloadZip')) document.getElementById('btnDownloadZip').textContent = isEn ? '📦 Download ZIP' : '📦 Pobierz ZIP';

  if(document.getElementById('btnCopyBlurb')) document.getElementById('btnCopyBlurb').textContent = isEn ? '📋 Copy Cover Message' : '📋 Kopiuj treść wiadomości';
  if(document.getElementById('btnToggleDesc')) document.getElementById('btnToggleDesc').textContent = isEn ? '🌐 View English Description' : '🌐 Zobacz opis po angielsku';

  if (reload && currentJobs.length > 0) {
    renderJobs(currentJobs);
  }
}

function setStatusFilter(filter, btn) {
  currentStatusFilter = filter;
  document.querySelectorAll('#btnActiveTab, #btnAppliedTab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  loadJobs();
}

function setScope(scope, btn) {
  currentScope = scope;
  document.querySelectorAll('#scopeAllBtn, #scopeLocalBtn, #scopeCountryBtn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  loadJobs();
}

function setWorkMode(mode, btn) {
  currentWorkMode = mode;
  document.querySelectorAll('#modeAllBtn, #modeHybridBtn, #modeOnsiteBtn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  loadJobs();
}

async function loadProfile() {
  try {
    const res = await fetch('/api/profile');
    if (!res.ok) return;
    const profile = await res.json();

    if(document.getElementById('profileName')) document.getElementById('profileName').textContent = profile.name || 'Kamila Drewniak';
    if(document.getElementById('profileHeadline')) document.getElementById('profileHeadline').textContent = profile.headline || '';
    
    if (profile.skills) {
      const pillsContainer = document.getElementById('profilePills');
      const topSkills = profile.skills.slice(0, 5);
      pillsContainer.innerHTML = topSkills.map(s => `<span class="pill">✨ ${s}</span>`).join('') +
        `<span class="pill">🇬🇧 Angielski (C1)</span>` +
        `<span class="pill">📍 ${profile.location || 'Częstochowa'}</span>`;
    }
  } catch (err) {
    console.error('Failed to load profile:', err);
  }
}

async function loadJobs() {
  const grid = document.getElementById('jobGrid');
  const isEn = (currentLang === 'en');
  grid.innerHTML = `<div style="text-align: center; padding: 40px; color: #94a3b8;">${isEn ? 'Loading job offers...' : 'Ładowanie ofert pracy...'}</div>`;

  try {
    const res = await fetch(`/api/jobs?scope=${currentScope}&work_mode=${currentWorkMode}&status_filter=${currentStatusFilter}`);
    const data = await res.json();
    currentJobs = data.jobs || [];
    renderJobs(currentJobs);
  } catch (err) {
    grid.innerHTML = `<div style="text-align: center; color: #ef4444; padding: 40px;">Error: ${err.message}</div>`;
  }
}

function renderProgressBar(percentage, statusText, subText) {
  return `
    <div class="loader-container">
      <div class="loader-spinner"></div>
      <div class="loader-status-text">${statusText} (${percentage}%)</div>
      <div class="progress-bar-bg">
        <div class="progress-bar-fill" style="width: ${percentage}%;"></div>
      </div>
      <div class="loader-subtext">${subText}</div>
    </div>
  `;
}

async function extendSearch() {
  const grid = document.getElementById('jobGrid');
  const isEn = (currentLang === 'en');

  let progress = 8;
  grid.innerHTML = renderProgressBar(
    progress,
    isEn ? '🔍 Connecting to job search APIs...' : '🔍 Łączenie z API wyszukiwania ofert...',
    isEn ? 'Searching Częstochowa, Śląsk & Poland hybrid roles' : 'Przeszukiwanie ofert Częstochowa, Śląsk i Polska hybrydowa'
  );

  const progressInterval = setInterval(() => {
    if (progress < 96) {
      progress += Math.floor(Math.random() * 5) + 3;
      if (progress > 96) progress = 96;

      let msg = isEn ? '🔍 Scraping live job listings...' : '🔍 Pobieranie świeżych ofert z sieci...';
      let sub = isEn ? 'Processing active job postings in Częstochowa & Poland' : 'Przetwarzanie aktywnych ogłoszeń w Częstochowie i Polsce';

      if (progress > 25 && progress <= 55) {
        msg = isEn ? '🤖 Evaluating candidate match scores with Gemini 3.6 Flash AI...' : '🤖 Ocena dopasowania kandydata z Gemini 3.6 Flash AI...';
        sub = isEn ? 'Comparing C1 Business English & Malta/Turkey experience' : 'Porównywanie języka C1 i doświadczenia z Malty i Turcji';
      } else if (progress > 55 && progress <= 85) {
        msg = isEn ? '💰 Estimating market salary ranges for Poland...' : '💰 Szacowanie rynkowych widełek wynagrodzeń...';
        sub = isEn ? 'Calculating target asks and negotiation advice' : 'Wyliczanie stawek dla Częstochowy i Polski';
      } else if (progress > 85) {
        msg = isEn ? '⚡ Indexing active jobs...' : '⚡ Indeksowanie aktywnych ofert...';
        sub = isEn ? 'Cover letters will be generated on demand when requested' : 'Listy motywacyjne generowane są na życzenie';
      }

      grid.innerHTML = renderProgressBar(progress, msg, sub);
    }
  }, 500);

  try {
    const res = await fetch('/api/jobs/extend-search', { method: 'POST' });
    const data = await res.json();
    
    clearInterval(progressInterval);
    grid.innerHTML = renderProgressBar(
      100,
      isEn ? '✨ Done! Fresh active listings updated!' : '✨ Gotowe! Zaktualizowano aktywne oferty!',
      isEn ? `Successfully evaluated ${data.count} job listings` : `Pomyślnie oceniono ${data.count} ofert pracy`
    );

    setTimeout(() => {
      loadJobs();
    }, 500);
  } catch (err) {
    clearInterval(progressInterval);
    alert('Error extending search: ' + err.message);
    loadJobs();
  }
}

async function markApplied(jobId) {
  try {
    await fetch(`/api/jobs/${jobId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'applied' })
    });
    alert(currentLang === 'en' ? '✅ Marked as Applied!' : '✅ Oznaczono jako Aplikowane!');
    loadJobs();
  } catch (err) {
    alert('Error marking applied: ' + err.message);
  }
}

async function dismissJob(jobId) {
  if (!confirm(currentLang === 'en' ? 'Remove this job offer from your list?' : 'Usunąć tę ofertę z listy?')) return;
  try {
    await fetch(`/api/jobs/${jobId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'dismissed' })
    });
    loadJobs();
  } catch (err) {
    alert('Error dismissing job: ' + err.message);
  }
}

function helperExtractArray(raw) {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw;
  if (typeof raw === 'object') {
    if (Array.isArray(raw[currentLang])) return raw[currentLang];
    if (Array.isArray(raw.pl)) return raw.pl;
    if (Array.isArray(raw.en)) return raw.en;
    return Object.values(raw).filter(x => typeof x === 'string');
  }
  if (typeof raw === 'string') return [raw];
  return [];
}

function helperExtractText(raw) {
  if (!raw) return '';
  if (typeof raw === 'string') return raw;
  if (typeof raw === 'object') {
    return raw[currentLang] || raw.pl || raw.en || '';
  }
  return String(raw);
}

function renderJobs(jobs) {
  const grid = document.getElementById('jobGrid');
  const isEn = (currentLang === 'en');

  if (!jobs || jobs.length === 0) {
    const emptyText = isEn ? 'No job offers found in this category.' : 'Brak ofert w tej kategorii.';
    grid.innerHTML = `<div style="text-align: center; padding: 40px; color: #94a3b8; font-weight:500;">${emptyText}</div>`;
    return;
  }

  grid.innerHTML = jobs.map((job, idx) => {
    const match = job.match || {};
    const score = match.match_score || 85;
    
    let summaryText = helperExtractText(match.summary);
    if (summaryText.length > 180) summaryText = summaryText.substring(0, 180) + '...';
    
    let strengthsArray = helperExtractArray(match.strengths);
    if (strengthsArray.length > 3) strengthsArray = strengthsArray.slice(0, 3);

    const sal = match.salary_estimator || {};
    const estRange = sal.estimated_range || job.salary || '6,5k - 8,5k PLN';

    const isApplied = (job.user_status === 'applied');

    return `
      <div class="job-card" style="padding: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; gap: 12px; flex-wrap: wrap;">
          <div style="flex: 1; min-width: 200px;">
            <h3 style="font-size: 18px; font-weight: 700; color: #e5e2e1; margin-bottom: 8px; line-height: 1.3;">${job.title}</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center;">
              <span style="font-size: 13px; color: #A1A1AA; display:flex; align-items:center; gap:4px;"><span class="material-symbols-outlined" style="font-size:14px;">business</span> ${job.company}</span>
              <span style="font-size: 13px; color: #A1A1AA; display:flex; align-items:center; gap:4px;"><span class="material-symbols-outlined" style="font-size:14px;">location_on</span> ${job.location}</span>
              ${isApplied ? `<span class="pill" style="background: rgba(16,185,129,0.15); color: #34d399; font-weight: 700; font-size:11px; padding: 2px 8px;">APPLIED</span>` : ''}
            </div>
          </div>
          <div class="score-badge" style="flex-shrink: 0;">
            <span class="material-symbols-outlined" style="font-size:16px;">bolt</span> ${score}%
          </div>
        </div>

        <div style="font-size: 13px; color: #34d399; font-weight: 500; margin-bottom: 12px; line-height: 1.5;">
          <span class="material-symbols-outlined" style="font-size:14px; vertical-align: middle; margin-right: 4px;">lightbulb</span>${isEn ? 'Why it matches:' : 'Dlaczego pasuje:'} ${summaryText}
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 20px;">
          ${strengthsArray.map(s => `<span class="strength-tag">${s}</span>`).join('')}
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 12px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 16px;">
          <button class="btn-apply" onclick="openBlurbModal(${idx})">
            <span class="material-symbols-outlined" style="font-size:18px;">analytics</span> ${isEn ? 'AI Analysis' : 'Analiza AI'}
          </button>
          ${!isApplied ? `
            <button class="btn-apply" style="flex: 0 0 auto; padding: 12px; border-color: rgba(48,209,88,0.3); color: #30D158;" onclick="markApplied('${job.id}')" title="${isEn ? 'Mark Applied' : 'Oznacz jako aplikowane'}">
              <span class="material-symbols-outlined" style="font-size:18px;">check</span>
            </button>
          ` : ''}
          <button class="btn-apply" style="flex: 0 0 auto; padding: 12px; border-color: rgba(239,68,68,0.3); color: #f87171;" onclick="dismissJob('${job.id}')" title="${isEn ? 'Dismiss' : 'Odrzuć'}">
            <span class="material-symbols-outlined" style="font-size:18px;">close</span>
          </button>
        </div>
      </div>
    `;
  }).join('');
}
async function markApplied(jobId) {
  try {
    await fetch(`/api/jobs/${jobId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'applied' })
    });
    alert(currentLang === 'en' ? '✅ Marked as Applied!' : '✅ Oznaczono jako Aplikowane!');
    loadJobs();
  } catch (err) {
    alert('Error marking applied: ' + err.message);
  }
}

async function dismissJob(jobId) {
  if (!confirm(currentLang === 'en' ? 'Remove this job offer from your list?' : 'Usunąć tę ofertę z listy?')) return;
  try {
    await fetch(`/api/jobs/${jobId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'dismissed' })
    });
    loadJobs();
  } catch (err) {
    alert('Error dismissing job: ' + err.message);
  }
}

function helperExtractArray(raw) {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw;
  if (typeof raw === 'object') {
    if (Array.isArray(raw[currentLang])) return raw[currentLang];
    if (Array.isArray(raw.pl)) return raw.pl;
    if (Array.isArray(raw.en)) return raw.en;
    return Object.values(raw).filter(x => typeof x === 'string');
  }
  if (typeof raw === 'string') return [raw];
  return [];
}

function helperExtractText(raw) {
  if (!raw) return '';
  if (typeof raw === 'string') return raw;
  if (typeof raw === 'object') {
    return raw[currentLang] || raw.pl || raw.en || '';
  }
  return String(raw);
}

function renderJobs(jobs) {
  const grid = document.getElementById('jobGrid');
  const isEn = (currentLang === 'en');

  if (!jobs || jobs.length === 0) {
    const emptyText = isEn ? 'No job offers found in this category.' : 'Brak ofert w tej kategorii.';
    grid.innerHTML = `<div style="text-align: center; padding: 40px; color: #94a3b8;">${emptyText}</div>`;
    return;
  }

  grid.innerHTML = jobs.map((job, idx) => {
    const match = job.match || {};
    const score = match.match_score || 85;
    const summaryText = helperExtractText(match.summary);
    const strengthsArray = helperExtractArray(match.strengths);

    const sal = match.salary_estimator || {};
    const estRange = sal.estimated_range || job.salary || '6,500 - 8,500 PLN brutto';

    const isApplied = (job.user_status === 'applied');
    const statusBadge = isApplied ? `<span style="background: rgba(16, 185, 129, 0.2); color: #34d399; padding: 4px 10px; border-radius: 20px; font-weight: 600; font-size: 12px;">✅ Applied</span>` : '';

    const sourceTag = job.source || 'LinkedIn Jobs';

    return `
      <div class="job-card">
        <div class="job-header">
          <div class="job-title-group">
            <div style="display: flex; align-items: center; gap: 10px;">
              <h3>${job.title}</h3>
              <span class="pill" style="background: rgba(59, 130, 246, 0.2); border-color: rgba(59, 130, 246, 0.4); color: #60a5fa; font-weight: 600;">${sourceTag}</span>
              ${statusBadge}
            </div>
            <div class="job-meta">
              <span>🏢 ${job.company}</span>
              <span>📍 ${job.location}</span>
              <span>💼 ${job.work_mode}</span>
              <span style="color: #6ee7b7; font-weight: 600;">💰 ${estRange}</span>
            </div>
          </div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <div class="score-badge">
              ${score}% <span>Match</span>
            </div>
            <button onclick="dismissJob('${job.id}')" title="${isEn ? 'Remove from list' : 'Usuń z listy'}" style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); color: #f87171; padding: 6px 10px; border-radius: 8px; cursor: pointer;">
              ❌
            </button>
          </div>
        </div>

        <div style="font-size: 13.5px; color: #34d399; font-weight: 500; margin-bottom: 8px;">
          ${isEn ? '💡 Why it matches:' : '💡 Dlaczego pasuje:'} ${summaryText}
        </div>

        <div class="job-description">
          ${job.description.trim().substring(0, 300)}...
        </div>

        <div class="job-strengths">
          ${strengthsArray.map(s => `<span class="strength-tag">✓ ${s}</span>`).join('')}
        </div>

        <div class="job-actions">
          <div style="display: flex; gap: 10px;">
            <button class="btn-blurb" onclick="openBlurbModal(${idx})">
              ${isEn ? '📝 AI Cover Package & Salary' : '📝 Paczka AI & Wynagrodzenie'}
            </button>
            ${!isApplied ? `
              <button class="btn-blurb" style="background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.3); color: #34d399;" onclick="markApplied('${job.id}')">
                ✅ ${isEn ? 'Mark as Applied' : 'Oznacz jako Aplikowane'}
              </button>
            ` : ''}
          </div>
          
          <a href="${job.apply_url}" target="_blank" rel="noopener" class="btn-apply" onclick="fetch('/api/jobs/${job.id}/status', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({status:'viewed'})})">
            ${isEn ? '🚀 Apply on Site' : '🚀 Aplikuj na stronie'}
          </a>
        </div>
      </div>
    `;
  }).join('');
}

async function openBlurbModal(index) {
  selectedJobIndex = index;
  const job = currentJobs[index];
  if (!job) return;

  const isEn = (currentLang === 'en');
  const match = job.match || {};
  if(document.getElementById('modalJobTitle')) document.getElementById('modalJobTitle').textContent = `${job.title} — ${job.company}`;

  // Populate Salary Estimator Box
  const sal = match.salary_estimator || {};
  if(document.getElementById('valEstRange')) document.getElementById('valEstRange').textContent = sal.estimated_range || job.salary || '6,500 - 8,500 PLN brutto';
  if(document.getElementById('valRecAsk')) document.getElementById('valRecAsk').textContent = sal.recommended_ask || '7,500 PLN brutto';
  
  const tipText = helperExtractText(sal.negotiation_tip) || (isEn ? 'Highlight C1 English proficiency and international customer experience in Malta/Turkey to justify asking for the higher end of the range.' : 'Znakomity angielski C1 oraz wykształcenie lingwistyczne z Języka Biznesu to Twój kluczowy atut podczas negocjacji.');
  if(document.getElementById('valSalaryTip')) document.getElementById('valSalaryTip').innerHTML = `<strong>💡 ${isEn ? 'Negotiation Tip:' : 'Porada Negocjacyjna:'}</strong> ${tipText}`;

  // On-demand fetch full cover letter
  const blurbBox = document.getElementById('modalBlurbText');
  blurbBox.textContent = isEn ? '⚡ Gemini 3.6 Flash generating full tailored cover letter on demand...' : '⚡ Gemini 3.6 Flash generuje pełny spersonalizowany list motywacyjny...';

  document.getElementById('blurbModal').style.display = 'flex';

  try {
    const res = await fetch(`/api/jobs/${job.id}/cover-letter?lang=${currentLang}`);
    if (res.ok) {
      const data = await res.json();
      blurbBox.textContent = data.cover_letter;
    } else {
      blurbBox.textContent = helperExtractText(match.cover_blurb) || 'Szanowni Państwo...';
    }
  } catch (err) {
    blurbBox.textContent = helperExtractText(match.cover_blurb) || 'Szanowni Państwo...';
  }

  const translatedDescBox = document.getElementById('modalTranslatedDesc');
  translatedDescBox.style.display = 'none';
  translatedDescBox.textContent = match.description_en || job.description;

  const qnaList = document.getElementById('qnaList');
  const qna = match.screening_qna || [];
  
  if (!Array.isArray(qna) || qna.length === 0) {
    qnaList.innerHTML = `<div style="color: #94a3b8; font-size: 13px;">${isEn ? 'No extra recruiter questions.' : 'Brak dodatkowych pytań rekrutera.'}</div>`;
  } else {
    qnaList.innerHTML = qna.map(item => {
      const q = isEn ? (item.question_en || item.question_pl || item.question) : (item.question_pl || item.question);
      const a = isEn ? (item.answer_en || item.answer_pl || item.answer) : (item.answer_pl || item.answer);
      return `
        <div class="qna-item">
          <div class="qna-q">Q: ${q}</div>
          <div class="qna-a">A: ${a}</div>
        </div>
      `;
    }).join('');
  }
}

function downloadZipPackage() {
  if (selectedJobIndex === null || !currentJobs[selectedJobIndex]) return;
  const job = currentJobs[selectedJobIndex];
  const includeCv = document.getElementById('chkIncludeCv').checked;
  window.location.href = `/api/download-package/${job.id}?include_cv=${includeCv}&lang=${currentLang}`;
}

function toggleTranslatedDesc() {
  const descBox = document.getElementById('modalTranslatedDesc');
  if (descBox.style.display === 'none') {
    descBox.style.display = 'block';
  } else {
    descBox.style.display = 'none';
  }
}

function copyBlurb() {
  const text = document.getElementById('modalBlurbText') ? document.getElementById('modalBlurbText').textContent : '';
  navigator.clipboard.writeText(text).then(() => {
    alert(currentLang === 'en' ? '✅ Cover message copied to clipboard!' : '✅ Treść wiadomości skopiowana do schowka!');
  });
}

function closeModal(modalId) {
  document.getElementById(modalId).style.display = 'none';
}

function openCustomJobModal() {
  document.getElementById('customJobModal').style.display = 'flex';
}

async function submitCustomJob(e) {
  e.preventDefault();
  const title = document.getElementById('customTitle').value;
  const company = document.getElementById('customCompany').value;
  const location = document.getElementById('customLocation').value;
  const description = document.getElementById('customDesc').value;

  closeModal('customJobModal');
  const grid = document.getElementById('jobGrid');
  const isEn = (currentLang === 'en');
  
  let progress = 15;
  grid.innerHTML = renderProgressBar(
    progress,
    isEn ? '⚡ Gemini 3.6 Flash analyzing custom job offer...' : '⚡ Gemini 3.6 Flash analizuje ogłoszenie...',
    isEn ? 'Calculating match score & salary range' : 'Wyliczanie dopasowania i widełek wynagrodzenia'
  );

  try {
    const res = await fetch('/api/generate-blurb', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        company,
        location,
        work_mode: 'Hybrid',
        description
      })
    });
    const data = await res.json();
    const newJob = {
      id: 'custom-' + Date.now(),
      title,
      company,
      location,
      work_mode: 'Hybrid',
      description,
      apply_url: '#',
      source: 'Custom Entry',
      match: data.match
    };
    currentJobs.unshift(newJob);
    renderJobs(currentJobs);
    openBlurbModal(0);
  } catch (err) {
    alert((isEn ? 'Analysis error: ' : 'Błąd analizy: ') + err.message);
    loadJobs();
  }
}
