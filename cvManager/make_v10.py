import os

app_code = """let currentJobs = [];
let currentLang = localStorage.getItem('cvManager_lang') || 'pl';
let currentScope = 'all';
let currentWorkMode = 'all';
let currentStatusFilter = 'active';
let selectedJobIndex = null;

document.addEventListener('DOMContentLoaded', () => {
  setLanguage(currentLang, false);
  loadProfile();
  fetchSearchStatus();
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
  if(document.getElementById('btnClearExpired')) document.getElementById('btnClearExpired').innerHTML = isEn ? '<span>🧹 Clear Expired & Fetch New</span>' : '<span>🧹 Wyczyść wygasłe & Szukaj nowych</span>';
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
  if(document.getElementById('btnGenerateCover')) document.getElementById('btnGenerateCover').textContent = isEn ? '⚡ Generate Cover Letter with AI' : '⚡ Wygeneruj List Motywacyjny z AI';

  loadProfile();
  fetchSearchStatus();

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

async function fetchSearchStatus() {
  const badge = document.getElementById('lastSearchBadge');
  if (!badge) return;
  const isEn = (currentLang === 'en');
  try {
    const res = await fetch('/api/search-status');
    if (!res.ok) return;
    const data = await res.json();
    if (data.last_searched) {
      const dt = new Date(data.last_searched);
      const formatted = dt.toLocaleString(isEn ? 'en-US' : 'pl-PL', { dateStyle: 'short', timeStyle: 'short' });
      badge.textContent = isEn ? `Last searched: ${formatted}` : `Ostatnie wyszukiwanie: ${formatted}`;
    } else {
      badge.textContent = isEn ? 'Last searched: Recently' : 'Ostatnie wyszukiwanie: Niedawno';
    }
  } catch (err) {
    badge.textContent = '';
  }
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
    const url = `/api/jobs?scope=${currentScope}&work_mode=${currentWorkMode}&status_filter=${currentStatusFilter}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    currentJobs = Array.isArray(data) ? data : (data.jobs || []);
    renderJobs(currentJobs);
    
    // Background verify first 5 jobs
    currentJobs.slice(0, 5).forEach((j, i) => {
      if (j.user_status !== 'dismissed') verifyJobAvailability(i);
    });
  } catch (err) {
    console.error('Failed to load jobs:', err);
    grid.innerHTML = `<div style="text-align: center; padding: 40px; color: #ef4444;">${isEn ? 'Failed to load jobs.' : 'Błąd ładowania ofert.'}</div>`;
  }
}

function renderProgressBar(percentage, statusText, subText) {
  return `
    <div style="padding: 30px; background: rgba(28, 28, 30, 0.75); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; margin: 20px 0;">
      <div style="display: flex; justify-content: space-between; margin-bottom: 10px; font-weight: 600; font-size: 14px; color: #e5e2e1;">
        <span>${statusText}</span>
        <span style="color: #60a5fa;">${percentage}%</span>
      </div>
      <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; margin-bottom: 12px;">
        <div style="width: ${percentage}%; height: 100%; background: linear-gradient(90deg, #3b82f6, #10b981); transition: width 0.3s ease;"></div>
      </div>
      <div style="font-size: 12px; color: #94a3b8;">${subText}</div>
    </div>
  `;
}

async function extendSearch() {
  const grid = document.getElementById('jobGrid');
  const isEn = (currentLang === 'en');
  
  let progress = 15;
  grid.innerHTML = renderProgressBar(
    progress,
    isEn ? '🔍 Searching live job listings across Poland...' : '🔍 Przeszukiwanie najnowszych ofert pracy w Polsce...',
    isEn ? 'Fetching LinkedIn, Pracuj.pl, NoFluffJobs & JustJoin.it' : 'Pobieranie z LinkedIn, Pracuj.pl, NoFluffJobs i JustJoin.it'
  );

  const progressInterval = setInterval(() => {
    if (progress < 90) {
      progress += Math.floor(Math.random() * 12) + 5;
      let msg = isEn ? '🔍 Fetching live listings...' : '🔍 Pobieranie najnowszych ofert...';
      let sub = isEn ? 'Scanning Frequent keywords...' : 'Skanowanie słów kluczowych...';

      if (progress > 30 && progress <= 60) {
        msg = isEn ? '⚡ Evaluating candidate match scores with Gemini 3.6 Flash AI...' : '⚡ Ocena dopasowania kandydata z Gemini 3.6 Flash AI...';
        sub = isEn ? 'Comparing C1 Business English & Malta/Turkey experience' : 'Porównywanie języka C1 i doświadczenia z Malty i Turcji';
      } else if (progress > 60) {
        msg = isEn ? '💰 Estimating market salary ranges for Poland...' : '💰 Szacowanie rynkowych widełek wynagrodzeń...';
        sub = isEn ? 'Calculating target asks and negotiation advice' : 'Wyliczanie stawek dla Częstochowy i Polski';
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
      isEn ? '✅ Done! Fresh active listings updated!' : '✅ Gotowe! Zaktualizowano aktywne oferty!',
      isEn ? `Successfully evaluated ${data.count} job listings` : `Pomyślnie oceniono ${data.count} ofert pracy`
    );

    fetchSearchStatus();

    setTimeout(() => {
      loadJobs();
    }, 500);
  } catch (err) {
    clearInterval(progressInterval);
    alert('Error extending search: ' + err.message);
    loadJobs();
  }
}

async function clearExpiredAndRefresh() {
  const grid = document.getElementById('jobGrid');
  const isEn = (currentLang === 'en');

  grid.innerHTML = renderProgressBar(
    30,
    isEn ? '🧹 Clearing expired job listings & fetching new active offers...' : '🧹 Usuwanie wygasłych ofert i pobieranie nowych...',
    isEn ? 'Verifying 404 links & fetching fresh listings' : 'Weryfikacja wygasłych linków i szukanie nowych'
  );

  try {
    const res = await fetch('/api/jobs/clear-expired', { method: 'POST' });
    const data = await res.json();
    grid.innerHTML = renderProgressBar(
      100,
      isEn ? '✅ Cleaned & Updated!' : '✅ Oczyszczono i zaktualizowano!',
      isEn ? `Removed ${data.dismissed_count} expired listings. ${data.count} active offers available.` : `Usunięto ${data.dismissed_count} wygasłych ofert. Dostępnych ${data.count} aktywnych ofert.`
    );
    fetchSearchStatus();
    setTimeout(() => {
      loadJobs();
    }, 600);
  } catch (err) {
    alert('Error clearing expired: ' + err.message);
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

async function verifyJobAvailability(index, btnElem) {
  const job = currentJobs[index];
  if (!job) return;
  const isEn = (currentLang === 'en');
  if (btnElem) btnElem.textContent = isEn ? '⏳ Verifying...' : '⏳ Sprawdzanie...';
  
  try {
    const res = await fetch(`/api/jobs/${job.id}/verify`);
    const data = await res.json();
    job.is_expired = !data.active;
    
    const cardElem = document.getElementById(`job-card-${job.id}`);
    
    if (data.active) {
      if (btnElem) {
        btnElem.innerHTML = '✅ Active';
        btnElem.style.borderColor = 'rgba(52, 211, 153, 0.4)';
        btnElem.style.color = '#34d399';
      }
      if (cardElem) cardElem.classList.remove('card-expired');
    } else {
      if (btnElem) {
        btnElem.innerHTML = '❌ Expired';
        btnElem.style.borderColor = 'rgba(239, 68, 68, 0.4)';
        btnElem.style.color = '#f87171';
      }
      if (cardElem) cardElem.classList.add('card-expired');
    }
  } catch (err) {
    if (btnElem) btnElem.textContent = isEn ? '⚠️ Unavailable' : '⚠️ Niedostępny';
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
    
    const summaryText = helperExtractText(match.summary);
    const strengthsArray = helperExtractArray(match.strengths);

    const sal = match.salary_estimator || {};
    const estRange = sal.estimated_range || job.salary || '6,5k - 8,5k PLN';

    const isApplied = (job.user_status === 'applied');
    const isExpired = job.is_expired || false;
    const rawUrl = job.apply_url || job.url || '';
    const jobUrl = (rawUrl && rawUrl !== '#') ? rawUrl : `https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(job.title)}`;

    return `
      <div class="job-card ${isExpired ? 'card-expired' : ''}" id="job-card-${job.id}">
        <div class="job-card-header">
          <div style="flex: 1; min-width: 180px;">
            <h3 class="job-card-title">${job.title}</h3>
            <div class="job-card-meta">
              <span>🏢 ${job.company}</span>
              <span>📍 ${job.location}</span>
              <span style="color: #34d399; font-weight: 600;">💰 ${estRange}</span>
              ${isApplied ? `<span class="pill pill-applied">APPLIED</span>` : ''}
            </div>
          </div>
          <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
            <div class="score-badge">
              ⚡ ${score}% Match
            </div>
            <button class="btn-action-icon" style="font-size: 11px; padding: 3px 8px; border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.03); color: #a1a1aa; border-radius: 6px; cursor: pointer;" onclick="verifyJobAvailability(${idx}, this)">
              ${isExpired ? '❌ Expired' : `🔍 ${isEn ? 'Verify' : 'Sprawdź ważność'}`}
            </button>
          </div>
        </div>

        <div class="job-why-matches">
          💡 <strong>${isEn ? 'Why it matches:' : 'Dlaczego pasuje:'}</strong> <span class="summary-text">${summaryText}</span>
        </div>

        <div class="job-strengths-list">
          ${strengthsArray.map(s => `<span class="strength-tag">✓ ${s}</span>`).join('')}
        </div>

        <div class="job-card-actions">
          <button class="btn-action-primary" onclick="openBlurbModal(${idx})">
            📝 <span>${isEn ? 'AI Cover Package' : 'Paczka AI & Wynagrodzenie'}</span>
          </button>
          
          <a href="${jobUrl}" target="_blank" rel="noopener" class="btn-action-secondary">
            🚀 <span>${isEn ? 'Apply on Site' : 'Aplikuj'}</span>
          </a>

          ${!isApplied ? `
            <button class="btn-action-icon btn-action-check" onclick="markApplied('${job.id}')" title="${isEn ? 'Mark Applied' : 'Oznacz jako aplikowane'}">
              ✅
            </button>
          ` : ''}
          
          <button class="btn-action-icon btn-action-dismiss" onclick="dismissJob('${job.id}')" title="${isEn ? 'Dismiss' : 'Odrzuć'}">
            ❌
          </button>
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
  if (document.getElementById('modalJobTitle')) {
    document.getElementById('modalJobTitle').textContent = `${job.title} — ${job.company}`;
  }

  // Populate Salary Estimator Box
  const sal = match.salary_estimator || {};
  if (document.getElementById('valEstRange')) {
    document.getElementById('valEstRange').textContent = sal.estimated_range || job.salary || '6,500 - 8,500 PLN brutto';
  }
  if (document.getElementById('valRecAsk')) {
    document.getElementById('valRecAsk').textContent = sal.recommended_ask || '7,500 PLN brutto';
  }
  
  const tipText = helperExtractText(sal.negotiation_tip) || (isEn ? 'Highlight C1 English proficiency and international customer experience in Malta/Turkey to justify asking for the higher end of the range.' : 'Znakomity angielski C1 oraz wykształcenie lingwistyczne z Języka Biznesu to Twój kluczowy atut podczas negocjacji.');
  if (document.getElementById('valSalaryTip')) {
    document.getElementById('valSalaryTip').innerHTML = `<strong>💡 ${isEn ? 'Negotiation Tip:' : 'Porada Negocjacyjna:'}</strong> ${tipText}`;
  }

  const blurbBox = document.getElementById('modalBlurbText');
  const btnGen = document.getElementById('btnGenerateCover');
  
  // Check if cover letter already exists in cached job object or saved_cover_letters
  const savedLetters = job.saved_cover_letters || {};
  if (savedLetters[currentLang]) {
    if (blurbBox) blurbBox.textContent = savedLetters[currentLang];
    if (btnGen) btnGen.textContent = isEn ? '⚡ Regenerate Cover Letter' : '⚡ Wygeneruj Ponownie List Motywacyjny';
  } else if (match.cover_blurb && helperExtractText(match.cover_blurb)) {
    if (blurbBox) blurbBox.textContent = helperExtractText(match.cover_blurb);
    if (btnGen) btnGen.textContent = isEn ? '⚡ Generate Full Cover Letter' : '⚡ Wygeneruj Pełny List Motywacyjny';
  } else {
    if (blurbBox) blurbBox.textContent = isEn ? 'Click the button below to generate a tailored cover letter with AI.' : 'Kliknij przycisk poniżej, aby wygenerować spersonalizowany list motywacyjny z AI.';
    if (btnGen) btnGen.textContent = isEn ? '⚡ Generate Cover Letter with AI' : '⚡ Wygeneruj List Motywacyjny z AI';
  }

  if (document.getElementById('blurbModal')) {
    document.getElementById('blurbModal').style.display = 'flex';
  }

  const translatedDescBox = document.getElementById('modalTranslatedDesc');
  if (translatedDescBox) {
    translatedDescBox.style.display = 'none';
    translatedDescBox.textContent = match.description_en || job.description;
  }

  const qnaList = document.getElementById('qnaList');
  if (qnaList) {
    const qna = match.screening_qna || [];
    if (!Array.isArray(qna) || qna.length === 0) {
      qnaList.innerHTML = `<div style="color: #94a3b8; font-size: 13px;">${isEn ? 'No extra recruiter questions.' : 'Brak dodatkowych pytań rekrutera.'}</div>`;
    } else {
      qnaList.innerHTML = qna.map(item => {
        const q = isEn ? (item.question_en || item.question_pl || item.question) : (item.question_pl || item.question);
        const a = isEn ? (item.answer_en || item.answer_pl || item.answer) : (item.answer_pl || item.answer);
        return `
          <div class="qna-item" style="margin-bottom: 12px; padding: 10px; background: rgba(255,255,255,0.03); border-radius: 8px;">
            <div class="qna-q" style="font-weight: 600; color: #60a5fa; margin-bottom: 4px;">Q: ${q}</div>
            <div class="qna-a" style="color: #e5e2e1; font-size: 13px;">A: ${a}</div>
          </div>
        `;
      }).join('');
    }
  }
}

async function generateCoverLetterAction() {
  if (selectedJobIndex === null || !currentJobs[selectedJobIndex]) return;
  const job = currentJobs[selectedJobIndex];
  const isEn = (currentLang === 'en');
  const blurbBox = document.getElementById('modalBlurbText');
  const btnGen = document.getElementById('btnGenerateCover');

  if (blurbBox) blurbBox.textContent = isEn ? '⚡ Gemini 3.6 Flash generating full tailored cover letter...' : '⚡ Gemini 3.6 Flash generuje pełny list motywacyjny...';
  if (btnGen) btnGen.disabled = true;

  try {
    const res = await fetch(`/api/jobs/${job.id}/cover-letter?lang=${currentLang}&force=true`);
    if (res.ok) {
      const data = await res.json();
      if (blurbBox) blurbBox.textContent = data.cover_letter;
      if (!job.saved_cover_letters) job.saved_cover_letters = {};
      job.saved_cover_letters[currentLang] = data.cover_letter;
    } else {
      alert(isEn ? 'Error generating cover letter.' : 'Błąd generowania listu motywacyjnego.');
    }
  } catch (err) {
    alert((isEn ? 'Network error: ' : 'Błąd sieci: ') + err.message);
  } finally {
    if (btnGen) {
      btnGen.disabled = false;
      btnGen.textContent = isEn ? '⚡ Regenerate Cover Letter' : '⚡ Wygeneruj Ponownie List Motywacyjny';
    }
  }
}

function downloadZipPackage() {
  if (selectedJobIndex === null || !currentJobs[selectedJobIndex]) return;
  const job = currentJobs[selectedJobIndex];
  const chk = document.getElementById('chkIncludeCv');
  const includeCv = chk ? chk.checked : true;
  window.location.href = `/api/download-package/${job.id}?include_cv=${includeCv}&lang=${currentLang}`;
}

function toggleTranslatedDesc() {
  const descBox = document.getElementById('modalTranslatedDesc');
  if (descBox) {
    descBox.style.display = (descBox.style.display === 'none') ? 'block' : 'none';
  }
}

function copyBlurb() {
  const elem = document.getElementById('modalBlurbText');
  const text = elem ? elem.textContent : '';
  navigator.clipboard.writeText(text).then(() => {
    alert(currentLang === 'en' ? '✅ Cover message copied to clipboard!' : '✅ Treść wiadomości skopiowana do schowka!');
  });
}

function closeModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.style.display = 'none';
}

function openCustomJobModal() {
  const m = document.getElementById('customJobModal');
  if (m) m.style.display = 'flex';
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
  
  grid.innerHTML = `<div style="text-align: center; padding: 40px; color: #94a3b8;">${isEn ? '⚡ Gemini 3.6 Flash analyzing custom job offer...' : '⚡ Gemini 3.6 Flash analizuje ogłoszenie...'}</div>`;

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
"""

with open('static/app_v10.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(app_code)

print("Generated clean app_v10.js!")
