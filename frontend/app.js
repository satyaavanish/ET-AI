/* ZH-1 dependency-free console client. */
const API_BASE = window.API_BASE || (window.location.protocol === "file:" ? "http://127.0.0.1:8420" : window.location.origin);
const POLL_MS = 2500;
let pollHandle = null;
let requestInFlight = false;

const byId = (id) => document.getElementById(id);
const els = {
  shift: byId("shiftValue"), tick: byId("tickValue"), mode: byId("modeValue"),
  connDot: byId("connDot"), connLabel: byId("connLabel"), zoneMap: byId("zoneMap"),
  riskFeed: byId("riskFeed"), orchLog: byId("orchLog"), permitRows: byId("permitRows"),
  complianceList: byId("complianceList"), ragForm: byId("ragForm"), ragQuery: byId("ragQuery"),
  ragResults: byId("ragResults"), triggerDemo: byId("triggerDemo"), resetDemo: byId("resetDemo"),
  downloadEvidence: byId("downloadEvidence"), scenarioBadge: byId("scenarioBadge"), toast: byId("toast"),
  kpiFused: byId("kpiFused"), kpiSensor: byId("kpiSensor"), kpiUplift: byId("kpiUplift"),
  kpiCompound: byId("kpiCompound"), kpiPeople: byId("kpiPeople"), kpiActions: byId("kpiActions"),
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  }[char]));
}

function showToast(message, kind = "info") {
  els.toast.textContent = message;
  els.toast.className = `toast toast--show toast--${kind}`;
  window.setTimeout(() => { els.toast.className = "toast"; }, 2800);
}

function setConnection(ok) {
  els.connDot.classList.toggle("live", ok);
  els.connDot.classList.toggle("down", !ok);
  els.connLabel.textContent = ok ? "live" : "disconnected";
}

function scoreColor(level) {
  return ({ critical: "var(--level-critical)", alert: "var(--level-alert)", elevated: "var(--level-elevated)" }[level] || "var(--text-muted)");
}

function renderMetrics(metrics) {
  els.kpiFused.textContent = Number(metrics.max_fused_score || 0).toFixed(1);
  els.kpiSensor.textContent = Number(metrics.max_sensor_only_score || 0).toFixed(1);
  els.kpiUplift.textContent = `+${Number(metrics.fusion_uplift || 0).toFixed(1)}`;
  els.kpiCompound.textContent = metrics.compound_zones || 0;
  els.kpiPeople.textContent = metrics.people_in_alert_zones || 0;
  els.kpiActions.textContent = metrics.automated_actions || 0;
}

function renderZoneMap(zones, risks) {
  const riskByZone = Object.fromEntries(risks.map((risk) => [risk.zone_id, risk]));
  els.zoneMap.innerHTML = Object.values(zones)
    .sort((a, b) => (a.y - b.y) || (a.x - b.x))
    .map((zone) => {
      const risk = riskByZone[zone.id];
      return `<article class="zone-card level-${escapeHtml(risk?.level || "normal")}" title="${escapeHtml((risk?.factors || []).join(" | "))}">
        <div class="zone-card__id">${escapeHtml(zone.id)}</div>
        <div class="zone-card__label">${escapeHtml(zone.label)}</div>
        <div class="zone-card__score" style="color:${scoreColor(risk?.level)}">${Number(risk?.score || 0).toFixed(0)}</div>
        <div class="zone-card__meta">${risk?.is_compound ? "COMPOUND" : ""}</div>
        <div class="zone-card__bar" style="width:${Math.min(100, Number(risk?.score || 0))}%;background:${scoreColor(risk?.level)}"></div>
      </article>`;
    }).join("");
}

function comparisonBar(label, value, level, cssClass) {
  return `<div class="compare-row"><span>${label}</span><div class="compare-track"><i class="${cssClass}" style="width:${Math.min(100, value)}%;background:${scoreColor(level)}"></i></div><b>${Number(value).toFixed(1)}</b></div>`;
}

function renderRiskFeed(risks) {
  const visible = risks.filter((risk) => risk.score > 4).slice(0, 8);
  if (!visible.length) {
    els.riskFeed.innerHTML = `<p class="empty-state">All zones nominal. Run the emergency demo to show multi-signal fusion.</p>`;
    return;
  }
  els.riskFeed.innerHTML = visible.map((risk) => `<article class="risk-row level-${escapeHtml(risk.level)}">
    <div class="risk-row__top"><span class="risk-row__zone">${escapeHtml(risk.zone_id)} · ${escapeHtml(risk.label)}</span><strong style="color:${scoreColor(risk.level)}">${Number(risk.score).toFixed(1)}</strong></div>
    <div class="risk-tags">${risk.is_compound ? '<span class="risk-tag">compound</span>' : ''}${(risk.factor_categories || []).map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</div>
    <div class="comparison">
      ${comparisonBar("Sensor only", risk.sensor_only_score, risk.sensor_only_level, "sensor-bar")}
      ${comparisonBar("Fused context", risk.score, risk.level, "fused-bar")}
    </div>
    <div class="uplift">Fusion uplift: <strong>+${Number(risk.fusion_uplift).toFixed(1)}</strong></div>
    <ul>${risk.factors.map((factor) => `<li>${escapeHtml(factor)}</li>`).join("")}</ul>
  </article>`).join("");
}

