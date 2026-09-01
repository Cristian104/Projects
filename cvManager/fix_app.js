const fs = require('fs');
let code = fs.readFileSync('static/app.js', 'utf8');

const startIdx = code.indexOf('function renderJobs(jobs)');
const endIdx = code.indexOf('async function markApplied');

if (startIdx !== -1 && endIdx !== -1) {
    const newRenderJobs = `function renderJobs(jobs) {
  const grid = document.getElementById('jobGrid');
  const isEn = (currentLang === 'en');

  if (!jobs || jobs.length === 0) {
    const emptyText = isEn ? 'No job offers found in this category.' : 'Brak ofert w tej kategorii.';
    grid.innerHTML = \`<div style="text-align: center; padding: 40px; color: #94a3b8; font-weight:500;">\${emptyText}</div>\`;
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

    return \`
      <div class="job-card" style="padding: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; gap: 12px; flex-wrap: wrap;">
          <div style="flex: 1; min-width: 200px;">
            <h3 style="font-size: 18px; font-weight: 700; color: #e5e2e1; margin-bottom: 8px; line-height: 1.3;">\${job.title}</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center;">
              <span style="font-size: 13px; color: #A1A1AA; display:flex; align-items:center; gap:4px;"><span class="material-symbols-outlined" style="font-size:14px;">business</span> \${job.company}</span>
              <span style="font-size: 13px; color: #A1A1AA; display:flex; align-items:center; gap:4px;"><span class="material-symbols-outlined" style="font-size:14px;">location_on</span> \${job.location}</span>
              \${isApplied ? \`<span class="pill" style="background: rgba(16,185,129,0.15); color: #34d399; font-weight: 700; font-size:11px; padding: 2px 8px;">APPLIED</span>\` : ''}
            </div>
          </div>
          <div class="score-badge" style="flex-shrink: 0;">
            <span class="material-symbols-outlined" style="font-size:16px;">bolt</span> \${score}%
          </div>
        </div>

        <div style="font-size: 13px; color: #34d399; font-weight: 500; margin-bottom: 12px; line-height: 1.5;">
          <span class="material-symbols-outlined" style="font-size:14px; vertical-align: middle; margin-right: 4px;">lightbulb</span>\${isEn ? 'Why it matches:' : 'Dlaczego pasuje:'} \${summaryText}
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 20px;">
          \${strengthsArray.map(s => \`<span class="strength-tag">\${s}</span>\`).join('')}
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 12px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 16px;">
          <button class="btn-apply" onclick="openBlurbModal(\${idx})">
            <span class="material-symbols-outlined" style="font-size:18px;">analytics</span> \${isEn ? 'AI Analysis' : 'Analiza AI'}
          </button>
          \${!isApplied ? \`
            <button class="btn-apply" style="flex: 0 0 auto; padding: 12px; border-color: rgba(48,209,88,0.3); color: #30D158;" onclick="markApplied('\${job.id}')" title="\${isEn ? 'Mark Applied' : 'Oznacz jako aplikowane'}">
              <span class="material-symbols-outlined" style="font-size:18px;">check</span>
            </button>
          \` : ''}
          <button class="btn-apply" style="flex: 0 0 auto; padding: 12px; border-color: rgba(239,68,68,0.3); color: #f87171;" onclick="dismissJob('\${job.id}')" title="\${isEn ? 'Dismiss' : 'Odrzuć'}">
            <span class="material-symbols-outlined" style="font-size:18px;">close</span>
          </button>
        </div>
      </div>
    \`;
  }).join('');
}
`;
    const finalCode = code.substring(0, startIdx) + newRenderJobs + code.substring(endIdx);
    fs.writeFileSync('static/app.js', finalCode);
    console.log("Replaced successfully!");
} else {
    console.log("Could not find start or end indices");
}
