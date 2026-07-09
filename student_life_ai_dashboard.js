// ──────────────────────────────── PREDICTION MODEL ────────────────────────────
function predict(s) {
  const burnout = clamp(Math.round(
    s.stress*7 + s.pressure*4 + (10-s.sleep)*3 + s.backlogs*4 +
    (100-s.att)*0.3 + s.screen*1.5 + (10-s.motivation)*4 +
    s.hostel*3 - s.exercise*2 - s.friends*1.5 - s.study*1 + (7-s.cgpa)*2
  ));
  const placement = clamp(Math.round(
    s.cgpa*6 + s.coding*3 + s.intern*8 + s.proj*3 + s.cert*2 +
    s.att*0.2 + s.motivation*1.5 - s.backlogs*2 + s.study*1
  ));
  const backlogRisk = clamp(Math.round(
    s.backlogs*8 + (100-s.att)*0.4 + (10-s.cgpa)*4 + s.stress*3 +
    (100-s.asn)*0.3 + (8-s.sleep)*2 - s.study*2 - s.motivation*2
  ));
  const loneliness = clamp(Math.round(
    (10-s.friends)*6 + s.hostel*4 + s.stress*2 + s.screen*1.5 -
    s.club*4 - s.exercise*2 + (8-s.sleep)*2
  ));
  const productivity = clamp(Math.round(
    s.study*5 + s.motivation*4 + s.att*0.3 - s.stress*2 -
    s.screen*1.5 + s.exercise*2 + s.cgpa*2
  ));
  return { burnout, placement, backlogRisk, loneliness, productivity };
}
function clamp(v) { return Math.min(100, Math.max(0, v)); }

// ──────────────────────────────── DATA PERSISTENCE ────────────────────────────
function generateStudentID() {
  const maxID = Math.max(...DATA.map(s => parseInt(s.id.replace('STU', '')) || 0), 0);
  return 'STU' + String(maxID + 1).padStart(3, '0');
}

function saveDatasetToStorage() {
  try {
    localStorage.setItem('studentDataset', JSON.stringify(DATA));
  } catch (e) {
    console.warn('Failed to save to localStorage:', e);
  }
}

function loadDatasetFromStorage() {
  try {
    const stored = localStorage.getItem('studentDataset');
    if (stored) {
      const parsed = JSON.parse(stored);
      DATA.length = 0;
      DATA.push(...parsed);
      return true;
    }
  } catch (e) {
    console.warn('Failed to load from localStorage:', e);
  }
  return false;
}

function updateStudentCountDisplay() {
  const count = DATA.length;
  const topbar = document.querySelector('.topbar-right span:not(.live-dot)');
  if (topbar) topbar.textContent = count + ' students · ML v2.1';
  
  const statsDiv = document.getElementById('dataset-stats');
  if (statsDiv) statsDiv.textContent = 'Dataset: ' + count + ' student' + (count !== 1 ? 's' : '');
}

