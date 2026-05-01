#!/usr/bin/env python3
"""
Simple Flask dashboard for google-maps-scraper.
Upload queries, monitor jobs, download results.
"""

import csv
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template_string, request, send_file, url_for
from campaigns import get_campaign_names, get_campaign

app = Flask(__name__)

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

import sys as _sys
_default_bin = "../google-maps-scraper.exe" if _sys.platform == "win32" else "../google-maps-scraper"
BINARY = os.environ.get("SCRAPER_BINARY", _default_bin)
KEEP_COLS = ["title", "category", "address", "website", "phone", "emails"]

# In-memory job store: { job_id: { status, query, output, log, started_at } }
jobs: dict = {}
jobs_lock = threading.Lock()

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Maps Scraper Dashboard</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #f5f5f5; color: #222; }
  header { background: #1a73e8; color: #fff; padding: 16px 32px; }
  header h1 { font-size: 1.4rem; }
  main { max-width: 1000px; margin: 32px auto; padding: 0 16px; }
  .card { background: #fff; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.1); padding: 24px; margin-bottom: 24px; }
  h2 { font-size: 1rem; font-weight: 600; margin-bottom: 16px; color: #444; }
  textarea { width: 100%; height: 120px; border: 1px solid #ddd; border-radius: 4px; padding: 8px; font-size: .9rem; resize: vertical; }
  .row { display: flex; gap: 12px; align-items: center; margin-top: 12px; flex-wrap: wrap; }
  label { font-size: .85rem; display: flex; align-items: center; gap: 6px; }
  button { background: #1a73e8; color: #fff; border: none; border-radius: 4px; padding: 10px 20px; cursor: pointer; font-size: .9rem; }
  button:hover { background: #1558b0; }
  button.danger { background: #d93025; }
  .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }
  .stat { background: #e8f0fe; border-radius: 6px; padding: 16px; text-align: center; }
  .stat .num { font-size: 2rem; font-weight: 700; color: #1a73e8; }
  .stat .lbl { font-size: .8rem; color: #555; margin-top: 4px; }
  table { width: 100%; border-collapse: collapse; font-size: .85rem; }
  th { background: #f0f0f0; padding: 8px 12px; text-align: left; font-weight: 600; }
  td { padding: 8px 12px; border-bottom: 1px solid #eee; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: .75rem; font-weight: 600; }
  .tabs { display: flex; gap: 4px; margin-bottom: 24px; }
  .tab { padding: 8px 20px; border-radius: 6px 6px 0 0; cursor: pointer; font-size: .9rem; background: #ddd; border: none; }
  .tab.active { background: #1a73e8; color: #fff; }
  .tab-panel { display: none; }
  .tab-panel.active { display: block; }
  .campaign-card { border: 1px solid #ddd; border-radius: 6px; padding: 16px; margin-bottom: 12px; }
  .campaign-card h3 { font-size: .95rem; margin-bottom: 6px; }
  .goal-badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: .75rem; font-weight: 600; margin-bottom: 8px; }
  .goal-badge.website_sales   { background: #d4edda; color: #155724; }
  .goal-badge.hidden_job_market { background: #cce5ff; color: #004085; }
  .goal-badge.custom          { background: #e2e3e5; color: #383d41; }
  .batch-list { font-size: .8rem; color: #666; margin: 8px 0; }
  .badge.running { background: #fff3cd; color: #856404; }
  .badge.done    { background: #d4edda; color: #155724; }
  .badge.error   { background: #f8d7da; color: #721c24; }
  .badge.queued  { background: #e2e3e5; color: #383d41; }
  a.dl { color: #1a73e8; text-decoration: none; font-size: .85rem; }
  a.dl:hover { text-decoration: underline; }
  #log { background: #1e1e1e; color: #d4d4d4; font-family: monospace; font-size: .8rem; padding: 12px; border-radius: 4px; height: 200px; overflow-y: auto; white-space: pre-wrap; }
</style>
</head>
<body>
<header><h1>Maps Scraper Dashboard</h1></header>
<main>

  <!-- Tabs -->
  <div class="tabs">
    <button class="tab active" onclick="showTab('manual')">Manual Scrape</button>
    <button class="tab" onclick="showTab('campaigns')">Campaigns</button>
    <button class="tab" onclick="showTab('results')">Results</button>
  </div>

  <div id="tab-manual" class="tab-panel active">

  <!-- Stats -->
  <div class="card">
    <h2>Overview</h2>
    <div class="stats" id="stats">
      <div class="stat"><div class="num" id="s-total">0</div><div class="lbl">Total Results</div></div>
      <div class="stat"><div class="num" id="s-email">0</div><div class="lbl">With Email</div></div>
      <div class="stat"><div class="num" id="s-phone">0</div><div class="lbl">With Phone</div></div>
      <div class="stat"><div class="num" id="s-web">0</div><div class="lbl">With Website</div></div>
      <div class="stat"><div class="num" id="s-jobs">0</div><div class="lbl">Jobs Run</div></div>
    </div>
  </div>

  <!-- Submit -->
  <div class="card">
    <h2>New Scrape Job</h2>
    <textarea id="queries" placeholder="One query per line&#10;staffing agencies in Kitchener Ontario&#10;restaurants in Toronto Ontario"></textarea>

    <div class="row" style="margin-top:14px">
      <label><input type="checkbox" id="use-grid"> Grid mode (more results)</label>
    </div>
    <div id="grid-opts" style="display:none;margin-top:10px;padding:12px;background:#f8f8f8;border-radius:6px;font-size:.85rem">
      <p style="margin-bottom:8px;color:#555">Grid splits city into zones → scrapes each → more unique results.</p>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
        <label>Min Lat<br><input type="text" id="g-minlat" value="43.37" style="width:100%;padding:4px;border:1px solid #ddd;border-radius:4px"></label>
        <label>Min Lon<br><input type="text" id="g-minlon" value="-80.57" style="width:100%;padding:4px;border:1px solid #ddd;border-radius:4px"></label>
        <label>Max Lat<br><input type="text" id="g-maxlat" value="43.47" style="width:100%;padding:4px;border:1px solid #ddd;border-radius:4px"></label>
        <label>Max Lon<br><input type="text" id="g-maxlon" value="-80.44" style="width:100%;padding:4px;border:1px solid #ddd;border-radius:4px"></label>
      </div>
      <label style="margin-top:8px;display:block">Cell size (km) — smaller = more zones = more results (slower)
        <input type="number" id="g-cell" value="1" min="0.5" max="10" step="0.5" style="width:80px;margin-left:8px;padding:4px;border:1px solid #ddd;border-radius:4px">
      </label>
      <p style="margin-top:8px;color:#888">KWC defaults pre-filled. <a href="https://boundingbox.klokantech.com/" target="_blank" style="color:#1a73e8">Get bbox for other cities →</a></p>
    </div>

    <div class="row" style="margin-top:12px">
      <label><input type="checkbox" id="req-email"> Require email</label>
      <label><input type="checkbox" id="req-phone"> Require phone</label>
      <label><input type="checkbox" id="req-web"> Require website</label>
      <button onclick="submitJob()">Run Scraper</button>
    </div>
  </div>

  <!-- Jobs -->
  <div class="card">
    <h2>Jobs</h2>
    <table>
      <thead><tr><th>ID</th><th>Query</th><th>Status</th><th>Started</th><th>Results</th><th>Download</th></tr></thead>
      <tbody id="jobs-tbody"></tbody>
    </table>
  </div>

  <!-- Log -->
  <div class="card">
    <h2>Log <small id="log-job" style="color:#888;font-weight:400"></small></h2>
    <div id="log">Click a job row to see log…</div>
  </div>

  <!-- Master download -->
  <div class="card">
    <h2>Master CSV</h2>
    <p style="font-size:.9rem;color:#555;margin-bottom:12px">Combined deduplicated output from all completed jobs.</p>
    <a class="dl" href="/download/master">Download master.csv</a>
    &nbsp;
    <button onclick="buildMaster()">Rebuild Now</button>
    <span id="master-msg" style="margin-left:12px;font-size:.85rem;color:#555"></span>
  </div>

  </div><!-- end tab-manual -->

  <!-- CAMPAIGNS TAB -->
  <div id="tab-campaigns" class="tab-panel" style="display:none">
    <div class="card">
      <h2>Campaign Templates</h2>
      <p style="font-size:.85rem;color:#555;margin-bottom:16px">
        Pre-built query sets targeting 1000+ results. Each campaign is split into batches (~200-300 results each).
        Run all batches → Rebuild Master → download clean CSV.
      </p>
      <div id="campaign-list">Loading…</div>
    </div>
    <div class="card" id="campaign-detail" style="display:none">
      <h2 id="cd-title"></h2>
      <p id="cd-desc" style="font-size:.85rem;color:#555;margin-bottom:12px"></p>
      <div id="cd-batches"></div>
      <div class="row" style="margin-top:16px">
        <label><input type="checkbox" id="cd-req-email"> Require email</label>
        <label><input type="checkbox" id="cd-req-phone"> Require phone</label>
        <label><input type="checkbox" id="cd-req-web"> Require website (for website sales)</label>
        <label><input type="checkbox" id="cd-no-web"> NO website (pitch web design)</label>
      </div>
      <div class="row" style="margin-top:12px">
        <button onclick="runAllBatches()">Run All Batches</button>
        <button onclick="runBatch(selectedBatch)" style="background:#28a745">Run Selected Batch</button>
      </div>
    </div>
  </div>

  <!-- RESULTS TAB -->
  <div id="tab-results" class="tab-panel" style="display:none">
    <div class="card">
      <h2>Results Browser</h2>
      <div class="row" style="margin-bottom:12px">
        <select id="res-job" onchange="loadResults()" style="padding:6px;border:1px solid #ddd;border-radius:4px;flex:1">
          <option value="master">Master CSV (all jobs combined)</option>
        </select>
        <button onclick="buildMaster();setTimeout(loadResults,1000)">Rebuild Master</button>
      </div>
      <div id="res-stats" style="font-size:.85rem;color:#555;margin-bottom:12px"></div>
      <div style="overflow-x:auto">
        <table id="res-table">
          <thead><tr><th>Title</th><th>Category</th><th>Address</th><th>Website</th><th>Phone</th><th>Email</th></tr></thead>
          <tbody id="res-tbody"></tbody>
        </table>
      </div>
      <p style="font-size:.8rem;color:#aaa;margin-top:8px">Showing first 200 rows. Download CSV for full list.</p>
    </div>
  </div>

</main>
<script>
let selectedJob = null;
let selectedCampaign = null;
let selectedBatch = null;
let campaignData = {};

// ── Tab switching ──
function showTab(name) {
  document.querySelectorAll('.tab').forEach((t,i) => t.classList.toggle('active', ['manual','campaigns','results'][i] === name));
  ['manual','campaigns','results'].forEach(n => {
    const el = document.getElementById('tab-' + n);
    if (el) el.style.display = n === name ? 'block' : 'none';
  });
  // stats + jobs always visible
  if (name === 'campaigns') loadCampaigns();
  if (name === 'results') { populateJobSelect(); loadResults(); }
}

// ── Campaigns ──
async function loadCampaigns() {
  const res = await fetch('/api/campaigns');
  const data = await res.json();
  campaignData = {};
  const el = document.getElementById('campaign-list');
  el.innerHTML = '';
  data.forEach(c => {
    campaignData[c.id] = c;
    const goalLabels = { website_sales: '🌐 Website Sales', hidden_job_market: '🤝 Hidden Job Market', custom: 'Custom' };
    const div = document.createElement('div');
    div.className = 'campaign-card';
    div.innerHTML = `
      <h3>${c.label}</h3>
      <span class="goal-badge ${c.goal}">${goalLabels[c.goal] || c.goal}</span>
      <div class="batch-list">${c.batch_count} batches · ~${c.batch_count * 200}–${c.batch_count * 300} expected results</div>
      <button onclick="selectCampaign('${c.id}')" style="margin-top:8px;padding:6px 14px;font-size:.85rem">Select →</button>
    `;
    el.appendChild(div);
  });
}

async function selectCampaign(id) {
  selectedCampaign = id;
  selectedBatch = 0;
  const res = await fetch('/api/campaigns/' + id);
  const c = await res.json();
  document.getElementById('campaign-detail').style.display = 'block';
  document.getElementById('cd-title').textContent = c.label;
  const goalDesc = {
    website_sales: 'Target businesses with NO website — pitch web design services.',
    hidden_job_market: 'Target businesses not on job boards — pitch staffing/recruitment.',
    custom: 'Custom campaign.',
  };
  document.getElementById('cd-desc').textContent = goalDesc[c.goal] || '';

  // Pre-check filters by goal
  document.getElementById('cd-no-web').checked = c.goal === 'website_sales';
  document.getElementById('cd-req-phone').checked = c.goal === 'hidden_job_market';

  const bDiv = document.getElementById('cd-batches');
  bDiv.innerHTML = '<p style="font-size:.85rem;font-weight:600;margin-bottom:8px">Batches (click to select):</p>';
  c.batches.forEach((batch, i) => {
    const div = document.createElement('div');
    div.id = 'batch-' + i;
    div.style = 'padding:8px 12px;border:2px solid ' + (i===0?'#1a73e8':'#ddd') + ';border-radius:4px;margin-bottom:6px;cursor:pointer;font-size:.82rem;';
    div.innerHTML = `<strong>Batch ${i+1}</strong>: ${batch.slice(0,2).join(', ')}${batch.length>2?' …':''}`;
    div.onclick = () => {
      selectedBatch = i;
      document.querySelectorAll('[id^=batch-]').forEach(el => el.style.borderColor = '#ddd');
      div.style.borderColor = '#1a73e8';
    };
    bDiv.appendChild(div);
  });
}

function getFilterParams(prefix='cd-') {
  return {
    require_email:   document.getElementById(prefix+'req-email')?.checked || false,
    require_phone:   document.getElementById(prefix+'req-phone')?.checked || false,
    require_website: document.getElementById(prefix+'req-web')?.checked || false,
    no_website:      document.getElementById(prefix+'no-web')?.checked || false,
  };
}

async function runBatch(batchIdx) {
  if (!selectedCampaign) return alert('Select a campaign first.');
  const res = await fetch('/api/campaigns/' + selectedCampaign);
  const c = await res.json();
  const batch = c.batches[batchIdx];
  const body = {
    queries: batch,
    grid: { ...c.bbox, cell: c.cell },
    ...getFilterParams('cd-'),
  };
  const r = await fetch('/api/jobs', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
  const data = await r.json();
  alert(`Batch ${batchIdx+1} started: ${data.job_id}`);
  showTab('manual');
}

async function runAllBatches() {
  if (!selectedCampaign) return alert('Select a campaign first.');
  const res = await fetch('/api/campaigns/' + selectedCampaign);
  const c = await res.json();
  for (let i = 0; i < c.batches.length; i++) {
    const body = {
      queries: c.batches[i],
      grid: { ...c.bbox, cell: c.cell },
      ...getFilterParams('cd-'),
    };
    await fetch('/api/jobs', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
    await new Promise(r => setTimeout(r, 500));
  }
  alert(`All ${c.batches.length} batches queued!`);
  showTab('manual');
}

// ── Results browser ──
async function populateJobSelect() {
  const res = await fetch('/api/jobs');
  const jobs = await res.json();
  const sel = document.getElementById('res-job');
  sel.innerHTML = '<option value="master">Master CSV (all jobs combined)</option>';
  jobs.slice().reverse().forEach(j => {
    if (j.status === 'done') {
      const opt = document.createElement('option');
      opt.value = j.job_id;
      opt.textContent = `${j.query} (${j.result_count} results)`;
      sel.appendChild(opt);
    }
  });
}

async function loadResults() {
  const jobId = document.getElementById('res-job')?.value || 'master';
  const res = await fetch('/api/preview/' + jobId);
  if (!res.ok) { document.getElementById('res-tbody').innerHTML = '<tr><td colspan=6>No data yet.</td></tr>'; return; }
  const data = await res.json();
  document.getElementById('res-stats').textContent =
    `${data.total} total · ${data.with_email} with email · ${data.with_phone} with phone · ${data.no_website} no website`;
  const tbody = document.getElementById('res-tbody');
  tbody.innerHTML = '';
  data.rows.forEach(r => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${escHtml(r.title||'')}</td>
      <td>${escHtml(r.category||'')}</td>
      <td>${escHtml(r.address||'')}</td>
      <td>${r.website ? '<a href="'+escHtml(r.website)+'" target="_blank" style="color:#1a73e8">'+escHtml(r.website.replace(/^https?:\/\//,'').slice(0,30))+'</a>' : '<span style="color:#d93025">None</span>'}</td>
      <td>${escHtml(r.phone||'')}</td>
      <td style="color:${r.emails?'#155724':'#aaa'}">${escHtml(r.emails||'-')}</td>
    `;
    tbody.appendChild(tr);
  });
}

document.getElementById('use-grid').addEventListener('change', function() {
  document.getElementById('grid-opts').style.display = this.checked ? 'block' : 'none';
});

async function submitJob() {
  const lines = document.getElementById('queries').value.trim().split('\\n').map(s => s.trim()).filter(Boolean);
  if (!lines.length) return alert('Enter at least one query.');
  const useGrid = document.getElementById('use-grid').checked;
  const body = {
    queries: lines,
    require_email: document.getElementById('req-email').checked,
    require_phone: document.getElementById('req-phone').checked,
    require_website: document.getElementById('req-web').checked,
    grid: useGrid ? {
      min_lat: document.getElementById('g-minlat').value,
      min_lon: document.getElementById('g-minlon').value,
      max_lat: document.getElementById('g-maxlat').value,
      max_lon: document.getElementById('g-maxlon').value,
      cell:    document.getElementById('g-cell').value,
    } : null,
  };
  const res = await fetch('/api/jobs', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
  const data = await res.json();
  alert('Job started: ' + data.job_id);
  refresh();
}

async function refresh() {
  const [jobsRes, statsRes] = await Promise.all([fetch('/api/jobs'), fetch('/api/stats')]);
  const jobsData = await jobsRes.json();
  const statsData = await statsRes.json();

  // stats
  document.getElementById('s-total').textContent = statsData.total;
  document.getElementById('s-email').textContent = statsData.with_email;
  document.getElementById('s-phone').textContent = statsData.with_phone;
  document.getElementById('s-web').textContent = statsData.with_website;
  document.getElementById('s-jobs').textContent = jobsData.length;

  // jobs table
  const tbody = document.getElementById('jobs-tbody');
  tbody.innerHTML = '';
  jobsData.slice().reverse().forEach(j => {
    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    tr.onclick = () => showLog(j.job_id);
    tr.innerHTML = `
      <td style="font-family:monospace;font-size:.75rem">${j.job_id.slice(0,8)}</td>
      <td>${escHtml(j.query)}</td>
      <td><span class="badge ${j.status}">${j.status}</span></td>
      <td>${j.started_at}</td>
      <td>${j.result_count ?? '-'}</td>
      <td>${j.status === 'done' ? '<a class="dl" href="/download/'+j.job_id+'">CSV</a>' : '-'}</td>
    `;
    tbody.appendChild(tr);
  });

  // refresh log if selected
  if (selectedJob) showLog(selectedJob);
}

async function showLog(jobId) {
  selectedJob = jobId;
  const res = await fetch('/api/jobs/' + jobId);
  const j = await res.json();
  document.getElementById('log-job').textContent = '— ' + j.query;
  const el = document.getElementById('log');
  el.textContent = j.log || '(no output yet)';
  el.scrollTop = el.scrollHeight;
}

async function buildMaster() {
  const res = await fetch('/api/master', { method: 'POST' });
  const data = await res.json();
  document.getElementById('master-msg').textContent = data.message;
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

refresh();
setInterval(refresh, 4000);
</script>
</body>
</html>
"""


# ── helpers ──────────────────────────────────────────────────────────────────

def read_csv_slim(path):
    rows = []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append({col: row.get(col, "") for col in KEEP_COLS})
    except Exception:
        pass
    return rows


def dedup(rows):
    seen_phones, seen_ta = set(), set()
    out = []
    for row in rows:
        phone = re.sub(r"\D", "", row.get("phone", ""))
        ta = (row.get("title", "").lower().strip(), row.get("address", "").lower().strip())
        if phone and phone in seen_phones:
            continue
        if ta in seen_ta:
            continue
        if phone:
            seen_phones.add(phone)
        seen_ta.add(ta)
        out.append(row)
    return out


def apply_filters(rows, require_email=False, require_phone=False, require_website=False, no_website=False):
    if require_email:
        rows = [r for r in rows if r.get("emails", "").strip()]
    if require_phone:
        rows = [r for r in rows if r.get("phone", "").strip()]
    if require_website:
        rows = [r for r in rows if r.get("website", "").strip()]
    if no_website:
        rows = [r for r in rows if not r.get("website", "").strip()]
    return rows


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=KEEP_COLS)
        writer.writeheader()
        writer.writerows(rows)


def stats_from_master():
    master = RESULTS_DIR / "master.csv"
    if not master.exists():
        return {"total": 0, "with_email": 0, "with_phone": 0, "with_website": 0}
    rows = read_csv_slim(master)
    return {
        "total": len(rows),
        "with_email": sum(1 for r in rows if r.get("emails", "").strip()),
        "with_phone": sum(1 for r in rows if r.get("phone", "").strip()),
        "with_website": sum(1 for r in rows if r.get("website", "").strip()),
    }


def run_job(job_id, query, require_email, require_phone, require_website):
    out_csv = RESULTS_DIR / f"job_{job_id}.csv"
    log_lines = []

    def log(msg):
        log_lines.append(msg)
        with jobs_lock:
            jobs[job_id]["log"] = "\n".join(log_lines)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as qf:
        qf.write(query + "\n")
        query_file = qf.name

    cmd = [BINARY, "-input", query_file, "-results", str(out_csv), "-email"]
    log(f"$ {' '.join(cmd)}")

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            log(line.rstrip())
        proc.wait()
        os.unlink(query_file)

        rows = read_csv_slim(out_csv) if out_csv.exists() else []
        rows = apply_filters(rows, require_email, require_phone, require_website)
        write_csv(rows, out_csv)

        with jobs_lock:
            jobs[job_id]["status"] = "done"
            jobs[job_id]["result_count"] = len(rows)
        log(f"\nDone. {len(rows)} results.")
    except Exception as e:
        os.unlink(query_file) if os.path.exists(query_file) else None
        with jobs_lock:
            jobs[job_id]["status"] = "error"
        log(f"\nERROR: {e}")


# ── routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def index():
    return render_template_string(HTML)


@app.post("/api/jobs")
def create_job():
    body = request.json or {}
    queries = body.get("queries", [])
    require_email = body.get("require_email", False)
    require_phone = body.get("require_phone", False)
    require_website = body.get("require_website", False)
    no_website = body.get("no_website", False)
    grid = body.get("grid")  # None or {min_lat, min_lon, max_lat, max_lon, cell}

    if not queries:
        return jsonify({"error": "no queries"}), 400

    # Run all queries as one combined job (sequential in background thread)
    job_id = uuid.uuid4().hex[:12]
    mode = "grid" if grid else "normal"
    label = queries[0] if len(queries) == 1 else f"{queries[0]} (+{len(queries)-1} more)"
    if grid:
        label = f"[GRID] {label}"

    with jobs_lock:
        jobs[job_id] = {
            "job_id": job_id,
            "query": label,
            "status": "running",
            "started_at": time.strftime("%H:%M:%S"),
            "log": "",
            "result_count": None,
        }

    def run_all():
        all_rows = []
        for q in queries:
            jid_tmp = uuid.uuid4().hex[:8]
            tmp_csv = RESULTS_DIR / f"tmp_{jid_tmp}.csv"
            log_lines = []

            def log(msg, ll=log_lines):
                ll.append(msg)
                with jobs_lock:
                    jobs[job_id]["log"] = "\n".join(ll)

            if grid:
                # Grid mode: no input file, use bbox flags
                bbox = f"{grid['min_lat']},{grid['min_lon']},{grid['max_lat']},{grid['max_lon']}"
                cmd = [
                    BINARY,
                    "-results", str(tmp_csv),
                    "-email",
                    "-grid-bbox", bbox,
                    "-grid-cell", str(grid["cell"]),
                ]
                # Append query as extra search term via input file
                with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as qf:
                    qf.write(q + "\n")
                    qfile = qf.name
                cmd += ["-input", qfile]
            else:
                with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as qf:
                    qf.write(q + "\n")
                    qfile = qf.name
                cmd = [BINARY, "-input", qfile, "-results", str(tmp_csv), "-email"]

            log(f"\n--- {q} ---\n$ {' '.join(cmd)}")
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in proc.stdout:
                    log(line.rstrip())
                proc.wait()
            except Exception as e:
                log(f"ERROR: {e}")
            finally:
                if os.path.exists(qfile):
                    os.unlink(qfile)

            rows = read_csv_slim(tmp_csv) if tmp_csv.exists() else []
            all_rows.extend(rows)
            if tmp_csv.exists():
                tmp_csv.unlink()

        all_rows = dedup(all_rows)
        all_rows = apply_filters(all_rows, require_email, require_phone, require_website, no_website)
        out = RESULTS_DIR / f"job_{job_id}.csv"
        write_csv(all_rows, out)

        with jobs_lock:
            jobs[job_id]["status"] = "done"
            jobs[job_id]["result_count"] = len(all_rows)
            jobs[job_id]["log"] += f"\n\nDone. {len(all_rows)} results after dedup+filter."

    threading.Thread(target=run_all, daemon=True).start()
    return jsonify({"job_id": job_id})


@app.get("/api/jobs")
def list_jobs():
    with jobs_lock:
        return jsonify(list(jobs.values()))


@app.get("/api/jobs/<job_id>")
def get_job(job_id):
    with jobs_lock:
        j = jobs.get(job_id)
    if not j:
        return jsonify({"error": "not found"}), 404
    return jsonify(j)


@app.get("/api/stats")
def get_stats():
    return jsonify(stats_from_master())


@app.get("/api/campaigns")
def list_campaigns():
    return jsonify(get_campaign_names())


@app.get("/api/campaigns/<campaign_id>")
def get_campaign_detail(campaign_id):
    c = get_campaign(campaign_id)
    if not c:
        return jsonify({"error": "not found"}), 404
    return jsonify({**c, "id": campaign_id})


@app.get("/api/preview/<job_id>")
def preview_results(job_id):
    if job_id == "master":
        path = RESULTS_DIR / "master.csv"
    else:
        path = RESULTS_DIR / f"job_{job_id}.csv"
    if not path.exists():
        return jsonify({"error": "not found"}), 404
    rows = read_csv_slim(path)
    return jsonify({
        "total": len(rows),
        "with_email": sum(1 for r in rows if r.get("emails", "").strip()),
        "with_phone": sum(1 for r in rows if r.get("phone", "").strip()),
        "no_website": sum(1 for r in rows if not r.get("website", "").strip()),
        "rows": rows[:200],
    })


@app.post("/api/master")
def rebuild_master():
    all_rows = []
    for p in RESULTS_DIR.glob("job_*.csv"):
        all_rows.extend(read_csv_slim(p))
    all_rows = dedup(all_rows)
    write_csv(all_rows, RESULTS_DIR / "master.csv")
    return jsonify({"message": f"Built master.csv with {len(all_rows)} rows."})


@app.get("/download/<job_id>")
def download(job_id):
    if job_id == "master":
        path = RESULTS_DIR / "master.csv"
    else:
        path = RESULTS_DIR / f"job_{job_id}.csv"
    if not path.exists():
        return "File not found", 404
    return send_file(path, as_attachment=True, download_name=path.name)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Dashboard running at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
