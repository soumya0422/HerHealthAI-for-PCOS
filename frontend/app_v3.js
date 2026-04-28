/* ═══════════════════════════════
   HerHealthAI — Application Logic
   ═══════════════════════════════ */

const API_BASE = window.location.origin;

// ─── PROFILE COLOR PALETTE ───
const PROFILE_COLORS = [
  { bg: 'rgba(168,85,247,0.15)',  border: 'rgba(168,85,247,0.4)',  text: '#c084fc', grad: 'linear-gradient(135deg, #a855f7, #7c3aed)' },
  { bg: 'rgba(236,72,153,0.15)',  border: 'rgba(236,72,153,0.4)',  text: '#f472b6', grad: 'linear-gradient(135deg, #ec4899, #db2777)' },
  { bg: 'rgba(6,182,212,0.15)',   border: 'rgba(6,182,212,0.4)',   text: '#22d3ee', grad: 'linear-gradient(135deg, #06b6d4, #0891b2)' },
  { bg: 'rgba(34,197,94,0.15)',   border: 'rgba(34,197,94,0.4)',   text: '#4ade80', grad: 'linear-gradient(135deg, #22c55e, #16a34a)' },
  { bg: 'rgba(245,158,11,0.15)',  border: 'rgba(245,158,11,0.4)',  text: '#fbbf24', grad: 'linear-gradient(135deg, #f59e0b, #d97706)' },
];

// ─── STATE ───
let state = {
  token: localStorage.getItem('hhToken') || null,
  user:  JSON.parse(localStorage.getItem('hhUser') || 'null'),
  currentStep: 1,
  symptoms: { weight_gain:0, hair_growth:0, skin_darkening:0, hair_loss:0, pimples:0, fast_food:0, exercise:0 },
  diarySymptoms: [],
  cycleRegular: 1,
  lastResult: null,
  activeProfile: null,
  profiles: []
};

// ─── ON LOAD ───
window.addEventListener('DOMContentLoaded', () => {
  initParticles();
  updateNavUI();
  updateProfileContext();
  loadModelMetrics();
  calcBMI();
  if (state.token) fetchProfiles();
});

// ════════════════════════════════
//  PARTICLE BACKGROUND
// ════════════════════════════════
function initParticles() {
  const canvas = document.getElementById('particleCanvas');
  const ctx    = canvas.getContext('2d');
  let W, H, particles;

  function resize() { W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; }
  window.addEventListener('resize', resize);
  resize();

  particles = Array.from({ length: 55 }, () => ({
    x: Math.random() * W, y: Math.random() * H,
    r: Math.random() * 2 + 0.5,
    dx: (Math.random() - 0.5) * 0.3,
    dy: (Math.random() - 0.5) * 0.3,
    color: Math.random() > 0.5 ? 'rgba(168,85,247,' : 'rgba(236,72,153,'
  }));

  function draw() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.color + '0.6)';
      ctx.fill();
      p.x += p.dx; p.y += p.dy;
      if (p.x < 0 || p.x > W) p.dx *= -1;
      if (p.y < 0 || p.y > H) p.dy *= -1;
    });

    // Connect nearby particles
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const d = Math.hypot(particles[i].x - particles[j].x, particles[i].y - particles[j].y);
        if (d < 120) {
          ctx.beginPath();
          ctx.strokeStyle = `rgba(168,85,247,${0.12 * (1 - d / 120)})`;
          ctx.lineWidth = 0.5;
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(draw);
  }
  draw();
}

// ════════════════════════════════
//  NAVIGATION
// ════════════════════════════════
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => { p.classList.remove('active'); p.classList.add('hidden'); });
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));

  const pageMap = { landing: 'landingPage', assess: 'assessPage', results: 'resultsPage', progress: 'progressPage', diary: 'diaryPage' };
  const navMap  = { landing: 'navHome', assess: 'navAssess', results: null, progress: 'navProgress', diary: 'navDiary' };

  const page = document.getElementById(pageMap[name]);
  if (page) { page.classList.remove('hidden'); page.classList.add('active'); }
  if (navMap[name]) document.getElementById(navMap[name])?.classList.add('active');

  if (name === 'progress') loadProgress();
  if (name === 'diary') initDiaryPage();
  updateProfileContext();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function scrollToHow() { document.getElementById('howSection')?.scrollIntoView({ behavior: 'smooth' }); }
function startAssessment() { showPage('assess'); }

// ════════════════════════════════
//  AUTH
// ════════════════════════════════
function openModal(tab) {
  document.getElementById('authModal').classList.remove('hidden');
  switchTab(tab);
}
function closeModal() { document.getElementById('authModal').classList.add('hidden'); }
function switchTab(tab) {
  const l = document.getElementById('loginTab');
  const r = document.getElementById('registerTab');
  if (tab === 'login')    { l.classList.remove('hidden'); r.classList.add('hidden'); }
  else                    { r.classList.remove('hidden'); l.classList.add('hidden'); }
}

async function doLogin() {
  const email = document.getElementById('loginEmail').value.trim();
  const pass  = document.getElementById('loginPassword').value;
  const errEl = document.getElementById('loginError');
  errEl.classList.add('hidden');

  if (!email || !pass) { showErr(errEl, 'Please fill all fields.'); return; }
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password: pass })
    });
    const data = await res.json();
    if (!res.ok) { showErr(errEl, data.detail || 'Login failed'); return; }
    saveAuth(data.token, data.user);
    closeModal(); toast(`Welcome back, ${data.user.name}! 💜`);
  } catch (e) { showErr(errEl, 'Connection error. Is the backend running?'); }
}

