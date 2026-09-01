import re

with open('static/app_v7.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Fix loadJobs to handle data.jobs || data
new_loadJobs = """async function loadJobs() {
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
  } catch (err) {
    console.error('Failed to load jobs:', err);
    grid.innerHTML = `<div style="text-align: center; padding: 40px; color: #ef4444;">${isEn ? 'Failed to load jobs.' : 'Błąd ładowania ofert.'}</div>`;
  }
}"""

js = re.sub(r'async function loadJobs\(\) \{[\s\S]*?(?=function renderProgressBar)', new_loadJobs + '\n\n', js)

with open('static/app_v7.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(js)

print("Fixed loadJobs array parsing!")
