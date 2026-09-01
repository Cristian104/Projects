import os

# Let's read app_v5.js
with open('static/app_v5.js', 'r', encoding='utf-8') as f:
    js_code = f.read()

# Restore modal functions if missing
modal_functions = """
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

  // On-demand fetch full cover letter
  const blurbBox = document.getElementById('modalBlurbText');
  if (blurbBox) {
    blurbBox.textContent = isEn ? '⚡ Gemini 3.6 Flash generating full tailored cover letter on demand...' : '⚡ Gemini 3.6 Flash generuje pełny spersonalizowany list motywacyjny...';
  }

  if (document.getElementById('blurbModal')) {
    document.getElementById('blurbModal').style.display = 'flex';
  }

  try {
    const res = await fetch(`/api/jobs/${job.id}/cover-letter?lang=${currentLang}`);
    if (res.ok) {
      const data = await res.json();
      if (blurbBox) blurbBox.textContent = data.cover_letter;
    } else {
      if (blurbBox) blurbBox.textContent = helperExtractText(match.cover_blurb) || 'Szanowni Państwo...';
    }
  } catch (err) {
    if (blurbBox) blurbBox.textContent = helperExtractText(match.cover_blurb) || 'Szanowni Państwo...';
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

if 'openBlurbModal' not in js_code:
    js_code += '\n\n' + modal_functions

# Update renderJobs to keep full text in DOM for Web, but use responsive CSS class for Mobile!
# And fix apply_url!
new_renderJobs = """function renderJobs(jobs) {
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
    const jobUrl = job.apply_url || job.url || '#';
    const sourceTag = job.source || 'LinkedIn';

    return `
      <div class="job-card">
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
          <div class="score-badge">
            ⚡ ${score}% Match
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
}"""

import re
js_code = re.sub(r'function renderJobs\(jobs\) \{[\s\S]*?(?=async function markApplied)', new_renderJobs + '\n\n', js_code)

with open('static/app_v5.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(js_code)

print("Updated app_v5.js successfully!")