async function doRegister() {
  const name  = document.getElementById('regName').value.trim();
  const email = document.getElementById('regEmail').value.trim();
  const pass  = document.getElementById('regPassword').value;
  const errEl = document.getElementById('regError');
  errEl.classList.add('hidden');

  if (!name || !email || !pass) { showErr(errEl, 'Please fill all fields.'); return; }
  if (pass.length < 6) { showErr(errEl, 'Password must be at least 6 characters.'); return; }
  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password: pass })
    });
    const data = await res.json();
    if (!res.ok) { showErr(errEl, data.detail || 'Registration failed'); return; }
    saveAuth(data.token, data.user);
    closeModal(); toast(`Welcome to HerHealthAI, ${data.user.name}! 🌸`);
  } catch (e) { showErr(errEl, 'Connection error. Is the backend running?'); }
}

function saveAuth(token, user) {
  state.token = token;
  state.user  = user;
  localStorage.setItem('hhToken', token);
  localStorage.setItem('hhUser', JSON.stringify(user));
  updateNavUI();
  fetchProfiles();
}

function logout() {
  state.token = null; state.user = null;
  state.activeProfile = null; state.profiles = [];
  localStorage.removeItem('hhToken'); localStorage.removeItem('hhUser');
  updateNavUI(); updateProfileContext(); showPage('landing'); toast('Logged out. See you soon! 👋');
}

function updateNavUI() {
  const auth = document.getElementById('navAuth');
  const user = document.getElementById('navUser');
  if (state.token && state.user) {
    auth.classList.add('hidden'); user.classList.remove('hidden');
    const initial = getProfileInitials(state.activeProfile?.name || state.user.name);
    const color = getProfileColor(state.activeProfile);
    const avatar = document.getElementById('userAvatar');
    avatar.textContent = initial;
    avatar.style.background = color.grad;
  } else {
    auth.classList.remove('hidden'); user.classList.add('hidden');
  }
}

// ════════════════════════════════
//  PROFILE MANAGEMENT
// ════════════════════════════════

function getProfileInitials(name) {
  if (!name) return '?';
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return name.charAt(0).toUpperCase();
}

function getProfileColor(profile) {
  if (!profile) return PROFILE_COLORS[0];
  const idx = state.profiles.findIndex(p => p.profile_id === profile.profile_id);
  return PROFILE_COLORS[idx >= 0 ? idx % PROFILE_COLORS.length : 0];
}

function getProfileAge(profile) {
  if (!profile?.dob) return null;
  const dob = new Date(profile.dob);
  const diff = Date.now() - dob.getTime();
  return Math.abs(new Date(diff).getUTCFullYear() - 1970);
}