function exportDatasetAsJSON() {
  const json = JSON.stringify(DATA, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'student_data_exported_' + new Date().toISOString().split('T')[0] + '.json';
  a.click();
  URL.revokeObjectURL(url);
}

// ──────────────────────────────── HELPERS ─────────────────────────────────────
let selIdx = 0;
let charts = {};

function sv(id, val) { document.getElementById(id).textContent = val; }

function chipColor(v, invert=false) {
  const low = invert ? '#1e40af' : '#15803d';
  const lowBg = invert ? '#dbeafe' : '#dcfce7';
  const midBg = '#fef9c3'; const midC = '#854d0e';
  const highBg = invert ? '#dcfce7' : '#fee2e2';
  const high = invert ? '#15803d' : '#991b1b';
  if (v < 35) return [lowBg, low];
  if (v < 65) return [midBg, midC];
  return [highBg, high];
}

function chip(v, invert=false) {
  const [bg,c] = chipColor(v, invert);
  return `<span class="chip" style="background:${bg};color:${c}">${v}</span>`;
}

function badgeLabel(v, invert=false) {
  if (invert) return v > 65 ? 'Strong' : v > 40 ? 'Moderate' : 'Weak';
  return v < 35 ? 'Low' : v < 65 ? 'Medium' : 'High';
}
function badgeClass(v, invert=false) {
  if (invert) return v > 65 ? 'badge-blue' : v > 40 ? 'badge-yellow' : 'badge-red';
  return v < 35 ? 'badge-green' : v < 65 ? 'badge-yellow' : 'badge-red';
}

// ──────────────────────────────── PAGE NAV ────────────────────────────────────
function showPage(name, button) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('page-'+name).classList.add('active');
  const target = button || (typeof event !== 'undefined' ? event.currentTarget : null);
  if (target) target.classList.add('active');
  if (name === 'dataset') { renderDSTable(); setTimeout(renderHeatmap, 80); }
  if (name === 'model') setTimeout(renderModelChart, 80);
}

// ──────────────────────────────── DASHBOARD ────────────────────────────────────
function renderPills() {
  const pillsHTML = DATA.map((s,i) =>
    `<button class="pill ${i===selIdx?'active':''}" onclick="selectStudent(${i})">${s.name.split(' ')[0]}</button>`
  ).join('');
  
  // Update pills wherever they exist
  const studentPillsEl = document.getElementById('student-pills');
  if (studentPillsEl) studentPillsEl.innerHTML = pillsHTML;
}

function selectStudent(i) {
  selIdx = i;
  renderPills();
  updateStudentInfoPreview();
  renderStudentReport();
}

function calculateAverageMetrics() {
  if (DATA.length === 0) return null;
  
  const avg = {
    burnout: Math.round(DATA.reduce((sum, s) => sum + s.burnout, 0) / DATA.length),
    placement: Math.round(DATA.reduce((sum, s) => sum + s.placement, 0) / DATA.length),
    backlogRisk: Math.round(DATA.reduce((sum, s) => sum + s.backlogRisk, 0) / DATA.length),
    loneliness: Math.round(DATA.reduce((sum, s) => sum + s.loneliness, 0) / DATA.length),
    productivity: Math.round(DATA.reduce((sum, s) => sum + s.productivity, 0) / DATA.length),
    stress: Math.round(DATA.reduce((sum, s) => sum + s.stress, 0) / DATA.length),
    sleep: parseFloat((DATA.reduce((sum, s) => sum + s.sleep, 0) / DATA.length).toFixed(1)),
    cgpa: parseFloat((DATA.reduce((sum, s) => sum + s.cgpa, 0) / DATA.length).toFixed(2)),
    att: Math.round(DATA.reduce((sum, s) => sum + s.att, 0) / DATA.length),
    study: parseFloat((DATA.reduce((sum, s) => sum + s.study, 0) / DATA.length).toFixed(1)),
    friends: Math.round(DATA.reduce((sum, s) => sum + s.friends, 0) / DATA.length),
    coding: Math.round(DATA.reduce((sum, s) => sum + s.coding, 0) / DATA.length),
  };
  return avg;
}

function renderDetailPage() {
  const s = DATA[selIdx];
  renderStudentReport();
}

