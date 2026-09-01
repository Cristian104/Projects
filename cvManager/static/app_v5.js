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

  loadProfile();
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
    const isEn = (currentLang === 'en');

    if(document.getElementById('profileName')) document.getElementById('profileName').textContent = profile.name || 'Kamila Drewniak';
    
    if(document.getElementById('profileHeadline')) {
      document.getElementById('profileHeadline').textContent = isEn 
        ? 'Experienced Customer Service Specialist (PL/EN C1), Tour Resident & Team Manager.'
        : (profile.headline || 'Doświadczona specjalistka ds. obsługi klienta (PL/EN C1), rezydentka turystyczna oraz kierownik zespołu.');
    }
    
    if (profile.skills) {
      const pillsContainer = document.getElementById('profilePills');
      const skillsPl = ['Obsługa klienta', 'Zarządzanie zespołem', 'Szkolenie pracowników', 'Grafiki pracy', 'Procedury KYC'];
      const skillsEn = ['Customer Service', 'Team Management', 'Staff Training', 'Scheduling', 'KYC Compliance'];
      
      const skillsToUse = isEn ? skillsEn : skillsPl;
      
      pillsContainer.innerHTML = skillsToUse.map(s => `<span class="pill">✨ ${s}</span>`).join('') +
        `<span class="pill">🇬🇧 ${isEn ? 'English (C1)' : 'Angielski (C1)'}</span>` +
        `<span class="pill">📍 Częstochowa, ${isEn ? 'Poland' : 'Polska'}</span>`;
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
    if (summaryText.length > 140) summaryText = summaryText.substring(0, 140) + '...';
    
    let strengthsArray = helperExtractArray(match.strengths);
    if (strengthsArray.length > 3) strengthsArray = strengthsArray.slice(0, 3);

    const sal = match.salary_estimator || {};
    const estRange = sal.estimated_range || job.salary || '6,5k - 8,5k PLN';

    const isApplied = (job.user_status === 'applied');
    const jobUrl = job.url || '#';

    return `
      <div class="job-card" style="padding: 20px; background: rgba(28, 28, 30, 0.75); backdrop-filter: blur(30px); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; margin-bottom: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; gap: 12px; flex-wrap: wrap;">
          <div style="flex: 1; min-width: 180px;">
            <h3 style="font-size: 17px; font-weight: 700; color: #e5e2e1; margin-bottom: 6px; line-height: 1.3;">${job.title}</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font-size: 12px; color: #A1A1AA;">
              <span style="display:flex; align-items:center; gap:4px;"><span class="material-symbols-outlined" style="font-size:14px;">business</span> ${job.company}</span>
              <span style="display:flex; align-items:center; gap:4px;"><span class="material-symbols-outlined" style="font-size:14px;">location_on</span> ${job.location}</span>
              <span style="color: #34d399; font-weight: 600;">💰 ${estRange}</span>
              ${isApplied ? `<span class="pill" style="background: rgba(16,185,129,0.15); color: #34d399; font-weight: 700; font-size:10px; padding: 2px 6px; border-radius: 4px;">APPLIED</span>` : ''}
            </div>
          </div>
          <div class="score-badge" style="flex-shrink: 0; background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); color: #60a5fa; font-weight: 700; padding: 4px 10px; border-radius: 20px; font-size: 13px;">
            ⚡ ${score}% Match
          </div>
        </div>

        <div style="font-size: 13px; color: #34d399; font-weight: 500; margin-bottom: 12px; line-height: 1.4; background: rgba(52, 211, 153, 0.05); padding: 8px 12px; border-radius: 8px; border-left: 3px solid #34d399;">
          💡 <strong>${isEn ? 'Why it matches:' : 'Dlaczego pasuje:'}</strong> ${summaryText}
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px;">
          ${strengthsArray.map(s => `<span class="strength-tag" style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #d1d5db; font-size: 11px; padding: 3px 8px; border-radius: 6px;"> ${s}</span>`).join('')}
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 10px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px; align-items: center;">
          <button class="btn-apply" onclick="openBlurbModal(${idx})" style="flex: 1; min-width: 140px; padding: 10px 14px; font-size: 13px; border-radius: 10px; background: rgba(10, 132, 255, 0.2); border: 1px solid rgba(10, 132, 255, 0.4); color: #60a5fa; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px;">
            📝 ${isEn ? 'AI Cover Package' : 'Paczka AI & Wynagrodzenie'}
          </button>
          
          <a href="${jobUrl}" target="_blank" class="btn-apply" style="padding: 10px 14px; font-size: 13px; border-radius: 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15); color: #e5e2e1; text-decoration: none; display: flex; align-items: center; gap: 6px;">
            🚀 ${isEn ? 'Apply on Site' : 'Aplikuj na stronie'}
          </a>

          ${!isApplied ? `
            <button class="btn-apply" style="padding: 10px 12px; border-radius: 10px; background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); color: #34d399; cursor: pointer;" onclick="markApplied('${job.id}')" title="${isEn ? 'Mark Applied' : 'Oznacz jako aplikowane'}">
              ✅
            </button>
          ` : ''}
          
          <button class="btn-apply" style="padding: 10px 12px; border-radius: 10px; background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.3); color: #f87171; cursor: pointer;" onclick="dismissJob('${job.id}')" title="${isEn ? 'Dismiss' : 'Odrzuć'}">
            ❌
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
    grid.innerHTML = `<div style="text-align: center; padding: 40px; color: #94a3b8; font-weight:500;">${emptyText}</div>`;
    return;
  }

  grid.innerHTML = jobs.map((job, idx) => {
    const match = job.match || {};
    const score = match.match_score || 85;
    
    let summaryText = helperExtractText(match.summary);
    if (summaryText.length > 140) summaryText = summaryText.substring(0, 140) + '...';
    
    let strengthsArray = helperExtractArray(match.strengths);
    if (strengthsArray.length > 3) strengthsArray = strengthsArray.slice(0, 3);

    const sal = match.salary_estimator || {};
    const estRange = sal.estimated_range || job.salary || '6,5k - 8,5k PLN';

    const isApplied = (job.user_status === 'applied');
    const jobUrl = job.url || '#';

    return `
      <div class="job-card" style="padding: 20px; background: rgba(28, 28, 30, 0.75); backdrop-filter: blur(30px); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; margin-bottom: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; gap: 12px; flex-wrap: wrap;">
          <div style="flex: 1; min-width: 180px;">
            <h3 style="font-size: 17px; font-weight: 700; color: #e5e2e1; margin-bottom: 6px; line-height: 1.3;">${job.title}</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font-size: 12px; color: #A1A1AA;">
              <span style="display:flex; align-items:center; gap:4px;"><span class="material-symbols-outlined" style="font-size:14px;">business</span> ${job.company}</span>
              <span style="display:flex; align-items:center; gap:4px;"><span class="material-symbols-outlined" style="font-size:14px;">location_on</span> ${job.location}</span>
              <span style="color: #34d399; font-weight: 600;">💰 ${estRange}</span>
              ${isApplied ? `<span class="pill" style="background: rgba(16,185,129,0.15); color: #34d399; font-weight: 700; font-size:10px; padding: 2px 6px; border-radius: 4px;">APPLIED</span>` : ''}
            </div>
          </div>
          <div class="score-badge" style="flex-shrink: 0; background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); color: #60a5fa; font-weight: 700; padding: 4px 10px; border-radius: 20px; font-size: 13px;">
            ⚡ ${score}% Match
          </div>
        </div>

        <div style="font-size: 13px; color: #34d399; font-weight: 500; margin-bottom: 12px; line-height: 1.4; background: rgba(52, 211, 153, 0.05); padding: 8px 12px; border-radius: 8px; border-left: 3px solid #34d399;">
          💡 <strong>${isEn ? 'Why it matches:' : 'Dlaczego pasuje:'}</strong> ${summaryText}
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px;">
          ${strengthsArray.map(s => `<span class="strength-tag" style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #d1d5db; font-size: 11px; padding: 3px 8px; border-radius: 6px;"> ${s}</span>`).join('')}
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 10px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px; align-items: center;">
          <button class="btn-apply" onclick="openBlurbModal(${idx})" style="flex: 1; min-width: 140px; padding: 10px 14px; font-size: 13px; border-radius: 10px; background: rgba(10, 132, 255, 0.2); border: 1px solid rgba(10, 132, 255, 0.4); color: #60a5fa; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px;">
            📝 ${isEn ? 'AI Cover Package' : 'Paczka AI & Wynagrodzenie'}
          </button>
          
          <a href="${jobUrl}" target="_blank" class="btn-apply" style="padding: 10px 14px; font-size: 13px; border-radius: 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15); color: #e5e2e1; text-decoration: none; display: flex; align-items: center; gap: 6px;">
            🚀 ${isEn ? 'Apply on Site' : 'Aplikuj na stronie'}
          </a>

          ${!isApplied ? `
            <button class="btn-apply" style="padding: 10px 12px; border-radius: 10px; background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); color: #34d399; cursor: pointer;" onclick="markApplied('${job.id}')" title="${isEn ? 'Mark Applied' : 'Oznacz jako aplikowane'}">
              ✅
            </button>
          ` : ''}
          
          <button class="btn-apply" style="padding: 10px 12px; border-radius: 10px; background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.3); color: #f87171; cursor: pointer;" onclick="dismissJob('${job.id}')" title="${isEn ? 'Dismiss' : 'Odrzuć'}">
            ❌
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
    grid.innerHTML = `<div style="text-align: center; padding: 40px; color: #94a3b8; font-weight:500;">${emptyText}</div>`;
    return;
  }

  grid.innerHTML = jobs.map((job, idx) => {
    const match = job.match || {};
    const score = match.match_score || 85;
    
    let summaryText = helperExtractText(match.summary);
    if (summaryText.length > 140) summaryText = summaryText.substring(0, 140) + '...';
    
    let strengthsArray = helperExtractArray(match.strengths);
    if (strengthsArray.length > 3) strengthsArray = strengthsArray.slice(0, 3);

    const sal = match.salary_estimator || {};
    const estRange = sal.estimated_range || job.salary || '6,5k - 8,5k PLN';

    const isApplied = (job.user_status === 'applied');
    const jobUrl = job.url || '#';

    return `
      <div class="job-card" style="padding: 20px; background: rgba(28, 28, 30, 0.75); backdrop-filter: blur(30px); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; margin-bottom: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; gap: 12px; flex-wrap: wrap;">
          <div style="flex: 1; min-width: 180px;">
            <h3 style="font-size: 17px; font-weight: 700; color: #e5e2e1; margin-bottom: 6px; line-height: 1.3;">${job.title}</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font-size: 12px; color: #A1A1AA;">
              <span style="display:flex; align-items:center; gap:4px;"><span class="material-symbols-outlined" style="font-size:14px;">business</span> ${job.company}</span>
              <span style="display:flex; align-items:center; gap:4px;"><span class="material-symbols-outlined" style="font-size:14px;">location_on</span> ${job.location}</span>
              <span style="color: #34d399; font-weight: 600;">💰 ${estRange}</span>
              ${isApplied ? `<span class="pill" style="background: rgba(16,185,129,0.15); color: #34d399; font-weight: 700; font-size:10px; padding: 2px 6px; border-radius: 4px;">APPLIED</span>` : ''}
            </div>
          </div>
          <div class="score-badge" style="flex-shrink: 0; background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); color: #60a5fa; font-weight: 700; padding: 4px 10px; border-radius: 20px; font-size: 13px;">
            ⚡ ${score}% Match
          </div>
        </div>

        <div style="font-size: 13px; color: #34d399; font-weight: 500; margin-bottom: 12px; line-height: 1.4; background: rgba(52, 211, 153, 0.05); padding: 8px 12px; border-radius: 8px; border-left: 3px solid #34d399;">
          💡 <strong>${isEn ? 'Why it matches:' : 'Dlaczego pasuje:'}</strong> ${summaryText}
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px;">
          ${strengthsArray.map(s => `<span class="strength-tag" style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #d1d5db; font-size: 11px; padding: 3px 8px; border-radius: 6px;"> ${s}</span>`).join('')}
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 10px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px; align-items: center;">
          <button class="btn-apply" onclick="openBlurbModal(${idx})" style="flex: 1; min-width: 140px; padding: 10px 14px; font-size: 13px; border-radius: 10px; background: rgba(10, 132, 255, 0.2); border: 1px solid rgba(10, 132, 255, 0.4); color: #60a5fa; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px;">
            📝 ${isEn ? 'AI Cover Package' : 'Paczka AI & Wynagrodzenie'}
          </button>
          
          <a href="${jobUrl}" target="_blank" class="btn-apply" style="padding: 10px 14px; font-size: 13px; border-radius: 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15); color: #e5e2e1; text-decoration: none; display: flex; align-items: center; gap: 6px;">
            🚀 ${isEn ? 'Apply on Site' : 'Aplikuj na stronie'}
          </a>

          ${!isApplied ? `
            <button class="btn-apply" style="padding: 10px 12px; border-radius: 10px; background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); color: #34d399; cursor: pointer;" onclick="markApplied('${job.id}')" title="${isEn ? 'Mark Applied' : 'Oznacz jako aplikowane'}">
              ✅
            </button>
          ` : ''}
          
          <button class="btn-apply" style="padding: 10px 12px; border-radius: 10px; background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.3); color: #f87171; cursor: pointer;" onclick="dismissJob('${job.id}')" title="${isEn ? 'Dismiss' : 'Odrzuć'}">
            ❌
          </button>
        </div>
      </div>
    `;
  }).join('');
}