async function fetchProfiles() {
  if (!state.token) return;
  try {
    const res = await fetch(`${API_BASE}/profiles/`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (res.status === 401) {
      logout();
      toast('⚠️ Session expired. Please log in again.');
      return;
    }
    const profiles = await res.json();
    state.profiles = profiles;
    
    if (profiles.length > 0 && !state.activeProfile) {
      state.activeProfile = profiles[0];
    }
    renderProfileSelect();
    updateNavUI();
    updateProfileContext();
  } catch (e) { console.error('Error fetching profiles', e); }
}

function renderProfileSelect() {
  const sel = document.getElementById('profileSelect');
  if (!sel) return;
  sel.innerHTML = state.profiles.map((p, i) => {
    const color = PROFILE_COLORS[i % PROFILE_COLORS.length];
    const age = getProfileAge(p);
    const label = age ? `${p.name} (${age}y)` : p.name;
    return `<option value="${p.profile_id}" ${state.activeProfile?.profile_id === p.profile_id ? 'selected' : ''}>${label}</option>`;
  }).join('');
}

function switchProfile(id) {
  const profile = state.profiles.find(p => p.profile_id === id);
  if (profile && profile.profile_id !== state.activeProfile?.profile_id) {
    state.activeProfile = profile;
    const color = getProfileColor(profile);

    // Update avatar
    updateNavUI();
    updateProfileContext();

    // Show profile switch confirmation banner
    showProfileSwitchBanner(profile);

    // Refresh active page data
    if (document.getElementById('progressPage')?.classList.contains('active')) loadProgress();
    if (document.getElementById('diaryPage')?.classList.contains('active')) { loadDiaryHistory(); }
    if (document.getElementById('resultsPage')?.classList.contains('active')) {
      // Clear stale results when switching profile
      document.getElementById('riskDesc').textContent = 'Switch detected — run a new assessment for this profile.';
    }
  }
}

function showProfileSwitchBanner(profile) {
  const color = getProfileColor(profile);
  const existing = document.getElementById('profileSwitchToast');
  if (existing) existing.remove();

  const el = document.createElement('div');
  el.id = 'profileSwitchToast';
  el.className = 'profile-switch-toast';
  el.innerHTML = `
    <div class="pst-avatar" style="background:${color.grad}">${getProfileInitials(profile.name)}</div>
    <div class="pst-text">
      <span class="pst-label">Switched to</span>
      <span class="pst-name">${profile.name}</span>
    </div>
    <span class="pst-check">✓</span>
  `;
  document.body.appendChild(el);
  requestAnimationFrame(() => el.classList.add('visible'));
  setTimeout(() => {
    el.classList.remove('visible');
    setTimeout(() => el.remove(), 400);
  }, 2500);
}

// ════════════════════════════════
//  PROFILE CONTEXT BANNERS
// ════════════════════════════════
function updateProfileContext() {
  const isLoggedIn = !!(state.token && state.user);
  const profile = state.activeProfile;
  const name = profile?.name || state.user?.name || 'Guest';
  const color = getProfileColor(profile);
  const initial = getProfileInitials(name);
  const age = getProfileAge(profile);
  const multiProfile = state.profiles.length > 1;

  // ─── Landing page greeting ───
  const landingCtx = document.getElementById('landingProfileCtx');
  if (landingCtx) {
    if (isLoggedIn) {
      landingCtx.classList.remove('hidden');
      const greeting = getTimeGreeting();
      landingCtx.innerHTML = `
        <div class="profile-ctx-avatar" style="background:${color.grad}">${initial}</div>
        <div class="profile-ctx-text">
          <span class="profile-ctx-greeting">${greeting}, <strong>${name}</strong> 👋</span>
          <span class="profile-ctx-sub">${multiProfile ? 'Viewing your personal dashboard' : 'Your personalized health dashboard'}</span>
        </div>
        ${multiProfile ? '<div class="profile-ctx-badge">Active Profile</div>' : ''}
      `;
    } else {
      landingCtx.classList.add('hidden');
    }
  }

  // ─── Assessment page ───
  const assessCtx = document.getElementById('assessProfileCtx');
  if (assessCtx) {
    if (isLoggedIn && profile) {
      assessCtx.classList.remove('hidden');
      const ageText = age ? ` · Age ${age}` : '';
      assessCtx.innerHTML = `
        <div class="profile-ctx-avatar sm" style="background:${color.grad}">${initial}</div>
        <span class="profile-ctx-inline">Assessing for <strong>${name}</strong>${ageText}</span>
        ${multiProfile ? `<button class="profile-ctx-switch" onclick="document.getElementById('profileSelect').focus()">Switch</button>` : ''}
      `;
    } else {
      assessCtx.classList.add('hidden');
    }
  }

  // ─── Progress page ───
  const progressCtx = document.getElementById('progressProfileCtx');
  if (progressCtx) {
    if (isLoggedIn && profile) {
      progressCtx.classList.remove('hidden');
      progressCtx.innerHTML = `
        <div class="profile-ctx-avatar sm" style="background:${color.grad}">${initial}</div>
        <span class="profile-ctx-inline">Hi, <strong>${name}</strong>. This is your progress.</span>
        ${multiProfile ? `<button class="profile-ctx-switch" onclick="document.getElementById('profileSelect').focus()">Switch Profile</button>` : ''}
      `;
    } else {
      progressCtx.classList.add('hidden');
    }
  }

  // ─── Results page ───
  const resultsCtx = document.getElementById('resultsProfileCtx');
  if (resultsCtx) {
    if (isLoggedIn && profile) {
      resultsCtx.classList.remove('hidden');
      resultsCtx.innerHTML = `
        <div class="profile-ctx-avatar sm" style="background:${color.grad}">${initial}</div>
        <span class="profile-ctx-inline">Results for <strong>${name}</strong></span>
      `;
    } else {
      resultsCtx.classList.add('hidden');
    }
  }

  // ─── Diary page ───
  const diaryCtx = document.getElementById('diaryProfileCtx');
  if (diaryCtx) {
    if (isLoggedIn && profile) {
      diaryCtx.classList.remove('hidden');
      diaryCtx.innerHTML = `
        <div class="profile-ctx-avatar sm" style="background:${color.grad}">${initial}</div>
        <span class="profile-ctx-inline"><strong>${name}'s</strong> Cycle Diary</span>
        ${multiProfile ? `<button class="profile-ctx-switch" onclick="document.getElementById('profileSelect').focus()">Switch Profile</button>` : ''}
      `;
    } else {
      diaryCtx.classList.add('hidden');
    }
  }

  // ─── No-data states ───
  const noDataMsg = document.querySelector('#progressNoData h3');
  if (noDataMsg && isLoggedIn) {
    noDataMsg.textContent = `No Assessments Yet for ${name}`;
  }
  const noDataDesc = document.querySelector('#progressNoData p');
  if (noDataDesc && isLoggedIn) {
    noDataDesc.textContent = `Complete ${name}'s first PCOS risk assessment to start tracking their health journey.`;
  }
}

function getTimeGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

function openProfileModal() { document.getElementById('profileModal').classList.remove('hidden'); }
function closeProfileModal() { document.getElementById('profileModal').classList.add('hidden'); }

async function doCreateProfile() {
  const name = document.getElementById('newProfileName').value.trim();
  const dob  = document.getElementById('newProfileDob').value;
  const err  = document.getElementById('profileError');
  err.classList.add('hidden');

  if (!name || !dob) { showErr(err, 'Please enter name and date of birth.'); return; }

  // Check for duplicate names
  const duplicate = state.profiles.find(p => p.name.toLowerCase() === name.toLowerCase());
  if (duplicate) {
    showErr(err, `A profile named "${name}" already exists. Please use a different name.`);
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/profiles/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${state.token}` },
      body: JSON.stringify({ name, dob })
    });
    const data = await res.json();
    if (!res.ok) { showErr(err, data.detail || 'Failed to create profile'); return; }
    
    state.profiles.push(data);
    state.activeProfile = data;
    renderProfileSelect();
    updateNavUI();
    updateProfileContext();
    closeProfileModal();
    showProfileSwitchBanner(data);
    toast(`Created profile for ${data.name}! 🌸`);
  } catch (e) { showErr(err, 'Connection error.'); }
}

function showErr(el, msg) { el.textContent = msg; el.classList.remove('hidden'); }

// ════════════════════════════════
//  ASSESSMENT FORM
// ════════════════════════════════
function calcBMI() {
  const w = parseFloat(document.getElementById('f_weight')?.value || 0);
  const h = parseFloat(document.getElementById('f_height')?.value || 0);
  if (w > 0 && h > 0) {
    const bmi = w / ((h / 100) ** 2);
    document.getElementById('f_bmi').value = bmi.toFixed(1);
    const cat = bmi < 18.5 ? 'Underweight' : bmi < 25 ? 'Normal' : bmi < 30 ? 'Overweight' : 'Obese';
    document.getElementById('bmiCat').textContent = cat;
    document.getElementById('bmiCat').style.color = bmi > 25 ? '#f59e0b' : '#22c55e';
  }
}
function calcWHR() {
  const w = parseFloat(document.getElementById('f_waist')?.value || 0);
  const h = parseFloat(document.getElementById('f_hip')?.value || 0);
  // just for display; will be calculated on backend too
}
function calcFSHLH() { /* ratios calculated in backend */ }
function setCycle(val) { state.cycleRegular = val; }

function toggleSymptom(key) {
  state.symptoms[key] = state.symptoms[key] ? 0 : 1;
  const el = document.getElementById(`tog_${key}`);
  if (state.symptoms[key]) el.classList.add('active');
  else el.classList.remove('active');
}

// Step navigation
function nextStep(current) {
  if (!validateStep(current)) return;
  markDone(current);
  goToStep(current + 1);
}
function prevStep(current) { goToStep(current - 1); }

function goToStep(n) {
  document.querySelectorAll('.form-step').forEach(s => { s.classList.add('hidden'); s.classList.remove('active'); });
  document.getElementById(`step${n}`).classList.remove('hidden');
  document.getElementById(`step${n}`).classList.add('active');
  state.currentStep = n;
  updateStepUI(n);
  window.scrollTo({ top: 160, behavior: 'smooth' });
}

function markDone(n) {
  const dot = document.getElementById(`dot${n}`);
  dot.classList.remove('active'); dot.classList.add('done');
  dot.querySelector('span').textContent = '✓';
}

function updateStepUI(n) {
  document.querySelectorAll('.step-dot').forEach((d, i) => {
    d.classList.remove('active');
    if (i + 1 === n) d.classList.add('active');
  });
  document.getElementById('stepBarFill').style.width = `${(n / 4) * 100}%`;
}

function calculateAge(dobStr) {
  if (!dobStr) return null;
  const dob = new Date(dobStr);
  const diffMs = Date.now() - dob.getTime();
  const ageDt = new Date(diffMs);
  return Math.abs(ageDt.getUTCFullYear() - 1970);
}

function handleDobChange() {
  const dob = document.getElementById('f_dob').value;
  const age = calculateAge(dob);
  document.getElementById('ageDisplay').textContent = age !== null ? `Age: ${age}` : 'Age: --';
}

function validateStep(n) {
  if (n === 1) {
    const dob = document.getElementById('f_dob').value;
    const w   = parseFloat(document.getElementById('f_weight').value);
    const h   = parseFloat(document.getElementById('f_height').value);
    
    if (!dob) { toast('⚠️ Please enter your date of birth.'); return false; }
    const age = calculateAge(dob);
    if (age < 12 || age > 60) { toast('⚠️ PCOS Risk Assessment is optimized for ages 12–60.'); return false; }
    if (!w || w < 20 || w > 250) { toast('⚠️ Please enter a valid weight (20–250 kg).'); return false; }
    if (!h || h < 100 || h > 220) { toast('⚠️ Please enter a valid height (100–220 cm).'); return false; }

    // Identify mismatch check: Catch early!
    if (state.token && state.activeProfile && state.activeProfile.dob) {
      if (dob !== state.activeProfile.dob) {
        handleIdentityMismatch();
        return false;
      }
    }
  }
  return true;
}

function collectPayload() {
  const v = (id) => parseFloat(document.getElementById(id)?.value) || null;
  const vs = (id) => document.getElementById(id)?.value || null;
  return {
    profile_id:     state.activeProfile?.profile_id,
    dob:            vs('f_dob'),
    weight:         v('f_weight'),
    height:         v('f_height'),
    bmi:            v('f_bmi'),
    pulse:          v('f_pulse'),
    rr:             v('f_rr'),
    hb:             v('f_hb'),
    rbs:            v('f_rbs'),
    bp_systolic:    v('f_bps'),
    bp_diastolic:   v('f_bpd'),
    tsh:            v('f_tsh'),
    amh:            v('f_amh'),
    prl:            v('f_prl'),
    vitd:           v('f_vitd'),
    fsh:            v('f_fsh'),
    lh:             v('f_lh'),
    cycle_regular:  state.cycleRegular,
    cycle_length:   v('f_cycle') || 28,
    waist:          v('f_waist'),
    hip:            v('f_hip'),
    marriage_years: v('f_marriage'),
    weight_gain:    state.symptoms.weight_gain,
    hair_growth:    state.symptoms.hair_growth,
    skin_darkening: state.symptoms.skin_darkening,
    hair_loss:      state.symptoms.hair_loss,
    pimples:        state.symptoms.pimples,
    fast_food:      state.symptoms.fast_food,
    exercise:       state.symptoms.exercise,
    save_record:    !!state.token,
  };
}

// ════════════════════════════════
//  PREDICTION
// ════════════════════════════════
async function runPrediction() {
  const btn  = document.getElementById('predictBtnText');
  const spin = document.getElementById('predictSpinner');
  btn.classList.add('hidden'); spin.classList.remove('hidden');

  const payload = collectPayload();

  try {
    let result;
    if (state.token) {
      // Authenticated: save record + get AI recommendations
      const res = await fetch(`${API_BASE}/predict/full`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${state.token}` },
        body: JSON.stringify(payload)
      });
      
      // Handle expired/invalid token — auto-logout and fall through to anonymous prediction
      if (res.status === 401) {
        logout();
        toast('⚠️ Session expired. Running assessment as guest — please log in again to save results.');
        // Fall through to anonymous prediction below
      } else {
        const data = await res.json();
        
        if (res.status === 409) {
            handleIdentityMismatch(payload);
            return;
        }
        
        if (!res.ok) { throw new Error(data.detail || 'Prediction failed'); }
        result = data;
      }
    }

    // Anonymous prediction (also used as fallback when token expired)
    if (!result) {
      payload.save_record = false;
      const [predRes, recRes] = await Promise.all([
        fetch(`${API_BASE}/predict`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        }),
        fetch(`${API_BASE}/recommend`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
      ]);
      if (!predRes.ok) { const e = await predRes.json(); throw new Error(e.detail || 'Prediction failed'); }
      const pred = await predRes.json();
      const recs = recRes.ok ? (await recRes.json()).recommendations : {};
      result = { ...pred, recommendations: recs };
    }

    state.lastResult = result;
    showResults(result);
    showPage('results');

  } catch (e) {
    toast(`❌ ${e.message}`);
  } finally {
    btn.classList.remove('hidden'); spin.classList.add('hidden');
  }
}