function renderStudentReport() {
  const s = DATA[selIdx];
  const reportSection = document.getElementById('student-report-section');
  if (!reportSection) return;
  
  reportSection.style.display = 'block';
  renderDetailMetrics(s);
  renderDetailTrendChart(s);
  renderDetailRadarChart(s);
  reportSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderDetailMetrics(student) {
  const s = student || DATA[selIdx];
  const rows = [
    { lbl:'Burnout risk', val:s.burnout+'%', fill:s.burnout, bar:'#ef4444', invert:false, hint:`Stress ${s.stress}/10 · Sleep ${s.sleep}h/night`, inv:false },
    { lbl:'Placement score', val:s.placement+'%', fill:s.placement, bar:'#3b82f6', hint:`CGPA ${s.cgpa} · Internships ${s.intern}`, inv:true },
    { lbl:'Backlog risk', val:s.backlogRisk+'%', fill:s.backlogRisk, bar:'#f59e0b', hint:`Backlogs ${s.backlogs} · Attendance ${s.att}%`, inv:false },
    { lbl:'Loneliness score', val:s.loneliness+'%', fill:s.loneliness, bar:'#8b5cf6', hint:`Friends ${s.friends} · Clubs ${s.club}`, inv:false },
    { lbl:'Productivity', val:s.productivity+'%', fill:s.productivity, bar:'#22c55e', hint:`Study ${s.study}h/day · Motivation ${s.motivation}/10`, inv:true },
  ];
  document.getElementById('student-detail-metrics').innerHTML = rows.map(r => `
    <div class="metric">
      <div class="metric-top">
        <span class="metric-label">${r.lbl}</span>
        <span class="badge ${badgeClass(r.fill,r.inv)}">${badgeLabel(r.fill,r.inv)}</span>
      </div>
      <div class="metric-val">${r.val}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${r.fill}%;background:${r.bar}"></div></div>
      <div class="metric-hint">${r.hint}</div>
    </div>`).join('');
}

function renderDetailTrendChart(student) {
  const s = student || DATA[selIdx];
  const weeks = [1,2,3,4,5,6,7,8];
  const seed = s.burnout + s.productivity;
  const pseudo = (i) => ((seed * 9301 + i * 49297) % 233280) / 233280;
  const prod = weeks.map((w,i) => clamp(Math.round(s.productivity + (i-3.5)*1.5 + (pseudo(i)*8-4))));
  const study = weeks.map((w,i) => Math.round((s.study + pseudo(i+10)*2 - 1)*10)/10);

  if (charts.detailTrend) charts.detailTrend.destroy();
  charts.detailTrend = new Chart(document.getElementById('student-detail-trendChart'), {
    type: 'line',
    data: {
      labels: weeks.map(w=>'W'+w),
      datasets: [
        { label:'Productivity %', data:prod, borderColor:'#6366f1', backgroundColor:'rgba(99,102,241,0.07)', borderWidth:2.5, tension:0.4, pointRadius:4, pointBackgroundColor:'#6366f1', yAxisID:'y' },
        { label:'Study hrs', data:study, borderColor:'#22c55e', borderDash:[5,3], borderWidth:1.8, tension:0.4, pointRadius:0, yAxisID:'y2' }
      ]
    },
    options: {
      responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{display:false} },
      scales: {
        x:{ ticks:{font:{size:11},color:'#888'}, grid:{color:'rgba(128,128,128,0.08)'} },
        y:{ min:0, max:100, ticks:{font:{size:11},color:'#888'}, grid:{color:'rgba(128,128,128,0.07)'} },
        y2:{ position:'right', min:0, max:14, ticks:{font:{size:10},color:'#22c55e'}, grid:{display:false} }
      }
    }
  });
}

function renderDetailRadarChart(student) {
  const s = student || DATA[selIdx];
  if (charts.detailRadar) charts.detailRadar.destroy();
  charts.detailRadar = new Chart(document.getElementById('student-detail-radarChart'), {
    type: 'radar',
    data: {
      labels:['Productivity','Placement','Sleep','Social','Academic','Career'],
      datasets:[{
        label: s.name,
        data: [
          s.productivity,
          s.placement,
          clamp(Math.round((s.sleep/10)*100)),
          clamp(Math.round(s.friends*6+s.club*7)),
          clamp(Math.round(s.cgpa*10)),
          clamp(Math.round(s.intern*15+s.proj*7+s.cert*6+s.coding*3))
        ],
        borderColor:'#6366f1', backgroundColor:'rgba(99,102,241,0.12)',
        borderWidth:2, pointRadius:4, pointBackgroundColor:'#6366f1'
      }]
    },
    options: {
      responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{display:false} },
      scales:{ r:{ min:0, max:100, ticks:{display:false}, grid:{color:'rgba(128,128,128,0.13)'}, pointLabels:{font:{size:11},color:'#888'} } }
    }
  });
}

