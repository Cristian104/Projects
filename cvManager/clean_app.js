const fs = require('fs');

let lines = fs.readFileSync('static/app_v4.js', 'utf8').split('\n');

let newLines = [];
let insideRenderJobs = false;

for (let line of lines) {
    if (line.includes('function renderJobs(')) {
        if (!insideRenderJobs) {
            insideRenderJobs = true;
            // Write our clean renderJobs function
            newLines.push(`function renderJobs(jobs) {
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
    if (summaryText.length > 140) summaryText = summaryText.substring(0, 140) + '...';
    
    let strengthsArray = helperExtractArray(match.strengths);
    if (strengthsArray.length > 3) strengthsArray = strengthsArray.slice(0, 3);

    const sal = match.salary_estimator || {};
    const estRange = sal.estimated_range || job.salary || '6,5k - 8,5k PLN';

    const isApplied = (job.user_status === 'applied');
    const jobUrl = job.url || '#';

    return \`
      <div class="job-card" style="padding: 20px; background: rgba(28, 28, 30, 0.75); backdrop-filter: blur(30px); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; margin-bottom: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; gap: 12px; flex-wrap: wrap;">
          <div style="flex: 1; min-width: 180px;">
            <h3 style="font-size: 17px; font-weight: 700; color: #e5e2e1; margin-bottom: 6px; line-height: 1.3;">\${job.title}</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font-size: 12px; color: #A1A1AA;">
              <span style="display:flex; align-items:center; gap:4px;"><span class="material-symbols-outlined" style="font-size:14px;">business</span> \${job.company}</span>
              <span style="display:flex; align-items:center; gap:4px;"><span class="material-symbols-outlined" style="font-size:14px;">location_on</span> \${job.location}</span>
              <span style="color: #34d399; font-weight: 600;">💰 \${estRange}</span>
              \${isApplied ? \`<span class="pill" style="background: rgba(16,185,129,0.15); color: #34d399; font-weight: 700; font-size:10px; padding: 2px 6px; border-radius: 4px;">APPLIED</span>\` : ''}
            </div>
          </div>
          <div class="score-badge" style="flex-shrink: 0; background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); color: #60a5fa; font-weight: 700; padding: 4px 10px; border-radius: 20px; font-size: 13px;">
            ⚡ \${score}% Match
          </div>
        </div>

        <div style="font-size: 13px; color: #34d399; font-weight: 500; margin-bottom: 12px; line-height: 1.4; background: rgba(52, 211, 153, 0.05); padding: 8px 12px; border-radius: 8px; border-left: 3px solid #34d399;">
          💡 <strong>\${isEn ? 'Why it matches:' : 'Dlaczego pasuje:'}</strong> \${summaryText}
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px;">
          \${strengthsArray.map(s => \`<span class="strength-tag" style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #d1d5db; font-size: 11px; padding: 3px 8px; border-radius: 6px;">✓ \${s}</span>\`).join('')}
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 10px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px; align-items: center;">
          <button class="btn-apply" onclick="openBlurbModal(\${idx})" style="flex: 1; min-width: 140px; padding: 10px 14px; font-size: 13px; border-radius: 10px; background: rgba(10, 132, 255, 0.2); border: 1px solid rgba(10, 132, 255, 0.4); color: #60a5fa; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px;">
            📝 \${isEn ? 'AI Cover Package' : 'Paczka AI & Wynagrodzenie'}
          </button>
          
          <a href="\${jobUrl}" target="_blank" class="btn-apply" style="padding: 10px 14px; font-size: 13px; border-radius: 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15); color: #e5e2e1; text-decoration: none; display: flex; align-items: center; gap: 6px;">
            🚀 \${isEn ? 'Apply on Site' : 'Aplikuj na stronie'}
          </a>

          \${!isApplied ? \`
            <button class="btn-apply" style="padding: 10px 12px; border-radius: 10px; background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); color: #34d399; cursor: pointer;" onclick="markApplied('\${job.id}')" title="\${isEn ? 'Mark Applied' : 'Oznacz jako aplikowane'}">
              ✅
            </button>
          \` : ''}
          
          <button class="btn-apply" style="padding: 10px 12px; border-radius: 10px; background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.3); color: #f87171; cursor: pointer;" onclick="dismissJob('\${job.id}')" title="\${isEn ? 'Dismiss' : 'Odrzuć'}">
            ❌
          </button>
        </div>
      </div>
    \`;
  }).join('');
}`);
        }
    } else if (line.includes('async function markApplied(')) {
        insideRenderJobs = false;
        newLines.push(line);
    } else if (!insideRenderJobs) {
        newLines.push(line);
    }
}

fs.writeFileSync('static/app_v4.js', newLines.join('\n'));
console.log("Line by line replacement complete!");