// ════════════════════════════════
//  RESULTS RENDERING
// ════════════════════════════════
function showResults(data) {
  const riskPct   = data.risk_percentage || 0;
  const level     = data.risk_level || 'Low';
  const recs      = data.recommendations || {};
  const confidence = data.confidence || 0;
  const prevScore = data.previous_score;

  // Reset Feedback UI
  const feedbackArea = document.getElementById('feedbackFormArea');
  const feedbackSuccess = document.getElementById('feedbackSuccess');
  const diagnosisSelect = document.getElementById('clinicalDiagnosis');
  if (feedbackArea) feedbackArea.style.display = 'block';
  if (feedbackSuccess) feedbackSuccess.classList.add('hidden');
  if (diagnosisSelect) diagnosisSelect.value = '';

  // ─ Gauge
  animateGauge(riskPct);

  // ─ Badge
  const badge = document.getElementById('riskBadge');
  badge.textContent = `${level} Risk`;
  badge.className = 'risk-badge';
  if (level === 'Low')      { badge.classList.add('low'); }
  else if (level === 'Moderate') { badge.classList.add('mod'); }
  else                      { badge.classList.add('high'); }

  // ─ Description
  const descMap = {
    Low:      '😊 Great news! Your risk is low. Keep up healthy habits.',
    Moderate: '⚠️ Moderate risk detected. Lifestyle changes can make a big difference.',
    High:     '🚨 High risk detected. We recommend consulting a doctor soon.'
  };
  document.getElementById('riskDesc').textContent = descMap[level] || '';

  // ─ Meta
  if (data.bmi) document.getElementById('resBMI').textContent = `${data.bmi} kg/m²`;
  document.getElementById('resConf').textContent = `${confidence}%`;
  document.getElementById('resPrev').textContent = prevScore != null ? `${prevScore}%` : '—';

  // ─ Feature chart
  if (data.feature_contributions && data.feature_contributions.length > 0) {
    drawFeatureChart(data.feature_contributions.slice(0, 8));
  }

  // ─ Insights
  const insights = recs.health_insights || [];
  const insEl = document.getElementById('insightsList');
  insEl.innerHTML = insights.map((ins, i) => `
    <div class="insight-item ${riskPct > 60 && i === 0 ? 'warn' : ''}">
      <span class="insight-icon">${['💡','🔬','🌿'][i] || '•'}</span>
      <span>${ins}</span>
    </div>`).join('');

  // ─ Diet
  const dietInc = recs.diet_plan?.include || [];
  const dietAvd = recs.diet_plan?.avoid   || [];
  document.getElementById('dietInclude').innerHTML = dietInc.map(d => `<li>${d}</li>`).join('');
  document.getElementById('dietAvoid').innerHTML   = dietAvd.map(d => `<li>${d}</li>`).join('');
  document.getElementById('mealTiming').textContent = recs.diet_plan?.meal_timing || '';

  // ─ Exercise
  const schedule = recs.exercise_plan?.weekly_schedule || [];
  document.getElementById('exerciseSchedule').innerHTML = schedule.map(s => `
    <div class="schedule-card">
      <div class="sched-day">${s.day}</div>
      <div class="sched-activity">${s.activity}</div>
      <div class="sched-dur">⏱ ${s.duration}</div>
    </div>`).join('');
  document.getElementById('exerciseTip').innerHTML = `<strong>💡 Why exercise helps:</strong> ${recs.exercise_plan?.tip || ''}`;

  // ─ Lifestyle
  const tips = recs.lifestyle_tips || [];
  document.getElementById('lifestyleList').innerHTML = tips.map((t, i) => `
    <div class="lifestyle-item">
      <span class="lifestyle-num">${i + 1}</span>
      <span>${t}</span>
    </div>`).join('');
  if (recs.doctor_advice) {
    document.getElementById('doctorBox').innerHTML = `🩺 <strong>Doctor's Note:</strong> ${recs.doctor_advice}`;
    document.getElementById('doctorBox').style.display = 'block';
  }
}