function updateStudentInfoPreview() {
  const s = DATA[selIdx];
  const preview = document.getElementById('student-info-preview');
  if (!preview) return;
  
  preview.innerHTML = `
    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px;">
      <div>
        <div style="font-size: 12px; color: var(--text3); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">Name</div>
        <div style="font-size: 15px; font-weight: 700; color: var(--text);">${s.name}</div>
      </div>
      <div>
        <div style="font-size: 12px; color: var(--text3); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">Student ID</div>
        <div style="font-size: 15px; font-weight: 700; color: var(--text); font-family: 'Space Mono', monospace;">${s.id}</div>
      </div>
      <div>
        <div style="font-size: 12px; color: var(--text3); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">Semester</div>
        <div style="font-size: 15px; font-weight: 700; color: var(--text);">${s.sem}</div>
      </div>
      <div>
        <div style="font-size: 12px; color: var(--text3); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">Branch</div>
        <div style="font-size: 15px; font-weight: 700; color: var(--text);">${s.branch}</div>
      </div>
      <div>
        <div style="font-size: 12px; color: var(--text3); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">CGPA</div>
        <div style="font-size: 15px; font-weight: 700; color: var(--text);">${s.cgpa.toFixed(1)}</div>
      </div>
      <div>
        <div style="font-size: 12px; color: var(--text3); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">Attendance</div>
        <div style="font-size: 15px; font-weight: 700; color: var(--text);">${s.att}%</div>
      </div>
    </div>
    <div style="margin-top: 16px; padding: 12px; background: var(--surface2); border-radius: var(--radius-sm); font-size: 12px; color: var(--text2);">
      <strong style="color: var(--text);">View full dashboard →</strong> Click the "Dashboard" tab to see detailed metrics, trends, and AI insights for this student.
    </div>
  `;
}

function renderMetrics() {
  const s = calculateAverageMetrics();
  if (!s) return;
  const rows = [
    { lbl:'Burnout risk', val:s.burnout+'%', fill:s.burnout, bar:'#ef4444', invert:false, hint:`Avg Stress ${s.stress}/10 · Sleep ${s.sleep}h/night`, inv:false },
    { lbl:'Placement score', val:s.placement+'%', fill:s.placement, bar:'#3b82f6', hint:`Avg CGPA ${s.cgpa}`, inv:true },
    { lbl:'Backlog risk', val:s.backlogRisk+'%', fill:s.backlogRisk, bar:'#f59e0b', hint:`Avg Attendance ${s.att}%`, inv:false },
    { lbl:'Loneliness score', val:s.loneliness+'%', fill:s.loneliness, bar:'#8b5cf6', hint:`Avg Friends ${s.friends}`, inv:false },
    { lbl:'Productivity', val:s.productivity+'%', fill:s.productivity, bar:'#22c55e', hint:`Avg Study ${s.study}h/day`, inv:true },
  ];
  document.getElementById('metrics-row').innerHTML = rows.map(r => `
    <div class="metric">
      <div class="metric-top">
        <span class="metric-label">${r.lbl}</span>
        <span class="badge ${badgeClass(r.fill,r.inv)}">${badgeLabel(r.fill,r.inv)}</span>
      </div>
      <div class="metric-val">${r.val}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${r.fill}%;background:${r.bar}"></div></div>
      <div class="metric-hint">${r.hint}</div>
    </div>`).join('');
}