function renderOrchestrator(log) {
  if (!log.length) {
    els.orchLog.innerHTML = `<p class="empty-state">No incident response active. Click “Run emergency demo”.</p>`;
    return;
  }
  els.orchLog.innerHTML = log.map((entry) => `<article class="orch-entry">
    <span class="orch-entry__time">T+${escapeHtml(entry.elapsed_seconds)}s</span>
    <span class="orch-entry__action">${escapeHtml(entry.action.replaceAll("_", " "))}</span>
    <span class="orch-entry__detail">${escapeHtml(entry.detail)}</span>
  </article>`).join("");
}

function renderPermits(permits) {
  els.permitRows.innerHTML = permits.length ? permits.map((permit) => `<tr>
    <td>${escapeHtml(permit.permit_id)}</td><td>${escapeHtml(permit.zone_id)}</td>
    <td><span class="permit-tag permit-tag--${escapeHtml(permit.kind)}">${escapeHtml(permit.kind.replaceAll("_", " "))}</span></td>
    <td>${escapeHtml(permit.issued_by)}</td>
  </tr>`).join("") : `<tr><td colspan="4" class="empty-state">No active permits.</td></tr>`;
}

function renderCompliance(items) {
  els.complianceList.innerHTML = items.map((item) => `<article class="compliance-row status-${escapeHtml(item.status)}">
    <span class="compliance-row__id">${escapeHtml(item.clause_id)}</span>
    <div><div class="compliance-row__status">${escapeHtml(item.status)}</div>
    <div class="compliance-row__body">${escapeHtml(item.summary)}${item.zones_in_violation.length ? ` — zones: ${escapeHtml(item.zones_in_violation.join(", "))}` : ""}</div></div>
  </article>`).join("");
}

function renderState(data) {
  setConnection(true);
  els.shift.textContent = data.shift;
  els.tick.textContent = data.tick;
  const active = Boolean(data.scenario?.active);
  els.mode.textContent = active ? "DEMO ACTIVE" : "Normal";
  els.mode.classList.toggle("meta-chip__value--critical", active);
  els.scenarioBadge.textContent = active ? `${data.scenario.label} · ${data.scenario.ticks_remaining} ticks` : data.scenario.label;
  els.scenarioBadge.classList.toggle("status-badge--active", active);
  renderMetrics(data.metrics);
  renderZoneMap(data.zones, data.risks);
  renderRiskFeed(data.risks);
  renderOrchestrator(data.orchestrator_log);
  renderPermits(data.permits);
  renderCompliance(data.compliance);
}

async function pollState() {
  if (requestInFlight) return;
  requestInFlight = true;
  try {
    const response = await fetch(`${API_BASE}/api/state`, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    renderState(await response.json());
  } catch (error) {
    setConnection(false);
    console.error("State poll failed", error);
  } finally {
    requestInFlight = false;
  }
}

async function postAction(path, successMessage) {
  [els.triggerDemo, els.resetDemo].forEach((button) => { button.disabled = true; });
  try {
    const response = await fetch(`${API_BASE}${path}`, { method: "POST" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (data.state) renderState(data.state);
    showToast(successMessage, "success");
  } catch (error) {
    showToast(`Action failed: ${error.message}`, "error");
  } finally {
    [els.triggerDemo, els.resetDemo].forEach((button) => { button.disabled = false; });
  }
}

async function runSearch(query) {
  els.ragResults.innerHTML = `<p class="empty-state">Searching local evidence index…</p>`;
  try {
    const response = await fetch(`${API_BASE}/api/incidents/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    els.ragResults.innerHTML = data.results.length ? data.results.map((result) => `<article class="rag-card">
      <div class="rag-card__head"><span>${escapeHtml(result.id)}</span><b>relevance ${Number(result.relevance).toFixed(3)}</b></div>
      <div class="rag-card__meta"><span class="rag-card__type ${escapeHtml(result.type)}">${escapeHtml(result.type.replaceAll("_", " "))}</span><span>${escapeHtml(result.source)}</span></div>
      <p>${escapeHtml(result.text)}</p>
      <small>Matched: ${escapeHtml((result.matched_terms || []).join(", ") || "context similarity")}</small>
    </article>`).join("") : `<p class="empty-state">No matches. Try “confined space shift changeover”.</p>`;
  } catch (error) {
    els.ragResults.innerHTML = `<p class="empty-state">Search failed: ${escapeHtml(error.message)}</p>`;
  }
}

async function downloadEvidence() {
  try {
    const response = await fetch(`${API_BASE}/api/evidence/report`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const report = await response.json();
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `ZH1-evidence-tick-${report.state.tick}.json`;
    link.click();
    URL.revokeObjectURL(link.href);
    showToast("Evidence snapshot downloaded", "success");
  } catch (error) {
    showToast(`Download failed: ${error.message}`, "error");
  }
}

els.triggerDemo.addEventListener("click", () => postAction("/api/demo/trigger", "Emergency demo started in zone B1"));
els.resetDemo.addEventListener("click", () => postAction("/api/demo/reset", "Simulation reset"));
els.downloadEvidence.addEventListener("click", downloadEvidence);
els.ragForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const query = els.ragQuery.value.trim();
  if (query.length >= 2) runSearch(query);
});

pollState();
runSearch(els.ragQuery.value);
pollHandle = window.setInterval(pollState, POLL_MS);
window.addEventListener("beforeunload", () => window.clearInterval(pollHandle));