// Animated gauge
function animateGauge(pct) {
  const fill = document.getElementById('gaugeFill');
  const label = document.getElementById('gaugePct');
  const totalLen = 251; // approximate arc length for the semicircle

  // Color by risk
  const color = pct < 30 ? '#22c55e' : pct < 70 ? '#f59e0b' : '#ef4444';

  // Create/update gradient
  let defs = fill.closest('svg').querySelector('defs') || fill.closest('svg').insertAdjacentHTML('afterbegin', '<defs></defs>') || fill.closest('svg').querySelector('defs');
  defs.innerHTML = `
    <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="${pct < 30 ? '#22c55e' : '#a855f7'}"/>
      <stop offset="100%" stop-color="${color}"/>
    </linearGradient>`;

  let current = 0;
  const target = (pct / 100) * totalLen;
  const step   = target / 60;

  const anim = setInterval(() => {
    current = Math.min(current + step, target);
    fill.setAttribute('stroke-dasharray', `${current} ${totalLen}`);
    label.textContent = `${Math.round((current / totalLen) * 100)}%`;
    if (current >= target) {
      clearInterval(anim);
      label.textContent = `${pct.toFixed(1)}%`;
    }
  }, 16);
}

// Feature contribution bar chart (Canvas) — with risk direction color coding
function drawFeatureChart(features) {
  const canvas = document.getElementById('featChart');
  const ctx    = canvas.getContext('2d');
  const dpr    = window.devicePixelRatio || 1;

  // Ensure crisp rendering on HiDPI
  const cssW = canvas.parentElement?.clientWidth || 560;
  const cssH = Math.max(300, features.length * 38 + 50);
  canvas.width  = cssW * dpr;
  canvas.height = cssH * dpr;
  canvas.style.width  = cssW + 'px';
  canvas.style.height = cssH + 'px';
  ctx.scale(dpr, dpr);

  const W = cssW, H = cssH;
  ctx.clearRect(0, 0, W, H);

  const maxImportance = Math.max(...features.map(f => f.importance));
  const barH     = 24;
  const gap       = 12;
  const labelW    = 170;
  const barAreaW  = W - labelW - 80;
  const startY    = 28;

  // Title
  ctx.fillStyle = '#e2e8f0';
  ctx.font = 'bold 13px Inter, sans-serif';
  ctx.textAlign = 'left';
  ctx.fillText('Key Factors Contributing to Your Result', 10, 16);

  features.forEach((feat, i) => {
    const y = startY + i * (barH + gap);
    const barW = (feat.importance / maxImportance) * barAreaW;
    const isRisk = feat.direction === 'increases_risk';

    // Background bar
    ctx.fillStyle = 'rgba(255,255,255,0.04)';
    roundRect(ctx, labelW + 10, y, barAreaW, barH, 6);
    ctx.fill();

    // Filled bar — red/pink for risk-increasing, green/teal for risk-decreasing
    const grad = ctx.createLinearGradient(labelW + 10, 0, labelW + 10 + barW, 0);
    if (isRisk) {
      grad.addColorStop(0, '#f97316');
      grad.addColorStop(1, '#ef4444');
    } else {
      grad.addColorStop(0, '#14b8a6');
      grad.addColorStop(1, '#22c55e');
    }
    ctx.fillStyle = grad;
    roundRect(ctx, labelW + 10, y, Math.max(barW, 4), barH, 6);
    ctx.fill();

    // Direction arrow
    const arrow = isRisk ? '▲' : '▼';
    ctx.fillStyle = isRisk ? '#fca5a5' : '#86efac';
    ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(arrow, labelW + 6, y + barH / 2 + 4);

    // Label — use human-readable label if available, else clean up feature name
    const displayName = (feat.label || feat.feature.replace(/\(.+\)/, '').replace('(Y/N)', '').trim()).substring(0, 22);
    ctx.fillStyle = '#cbd5e1';
    ctx.font = '11px Inter, sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(displayName, labelW - 2, y + barH / 2 + 4);

    // Percentage + direction label
    const pctText = `${(feat.importance * 100).toFixed(1)}%`;
    ctx.fillStyle = isRisk ? '#fca5a5' : '#86efac';
    ctx.font = 'bold 11px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(pctText, labelW + 10 + barW + 8, y + barH / 2 + 4);
  });

  // Legend
  const legendY = startY + features.length * (barH + gap) + 6;
  ctx.font = '10px Inter, sans-serif';
  // Risk increasing
  ctx.fillStyle = '#ef4444';
  roundRect(ctx, labelW + 10, legendY, 10, 10, 2); ctx.fill();
  ctx.fillStyle = '#94a3b8';
  ctx.textAlign = 'left';
  ctx.fillText('Increases Risk', labelW + 26, legendY + 9);
  // Risk decreasing
  ctx.fillStyle = '#22c55e';
  roundRect(ctx, labelW + 130, legendY, 10, 10, 2); ctx.fill();
  ctx.fillStyle = '#94a3b8';
  ctx.fillText('Decreases Risk', labelW + 146, legendY + 9);
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

async function submitClinicalFeedback() {
  const diagnosisSelect = document.getElementById('clinicalDiagnosis');
  if (!diagnosisSelect) return;
  const diagnosis = diagnosisSelect.value;
  
  if (!diagnosis) {
    toast('⚠️ Please select a valid diagnosis first.');
    return;
  }
  
  if (!state.lastResult || !state.lastResult.request_id) {
    toast('⚠️ Unlinkable result. Please run a new assessment first.');
    return;
  }

  const payload = {
    request_id: state.lastResult.request_id,
    diagnosis: diagnosis
  };

  try {
    const res = await fetch(`${API_BASE}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) throw new Error('Failed to submit feedback');
    
    document.getElementById('feedbackFormArea').style.display = 'none';
    document.getElementById('feedbackSuccess').classList.remove('hidden');
    toast('🎉 Feedback submitted to continuous learning AI!');
  } catch(e) {
    toast('❌ Error saving feedback');
  }
}

// ════════════════════════════════
//  RECOMMENDATIONS TABS
// ════════════════════════════════
function switchRecTab(name) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => { c.classList.remove('active'); c.classList.add('hidden'); });
  document.getElementById(`tab${name.charAt(0).toUpperCase() + name.slice(1)}`).classList.add('active');
  document.getElementById(`tabContent${name.charAt(0).toUpperCase() + name.slice(1)}`).classList.remove('hidden');
  document.getElementById(`tabContent${name.charAt(0).toUpperCase() + name.slice(1)}`).classList.add('active');
}

// ════════════════════════════════
//  PROGRESS PAGE
// ════════════════════════════════
async function loadProgress() {
  if (!state.token) {
    document.getElementById('progressAuth').classList.remove('hidden');
    document.getElementById('progressContent').classList.add('hidden');
    document.getElementById('progressNoData').classList.add('hidden');
    return;
  }
  document.getElementById('progressAuth').classList.add('hidden');

  try {
    const profile_id = state.activeProfile?.profile_id;
    const query = profile_id ? `?profile_id=${profile_id}` : '';
    
    const [progRes, histRes] = await Promise.all([
      fetch(`${API_BASE}/progress${query}`, { headers: { 'Authorization': `Bearer ${state.token}` } }),
      fetch(`${API_BASE}/history${query}`,  { headers: { 'Authorization': `Bearer ${state.token}` } })
    ]);
    const prog = await progRes.json();
    const hist = histRes.ok ? await histRes.json() : { records: [] };

    if (!prog.has_data || hist.records.length === 0) {
      document.getElementById('progressNoData').classList.remove('hidden');
      document.getElementById('progressContent').classList.add('hidden');
      return;
    }

    document.getElementById('progressContent').classList.remove('hidden');
    document.getElementById('progressNoData').classList.add('hidden');

    // Cards
    document.getElementById('progTotal').textContent  = prog.total_assessments;
    document.getElementById('progLatest').textContent = `${prog.latest_score}%`;
    document.getElementById('progFirst').textContent  = `${prog.first_score}%`;

    const imp = prog.improvement_percentage;
    const improving = imp > 0;
    document.getElementById('progImprovement').textContent = `${Math.abs(imp).toFixed(1)}%`;
    document.getElementById('progTrendIcon').textContent   = improving ? '📉' : imp < 0 ? '📈' : '➡️';

    // Progress line chart
    drawProgressChart(prog.scores_over_time || []);

    // History table
    const tbody = document.getElementById('historyBody');
    tbody.innerHTML = hist.records.map((r, i) => {
      const prev = hist.records[i + 1];
      const change = prev ? (prev.risk_score - r.risk_score).toFixed(1) : null;
      const lvl = r.risk_level.toLowerCase() === 'low' ? 'low' : r.risk_level.toLowerCase() === 'moderate' ? 'mod' : 'high';
      return `<tr>
        <td>${hist.records.length - i}</td>
        <td>${new Date(r.prediction_date).toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' })}</td>
        <td style="font-weight:700; color:var(--text-primary)">${r.risk_score}%</td>
        <td><span class="level-badge ${lvl}">${r.risk_level}</span></td>
        <td>${change !== null ? `<span class="${parseFloat(change) > 0 ? 'change-pos' : 'change-neg'}">${parseFloat(change) > 0 ? '▼' : '▲'} ${Math.abs(change)}%</span>` : '—'}</td>
      </tr>`;
    }).join('');

  } catch (e) {
    console.error('Progress load error:', e);
    toast('⚠️ Could not load progress data.');
  }
}

function drawProgressChart(scores) {
  const canvas = document.getElementById('progChart');
  const ctx    = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  if (!scores || scores.length === 0) {
    document.getElementById('progChartEmpty').classList.remove('hidden');
    return;
  }

  const pad = { top: 20, bottom: 50, left: 50, right: 30 };
  const cW = W - pad.left - pad.right;
  const cH = H - pad.top - pad.bottom;

  const vals  = scores.map(s => s.score);
  const minV  = Math.max(0, Math.min(...vals) - 10);
  const maxV  = Math.min(100, Math.max(...vals) + 10);

  // Grid lines
  [0, 25, 50, 75, 100].forEach(v => {
    if (v < minV || v > maxV) return;
    const y = pad.top + cH - ((v - minV) / (maxV - minV)) * cH;
    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(W - pad.right, y); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#64748b'; ctx.font = '11px Inter'; ctx.textAlign = 'right';
    ctx.fillText(`${v}%`, pad.left - 8, y + 4);
  });

  // Risk zones shading
  const zones = [
    { from: 0,  to: 30,  color: 'rgba(34,197,94,0.04)' },
    { from: 30, to: 70,  color: 'rgba(245,158,11,0.04)' },
    { from: 70, to: 100, color: 'rgba(239,68,68,0.04)' }
  ];
  zones.forEach(z => {
    const y1 = pad.top + cH - ((Math.min(z.to, maxV) - minV) / (maxV - minV)) * cH;
    const y2 = pad.top + cH - ((Math.max(z.from, minV) - minV) / (maxV - minV)) * cH;
    if (y2 > y1) { ctx.fillStyle = z.color; ctx.fillRect(pad.left, y1, cW, y2 - y1); }
  });

  // Points
  const points = scores.map((s, i) => ({
    x: pad.left + (i / Math.max(scores.length - 1, 1)) * cW,
    y: pad.top + cH - ((s.score - minV) / (maxV - minV)) * cH
  }));

  // Area fill
  const areaGrad = ctx.createLinearGradient(0, pad.top, 0, H - pad.bottom);
  areaGrad.addColorStop(0, 'rgba(168,85,247,0.25)');
  areaGrad.addColorStop(1, 'rgba(168,85,247,0)');
  ctx.fillStyle = areaGrad;
  ctx.beginPath();
  ctx.moveTo(points[0].x, H - pad.bottom);
  points.forEach(p => ctx.lineTo(p.x, p.y));
  ctx.lineTo(points[points.length - 1].x, H - pad.bottom);
  ctx.closePath(); ctx.fill();

  // Line
  const lineGrad = ctx.createLinearGradient(pad.left, 0, W - pad.right, 0);
  lineGrad.addColorStop(0, '#a855f7');
  lineGrad.addColorStop(1, '#ec4899');
  ctx.strokeStyle = lineGrad;
  ctx.lineWidth = 3;
  ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  ctx.setLineDash([]);
  ctx.beginPath();
  points.forEach((p, i) => i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y));
  ctx.stroke();

  // Dots + labels
  points.forEach((p, i) => {
    ctx.beginPath();
    ctx.arc(p.x, p.y, 6, 0, Math.PI * 2);
    ctx.fillStyle = '#a855f7'; ctx.fill();
    ctx.strokeStyle = '#1a1a2e'; ctx.lineWidth = 2; ctx.stroke();

    ctx.fillStyle = '#f8fafc'; ctx.font = 'bold 10px Inter'; ctx.textAlign = 'center';
    ctx.fillText(`${scores[i].score}%`, p.x, p.y - 12);

    ctx.fillStyle = '#64748b'; ctx.font = '10px Inter';
    ctx.fillText(scores[i].date?.slice(5) || '', p.x, H - pad.bottom + 18);
  });
}

// ════════════════════════════════
//  MODEL METRICS (API)
// ════════════════════════════════
async function loadModelMetrics() {
  try {
    const res = await fetch(`${API_BASE}/metrics`);
    if (!res.ok) return;
    const m = await res.json();
    if (m.accuracy)  document.getElementById('lAccuracy')?.setAttribute('data-val', m.accuracy + '%');
    document.getElementById('lAccuracy') && (document.getElementById('lAccuracy').textContent = m.accuracy  + '%');
    document.getElementById('lPrecision') && (document.getElementById('lPrecision').textContent = m.precision + '%');
    document.getElementById('lRecall')   && (document.getElementById('lRecall').textContent = m.recall   + '%');
    document.getElementById('lF1')       && (document.getElementById('lF1').textContent = m.f1_score + '%');
    document.getElementById('lAUC')      && (document.getElementById('lAUC').textContent = m.roc_auc  + '%');
  } catch (e) {
    // Backend might not be running yet — use hardcoded values (already set in HTML)
  }
}

// ════════════════════════════════
//  TOAST
// ════════════════════════════════
let toastTimer = null;
function toast(msg, duration = 3000) {
  const el = document.getElementById('toast');
  el.textContent = msg; el.classList.remove('hidden');
  toastTimer = setTimeout(() => el.classList.add('hidden'), duration);
}

// ════════════════════════════════
//  DIARY LOGIC
// ════════════════════════════════
function initDiaryPage() {
  if (!state.token) {
    document.getElementById('diaryAuth').classList.remove('hidden');
    document.getElementById('diaryContent').classList.add('hidden');
    return;
  }
  document.getElementById('diaryAuth').classList.add('hidden');
  document.getElementById('diaryContent').classList.remove('hidden');
  document.getElementById('d_date').valueAsDate = new Date();
  loadDiaryHistory();
}

async function loadDiaryHistory() {
  if (!state.token) return;
  const profile_id = state.activeProfile?.profile_id;
  const query = profile_id ? `?profile_id=${profile_id}` : '';
  try {
     const res = await fetch(`${API_BASE}/diary/history${query}`, {
       headers: { 'Authorization': `Bearer ${state.token}` }
     });
     // Render list if needed (optional for now)
  } catch (e) {}
}

function toggleDiarySymptom(symp, btn) {
  const idx = state.diarySymptoms.indexOf(symp);
  if (idx > -1) {
    state.diarySymptoms.splice(idx, 1);
    btn.classList.remove('active');
  } else {
    state.diarySymptoms.push(symp);
    btn.classList.add('active');
  }
}

async function logDiaryEntry() {
  if (!state.token) return;
  
  const d_date = document.getElementById('d_date').value;
  const d_status = document.getElementById('d_status').value;
  const flowNode = document.querySelector('input[name="flow"]:checked');
  const d_flow = flowNode ? flowNode.value : 'None';
  const d_mood = document.getElementById('d_mood').value;
  const d_notes = document.getElementById('d_notes').value;

  if (!d_date) { toast('⚠️ Please select a date.'); return; }

  const payload = {
    profile_id: state.activeProfile?.profile_id,
    date: d_date,
    period_status: d_status,
    flow_level: d_flow,
    symptoms: state.diarySymptoms,
    mood: d_mood,
    notes: d_notes
  };

  const btnText = document.getElementById('diaryLogText');
  const spinner = document.getElementById('diarySpinner');
  btnText.classList.add('hidden'); spinner.classList.remove('hidden');

  try {
    const res = await fetch(`${API_BASE}/diary/entry`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${state.token}` },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Failed to log diary entry');
    const insights = await res.json();
    
    renderDiaryInsights(insights);
    toast('✅ Diary entry successfully logged!');
  } catch (e) {
    toast(`❌ ${e.message}`);
  } finally {
    btnText.classList.remove('hidden'); spinner.classList.add('hidden');
  }
}

function renderDiaryInsights(data) {
  const box = document.getElementById('diaryAiOutput');
  box.style.display = 'block';
  box.innerHTML = `
    <div class="insight-item" style="color:#22c55e;"><strong>${data.entry_confirmation || ''}</strong></div>
    <hr style="border-color: rgba(255,255,255,0.05); margin: 0.5rem 0;">
    <div class="insight-item"><strong>📅 Cycle Summary:</strong> ${data.cycle_summary || ''}</div>
    <div class="insight-item"><strong>📊 Insights:</strong> ${data.insights || ''}</div>
    <div class="insight-item" style="color:#c4b5fd;"><strong>🔮 Next Period:</strong> ${data.next_period_prediction || ''}</div>
    <div class="insight-item" style="color:#f59e0b;"><strong>💡 Tips:</strong> ${data.tips || ''}</div>
  `;
}
// ════════════════════════════════
//  IDENTITY MISMATCH HANDLERS
// ════════════════════════════════
function handleIdentityMismatch(payload) {
    document.getElementById('mismatchModal').classList.remove('hidden');
    document.getElementById('newNameGroup').classList.add('hidden');
    document.getElementById('mismatchNewBtn').classList.remove('hidden');
}

function closeMismatchModal() {
    document.getElementById('mismatchModal').classList.add('hidden');
}

function showNewNameInput() {
    document.getElementById('newNameGroup').classList.remove('hidden');
    document.getElementById('mismatchNewBtn').classList.add('hidden');
    
    if (document.getElementById('confirmNewProfileBtn')) return;

    // Create actual profile after name input
    const btn = document.createElement('button');
    btn.id = 'confirmNewProfileBtn';
    btn.className = 'btn btn-primary btn-full';
    btn.textContent = 'Confirm & Create New Profile';
    btn.onclick = async () => {
        const name = document.getElementById('mismatchNewName').value.trim();
        if (!name) { toast('⚠️ Please enter a name for the new profile.'); return; }
        
        // Create profile
        const dob = document.getElementById('f_dob').value;
        try {
            const res = await fetch(`${API_BASE}/profiles/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${state.token}` },
                body: JSON.stringify({ name, dob })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail);
            
            state.profiles.push(data);
            state.activeProfile = data;
            renderProfileSelect();
            closeMismatchModal();
            toast(`Profile created for ${name}! Re-running assessment...`);
            runPrediction(); // Retry
        } catch (e) { toast(`❌ ${e.message}`); }
    };
    document.querySelector('.mismatch-actions').appendChild(btn);
}