function renderTrend() {
  const s = calculateAverageMetrics();
  if (!s) return;
  const weeks = [1,2,3,4,5,6,7,8];
  const seed = s.burnout + s.productivity;
  const pseudo = (i) => ((seed * 9301 + i * 49297) % 233280) / 233280;
  const prod = weeks.map((w,i) => clamp(Math.round(s.productivity + (i-3.5)*1.5 + (pseudo(i)*8-4))));
  const study = weeks.map((w,i) => Math.round((s.study + pseudo(i+10)*2 - 1)*10)/10);

  if (charts.trend) charts.trend.destroy();
  charts.trend = new Chart(document.getElementById('trendChart'), {
    type: 'line',
    data: {
      labels: weeks.map(w=>'W'+w),
      datasets: [
        { label:'Productivity %', data:prod, borderColor:'#6366f1', backgroundColor:'rgba(99,102,241,0.07)', borderWidth:2.5, tension:0.4, pointRadius:4, pointBackgroundColor:'#6366f1', yAxisID:'y' },
        { label:'Study hrs', data:study, borderColor:'#22c55e', borderDash:[5,3], borderWidth:1.8, tension:0.4, pointRadius:0, yAxisID:'y2' }
      ]
    },
    options: {
      responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{display:false} },
      scales: {
        x:{ ticks:{font:{size:11},color:'#888'}, grid:{color:'rgba(128,128,128,0.08)'} },
        y:{ min:0, max:100, ticks:{font:{size:11},color:'#888'}, grid:{color:'rgba(128,128,128,0.07)'} },
        y2:{ position:'right', min:0, max:14, ticks:{font:{size:10},color:'#22c55e'}, grid:{display:false} }
      }
    }
  });
}

function renderRadar() {
  const s = calculateAverageMetrics();
  if (!s) return;
  if (charts.radar) charts.radar.destroy();
  charts.radar = new Chart(document.getElementById('radarChart'), {
    type: 'radar',
    data: {
      labels:['Productivity','Placement','Sleep','Social','Academic','Career'],
      datasets:[{
        label: 'Dataset Average',
        data: [
          s.productivity,
          s.placement,
          clamp(Math.round((s.sleep/10)*100)),
          clamp(Math.round(s.friends*6)),
          clamp(Math.round(s.cgpa*15)),
          clamp(Math.round(s.coding*8))
        ],
        borderColor:'#6366f1', backgroundColor:'rgba(99,102,241,0.12)',
        borderWidth:2, pointRadius:4, pointBackgroundColor:'#6366f1'
      }]
    },
    options: {
      responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{display:false} },
      scales:{ r:{ min:0, max:100, ticks:{display:false}, grid:{color:'rgba(128,128,128,0.13)'}, pointLabels:{font:{size:11},color:'#888'} } }
    }
  });
}

function renderDist() {
  if (charts.dist) charts.dist.destroy();
  const buckets = [0,0,0,0,0];
  DATA.forEach(s => { buckets[Math.min(4,Math.floor(s.burnout/20))]++; });
  charts.dist = new Chart(document.getElementById('distChart'), {
    type:'bar',
    data:{
      labels:['0–20','20–40','40–60','60–80','80–100'],
      datasets:[{
        label:'Students', data:buckets,
        backgroundColor:['#4ade80','#facc15','#fb923c','#f87171','#ef4444'],
        borderRadius:6, borderWidth:0
      }]
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{display:false} },
      scales:{
        x:{ ticks:{font:{size:12}}, grid:{display:false} },
        y:{ ticks:{stepSize:1,font:{size:11}}, grid:{color:'rgba(128,128,128,0.07)'} }
      }
    }
  });
}

function renderOverviewTable() {
  const sorted = [...DATA].sort((a,b)=>b.burnout-a.burnout);
  document.getElementById('overview-tbody').innerHTML = sorted.map(s => `
    <tr>
      <td style="font-weight:500">${s.name}</td>
      <td>Sem ${s.sem}</td>
      <td>${s.branch}</td>
      <td>${chip(s.burnout)}</td>
      <td>${chip(s.placement,true)}</td>
      <td>${chip(s.backlogRisk)}</td>
      <td>${chip(s.loneliness)}</td>
      <td>${chip(s.productivity,true)}</td>
    </tr>`).join('');
}

