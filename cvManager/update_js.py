import re

with open('static/app_v4.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Update loadProfile to handle EN/PL translation of profile card
new_loadProfile = """async function loadProfile() {
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
}"""

js = re.sub(r'async function loadProfile\(\) \{[\s\S]*?(?=async function loadJobs)', new_loadProfile + '\n\n', js)

# Also ensure setLanguage calls loadProfile()
js = js.replace("if (reload && currentJobs.length > 0) {\n    renderJobs(currentJobs);\n  }", "loadProfile();\n  if (reload && currentJobs.length > 0) {\n    renderJobs(currentJobs);\n  }")

with open('static/app_v4.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(js)

print("Updated app_v4.js for profile translation!")
