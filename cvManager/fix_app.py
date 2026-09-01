import re
import os

with open('static/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix setLanguage to be robust against missing IDs
content = re.sub(r"document\.getElementById\('([^']+)'\)\.textContent", r"if(document.getElementById('\1')) document.getElementById('\1').textContent", content)
content = re.sub(r"document\.getElementById\('([^']+)'\)\.innerHTML", r"if(document.getElementById('\1')) document.getElementById('\1').innerHTML", content)
content = re.sub(r"document\.getElementById\('([^']+)'\)\.classList", r"if(document.getElementById('\1')) document.getElementById('\1').classList", content)

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
    let summaryText = helperExtractText(match.summary);
    if(summaryText.length > 120) summaryText = summaryText.substring(0, 120) + '...';
    
    let strengthsArray = helperExtractArray(match.strengths);
    if(strengthsArray.length > 4) strengthsArray = strengthsArray.slice(0, 4);

    const sal = match.salary_estimator || {};
    const estRange = sal.estimated_range || job.salary || '6,5k - 8,5k PLN';

    const isApplied = (job.user_status === 'applied');
    const sourceTag = job.source || 'LinkedIn';

    return `
      <div class="job-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; gap: 12px;">
          <div style="flex: 1; min-width: 0;">
            <h3 style="font-size: 18px; font-weight: 600; color: #e5e2e1; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${job.title}</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 6px; align-items: center;">
              <span style="font-size: 13px; color: #A1A1AA; display:flex; align-items:center; gap:4px;"><span class="material-symbols-outlined" style="font-size:14px;">business</span> ${job.company}</span>
              ${isApplied ? `<span class="pill" style="background: rgba(16,185,129,0.15); color: #34d399; font-weight: 700; font-size:11px; padding: 2px 8px;">APPLIED</span>` : ''}
            </div>
          </div>
          <div class="score-badge">
            <span class="material-symbols-outlined" style="font-size:14px;">bolt</span> ${score}%
          </div>
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px;">
          ${strengthsArray.map(s => `<span class="strength-tag">${s}</span>`).join('')}
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 12px; margin-top: auto; padding-top: 16px;">
          <button class="btn-apply" onclick="openBlurbModal(${idx})">
            <span class="material-symbols-outlined" style="font-size:18px;">analytics</span> ${isEn ? 'Analyze' : 'Analiza'}
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
"""

content = re.sub(r'function renderJobs\(jobs\) \{[\s\S]*?(?=function markApplied)', new_renderJobs, content)

with open('static/app.js', 'w', encoding='utf-8') as f:
    f.write(content)