// ──────────────────────────────── FORM ────────────────────────────────────────
function runFormPrediction() {
  const name = document.getElementById('f_name').value.trim() || 'Student';
  const sid = document.getElementById('f_sid').value.trim() || generateStudentID();
  const sem = parseInt(document.getElementById('f_sem').value);
  const branch = document.getElementById('f_branch').value;
  
  const s = {
    id: sid,
    name: name,
    sem: sem,
    branch: branch,
    cgpa: parseFloat(document.getElementById('v_cgpa').textContent),
    att: parseInt(document.getElementById('v_att').textContent),
    backlogs: parseInt(document.getElementById('v_bl').textContent),
    asn: parseInt(document.getElementById('v_asn').textContent),
    study: parseFloat(document.getElementById('v_study').textContent),
    sleep: parseFloat(document.getElementById('v_sleep').textContent),
    screen: parseFloat(document.getElementById('v_screen').textContent),
    exercise: parseInt(document.getElementById('v_ex').textContent),
    friends: parseInt(document.getElementById('v_friends').textContent),
    hostel: parseInt(document.getElementById('f_hostel').value),
    stress: parseInt(document.getElementById('v_stress').textContent),
    pressure: parseInt(document.getElementById('v_pressure').textContent),
    motivation: parseInt(document.getElementById('v_mot').textContent),
    club: parseInt(document.getElementById('v_club').textContent),
    intern: parseInt(document.getElementById('v_intern').textContent),
    proj: parseInt(document.getElementById('v_proj').textContent),
    cert: parseInt(document.getElementById('v_cert').textContent),
    coding: parseInt(document.getElementById('v_code').textContent),
  };
  
  // Run preprocessing (prediction) on the student
  const p = predict(s);
  s.burnout = p.burnout;
  s.placement = p.placement;
  s.backlogRisk = p.backlogRisk;
  s.loneliness = p.loneliness;
  s.productivity = p.productivity;
  
  // Add to dataset and save
  DATA.push(s);
  saveDatasetToStorage();
  
  // Find the index of the newly added student
  selIdx = DATA.length - 1;
  
  document.getElementById('pred-name-out').textContent = name + ' (saved to dataset)';

  const items = [
    { lbl:'Burnout risk', val:p.burnout+'%', c:'#ef4444', inv:false },
    { lbl:'Placement score', val:p.placement+'%', c:'#3b82f6', inv:true },
    { lbl:'Backlog risk', val:p.backlogRisk+'%', c:'#f59e0b', inv:false },
    { lbl:'Loneliness', val:p.loneliness+'%', c:'#8b5cf6', inv:false },
    { lbl:'Productivity', val:p.productivity+'%', c:'#22c55e', inv:true },
  ];

  const numVals = [p.burnout, p.placement, p.backlogRisk, p.loneliness, p.productivity];
  document.getElementById('pred-result-grid').innerHTML = items.map((item,i) => {
    const [bg,tc] = chipColor(numVals[i], item.inv);
    return `<div class="result-item" style="background:${bg}20">
      <div class="result-item-lbl">${item.lbl}</div>
      <div class="result-item-val" style="color:${tc}">${item.val}</div>
    </div>`;
  }).join('');

  const advices = [];
  if (p.burnout > 65) advices.push('🔴 High burnout detected — recommend counselling sessions and workload adjustment.');
  else if (p.burnout > 40) advices.push('🟡 Moderate burnout risk — encourage stress management techniques.');
  if (p.backlogRisk > 65) advices.push('🔴 Backlog risk is high — academic mentorship and structured study plan needed.');
  if (p.loneliness > 65) advices.push('🟠 Social isolation detected — encourage club participation and peer interaction.');
  if (p.placement < 40) advices.push('🟡 Placement readiness is low — focus on internships, projects, and coding practice.');
  if (p.productivity < 40) advices.push('🔴 Low productivity — review daily schedule, reduce screen time, improve sleep.');
  if (advices.length === 0) advices.push('✅ Student is performing well across all dimensions. Keep up the great work!');

  document.getElementById('pred-advice').innerHTML =
    `<strong>AI recommendations:</strong><br>${advices.join('<br>')}`;

  const box = document.getElementById('form-result');
  box.classList.add('show');
  box.scrollIntoView({ behavior:'smooth', block:'nearest' });
  
  // Update UI to reflect new student
  updateStudentCountDisplay();
  renderPills();
  renderMetrics();
  
  // Clear form after 2 seconds for next entry
  setTimeout(() => resetStudentForm(), 2000);
}

function resetStudentForm() {
  document.getElementById('f_name').value = '';
  document.getElementById('f_sid').value = '';
  document.getElementById('f_sem').value = '1';
  document.getElementById('f_branch').value = 'Computer Science';
  document.getElementById('v_cgpa').textContent = '7.5';
  document.getElementById('v_att').textContent = '75';
  document.getElementById('v_bl').textContent = '1';
  document.getElementById('v_asn').textContent = '80';
  document.getElementById('v_study').textContent = '4.0';
  document.getElementById('v_sleep').textContent = '6.0';
  document.getElementById('v_screen').textContent = '5.0';
  document.getElementById('v_ex').textContent = '2';
  document.getElementById('v_friends').textContent = '3';
  document.getElementById('f_hostel').value = '1';
  document.getElementById('v_stress').textContent = '5';
  document.getElementById('v_pressure').textContent = '5';
  document.getElementById('v_mot').textContent = '6';
  document.getElementById('v_club').textContent = '1';
  document.getElementById('v_intern').textContent = '0';
  document.getElementById('v_proj').textContent = '1';
  document.getElementById('v_cert').textContent = '0';
  document.getElementById('v_code').textContent = '5';
}

// ──────────────────────────────── DATASET ─────────────────────────────────────
function renderDSTable(filter='') {
  const rows = filter
    ? DATA.filter(s => s.name.toLowerCase().includes(filter.toLowerCase()) || s.id.includes(filter))
    : DATA;
  document.getElementById('ds-tbody').innerHTML = rows.map(s => `
    <tr>
      <td style="font-family:'Space Mono',monospace;font-size:11px;color:var(--text3)">${s.id}</td>
      <td style="font-weight:500">${s.name}</td>
      <td>${s.sem}</td><td>${s.cgpa.toFixed(1)}</td><td>${s.att}%</td>
      <td>${s.study}</td><td>${s.sleep}</td><td>${s.stress}/10</td>
      <td>${s.friends}</td><td>${s.backlogs}</td><td>${s.intern}</td><td>${s.coding}/10</td>
      <td>${chip(s.burnout)}</td><td>${chip(s.placement,true)}</td>
      <td>${chip(s.backlogRisk)}</td><td>${chip(s.loneliness)}</td>
      <td>${chip(s.productivity,true)}</td>
    </tr>`).join('');
}
function filterDS(v) { renderDSTable(v); }

function renderHeatmap() {
  if (charts.heat) charts.heat.destroy();
  const features = ['CGPA','Attendance','Sleep','Study hrs','Stress','Backlogs','Friends','Exercise','Screen','Coding'];
  const targets = ['Burnout','Placement','Backlog','Loneliness','Productivity'];
  const imp = [
    [15, 8, 18, 10, 28, 15, 12, 10, 14, 5],
    [30, 12, 5, 10, 5, 12, 8, 5, 4, 35],
    [20, 22, 12, 18, 15, 30, 5, 5, 5, 8],
    [5, 4, 12, 5, 15, 5, 40, 12, 18, 4],
    [12, 12, 8, 28, 18, 6, 8, 12, 20, 10],
  ];
  const data = [];
  const colors = [];
  for (let t=0;t<targets.length;t++) for (let f=0;f<features.length;f++) {
    const v = imp[t][f];
    data.push({ x:f, y:t, v });
    const a = v/40;
    colors.push(`rgba(99,102,241,${a.toFixed(2)})`);
  }
  charts.heat = new Chart(document.getElementById('heatChart'), {
    type:'scatter',
    data:{ datasets:[{ data: data.map(d=>({x:d.x,y:d.y,v:d.v})), pointRadius:22, pointStyle:'rect', backgroundColor: colors }] },
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{
        legend:{display:false},
        tooltip:{ callbacks:{ label: ctx => `${targets[ctx.raw.y]} ← ${features[ctx.raw.x]}: ${ctx.raw.v}%` } }
      },
      scales:{
        x:{ min:-0.5, max:9.5, ticks:{ callback:v=>features[v]||'', stepSize:1, font:{size:10} }, grid:{display:false} },
        y:{ min:-0.5, max:4.5, ticks:{ callback:v=>targets[v]||'', stepSize:1, font:{size:11} }, grid:{display:false} }
      },
    },
    plugins:[{
      id:'heatLabels',
      afterDraw(chart) {
        const ctx2 = chart.ctx;
        chart.data.datasets[0].data.forEach((d,i) => {
          const meta = chart.getDatasetMeta(0);
          const pt = meta.data[i];
          if (!pt) return;
          ctx2.fillStyle = d.v > 20 ? '#fff' : '#6366f1';
          ctx2.font = '600 10px DM Sans';
          ctx2.textAlign = 'center'; ctx2.textBaseline = 'middle';
          ctx2.fillText(d.v+'%', pt.x, pt.y);
        });
      }
    }]
  });
}

function renderModelChart() {
  if (charts.model) charts.model.destroy();
  charts.model = new Chart(document.getElementById('modelChart'), {
    type:'bar',
    data:{
      labels:['Stress','Sleep','Motivation','Backlogs','CGPA','Coding','Internships','Friends','Exercise','Screen time'],
      datasets:[
        { label:'Burnout',     data:[28,18,15,15,10,0,0,12,10,14], backgroundColor:'rgba(239,68,68,0.7)', borderRadius:3 },
        { label:'Placement',   data:[0,5,10,12,30,35,20,8,5,4], backgroundColor:'rgba(59,130,246,0.7)', borderRadius:3 },
        { label:'Productivity',data:[18,8,25,6,12,10,0,8,12,20], backgroundColor:'rgba(34,197,94,0.7)', borderRadius:3 },
      ]
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{
        legend:{
          display:true,
          labels:{ font:{size:11}, boxWidth:10, boxHeight:10, usePointStyle:false }
        }
      },
      scales:{
        x:{ ticks:{font:{size:10}}, grid:{display:false} },
        y:{ ticks:{font:{size:11}}, grid:{color:'rgba(128,128,128,0.07)'}, title:{display:true,text:'Feature weight (%)',font:{size:11}} }
      }
    }
  });
}

function downloadCSV() {
  const headers = ['id','name','sem','branch','cgpa','att','backlogs','asn','study','sleep','screen','exercise','friends','hostel','stress','pressure','motivation','club','intern','proj','cert','coding','burnout','placement','backlogRisk','loneliness','productivity'];
  const rows = DATA.map(s => headers.map(h => s[h] ?? '').join(','));
  const csv = [headers.join(','), ...rows].join('\n');
  const a = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(new Blob([csv],{type:'text/csv'})),
    download: 'student_life_dataset.csv'
  });
  a.click(); URL.revokeObjectURL(a.href);
}

renderPills();
renderMetrics();
renderOverviewTable();
renderDist();
setTimeout(() => { renderTrend(); renderRadar(); }, 150);
