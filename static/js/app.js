/**
 * BRAHMO Citation Safety Engine — Frontend JavaScript
 *
 * Handles:
 * - Matter selection → auto-fill query
 * - Generic AI request
 * - Verified AI request (full citation pipeline)
 * - Side-by-side rendering
 * - Verification report display
 */

const API_BASE = '';  // Same origin

document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    setupMatterSelector();
});

// ─── Stats ───────────────────────────────────────────────────────────

async function loadStats() {
    try {
        const resp = await fetch(`${API_BASE}/api/stats`);
        const stats = await resp.json();
        const el = document.getElementById('stats-display');
        el.textContent = `${stats.patterns} patterns · ${stats.mappings} mappings · ${stats.matters} matters` +
            ` · IK: ${stats.ik_configured ? '✅' : '❌'} · LLM: ${stats.llm_configured ? '✅' : '❌'}`;
    } catch (e) {
        document.getElementById('stats-display').textContent = 'Stats unavailable';
    }
}

// ─── Matter Selector ─────────────────────────────────────────────────

function setupMatterSelector() {
    const select = document.getElementById('matter-select');
    select.addEventListener('change', async () => {
        const matterId = select.value;
        if (!matterId) return;

        try {
            const resp = await fetch(`${API_BASE}/api/matters/${matterId}`);
            const matter = await resp.json();
            document.getElementById('query-input').value = matter.query || '';

            // Auto-enable sample mode for demo scenarios
            if (matter.scenario_type) {
                document.getElementById('use-sample').checked = true;
            }
        } catch (e) {
            console.error('Error loading matter:', e);
        }
    });
}

// ─── Generic AI Request ──────────────────────────────────────────────

async function askGeneric() {
    const query = document.getElementById('query-input').value.trim();
    const matterId = document.getElementById('matter-select').value;
    const useSample = document.getElementById('use-sample').checked;

    if (!query) {
        alert('Please enter a legal query');
        return;
    }

    setLoading(true, 'generic');

    try {
        const resp = await fetch(`${API_BASE}/api/ask-generic`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query,
                matter_id: matterId ? parseInt(matterId) : null,
                use_sample: useSample,
            }),
        });

        const data = await resp.json();

        if (data.error) {
            showGenericResponse('Error: ' + data.error);
            document.getElementById('comparison-panel').classList.remove('hidden');
            document.getElementById('report-panel').classList.add('hidden');
            document.getElementById('section-alerts').classList.add('hidden');
            document.getElementById('output-alerts-panel').classList.add('hidden');
            return;
        }

        // Clear verified panel when running generic only
        document.getElementById('verified-response').innerHTML = '<span class="text-gray-500 italic">Run "Ask with Citation Verification" to see verified output</span>';

        // Show only the generic panel
        showGenericResponse(data.ai_response);
        document.getElementById('comparison-panel').classList.remove('hidden');
        document.getElementById('report-panel').classList.add('hidden');
        document.getElementById('section-alerts').classList.add('hidden');
        document.getElementById('output-alerts-panel').classList.add('hidden');

    } catch (e) {
        alert('Request failed: ' + e.message);
    } finally {
        setLoading(false);
    }
}

// ─── Verified AI Request (Full Pipeline) ──────────────────────────────

async function askVerified() {
    const query = document.getElementById('query-input').value.trim();
    const matterId = document.getElementById('matter-select').value;
    const useSample = document.getElementById('use-sample').checked;

    if (!query) {
        alert('Please enter a legal query');
        return;
    }

    setLoading(true, 'verified');

    try {
        const resp = await fetch(`${API_BASE}/api/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query,
                matter_id: matterId ? parseInt(matterId) : null,
                use_sample: useSample,
            }),
        });

        const data = await resp.json();

        if (data.error) {
            alert('Error: ' + data.error);
            return;
        }

        // Show both panels for comparison
        // For side-by-side, we also need the generic response
        // If using sample data, the generic is the same unverified text
        showGenericResponse(data.ai_response);
        showVerifiedResponse(data.annotated_html);
        showReport(data.report, data.citations);
        showSectionAlerts(data.query_alerts, data.output_alerts);

        document.getElementById('comparison-panel').classList.remove('hidden');
        document.getElementById('report-panel').classList.remove('hidden');

    } catch (e) {
        alert('Request failed: ' + e.message);
    } finally {
        setLoading(false);
    }
}

// ─── Rendering Functions ──────────────────────────────────────────────

function showGenericResponse(text) {
    const el = document.getElementById('generic-response');
    el.textContent = text;
    el.classList.add('loading-active');
    setTimeout(() => el.classList.remove('loading-active'), 2000);
}

function showVerifiedResponse(html) {
    const el = document.getElementById('verified-response');
    el.innerHTML = html;
    el.classList.add('loading-active');
    setTimeout(() => el.classList.remove('loading-active'), 2000);
}

function showReport(report, citations) {
    // Stats cards
    const statsEl = document.getElementById('report-stats');
    statsEl.innerHTML = `
        <div class="stat-card">
            <div class="stat-value text-white">${report.total_citations}</div>
            <div class="stat-label">Total Found</div>
        </div>
        <div class="stat-card">
            <div class="stat-value text-green-400">${report.verified}</div>
            <div class="stat-label">✅ Verified</div>
        </div>
        <div class="stat-card">
            <div class="stat-value text-yellow-400">${report.corrected}</div>
            <div class="stat-label">⚠️ Corrected</div>
        </div>
        <div class="stat-card">
            <div class="stat-value text-orange-400">${report.unverified}</div>
            <div class="stat-label">⚠️ Unverified</div>
        </div>
        <div class="stat-card">
            <div class="stat-value text-red-400">${report.removed}</div>
            <div class="stat-label">❌ Removed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value text-brand-400">${report.accuracy_pct}%</div>
            <div class="stat-label">Accuracy</div>
        </div>
        <div class="stat-card">
            <div class="stat-value text-green-300">₹${report.ik_cost_inr}</div>
            <div class="stat-label">IK API Cost</div>
        </div>
    `;

    // Citation details
    const citEl = document.getElementById('report-citations');
    citEl.innerHTML = '';

    // Group: show problematic first, then verified (collapsed)
    const problematic = citations.filter(c => c.status !== 'VERIFIED');
    const verified = citations.filter(c => c.status === 'VERIFIED');

    if (problematic.length > 0) {
        problematic.forEach(c => {
            citEl.appendChild(createCitationCard(c));
        });
    }

    if (verified.length > 0) {
        const verifiedSection = document.createElement('div');
        verifiedSection.innerHTML = `
            <div class="flex items-center space-x-2 text-green-400 text-sm cursor-pointer py-1"
                 onclick="this.nextElementSibling.classList.toggle('hidden')">
                <span>✅ ${verified.length} verified citations</span>
                <span class="text-gray-500 text-xs">(click to expand)</span>
            </div>
            <div class="hidden space-y-2 mt-1">
                ${verified.map(c => createCitationCard(c).outerHTML).join('')}
            </div>
        `;
        citEl.appendChild(verifiedSection);
    }
}

function createCitationCard(citation) {
    const div = document.createElement('div');
    const statusClass = citation.status.toLowerCase().replace('_', '-');
    if (citation.status === 'HALLUCINATED' || citation.status === 'NOT_FOUND') {
        div.className = 'citation-detail removed';
    } else {
        div.className = `citation-detail ${statusClass}`;
    }

    let html = `<div class="flex items-center justify-between">
        <span class="font-mono">${escapeHtml(citation.original)}</span>
        <span class="text-xs ${getStatusColor(citation.status)}">${citation.badge} ${citation.status}</span>
    </div>`;

    if (citation.case_name) {
        html += `<div class="text-gray-400 text-xs mt-1">Case: ${escapeHtml(citation.case_name)}</div>`;
    }

    if (citation.corrected_citation) {
        html += `<div class="text-yellow-400 text-xs mt-1">Corrected to: ${escapeHtml(citation.corrected_citation)}</div>`;
    }

    if (citation.reason) {
        html += `<div class="text-gray-500 text-xs mt-1">${escapeHtml(citation.reason)}</div>`;
    }

    if (citation.source) {
        html += `<div class="text-gray-600 text-xs mt-1">Source: ${citation.source} ${citation.cost ? '· ₹' + citation.cost.toFixed(2) : ''}</div>`;
    }

    div.innerHTML = html;
    return div;
}

function showSectionAlerts(queryAlerts, outputAlerts) {
    // Query alerts (sections in the user's query)
    const queryPanel = document.getElementById('section-alerts');
    const queryContent = document.getElementById('section-alerts-content');

    if (queryAlerts && queryAlerts.length > 0) {
        queryPanel.classList.remove('hidden');
        queryContent.innerHTML = queryAlerts.map(a => `
            <div class="section-alert-item">
                <span class="section-old">${escapeHtml(a.original)}</span>
                <span class="section-arrow">→</span>
                <span class="section-new">${escapeHtml(a.converted)}</span>
                <span class="text-gray-500 text-xs">(${escapeHtml(a.old_act)})</span>
            </div>
        `).join('');
    } else {
        queryPanel.classList.add('hidden');
    }

    // Output alerts (sections in the AI response)
    const outputPanel = document.getElementById('output-alerts-panel');
    const outputContent = document.getElementById('output-alerts-content');

    if (outputAlerts && outputAlerts.length > 0) {
        outputPanel.classList.remove('hidden');
        outputContent.innerHTML = outputAlerts.map(a => `
            <div class="section-alert-item">
                <span class="section-old">${escapeHtml(a.original)}</span>
                <span class="section-arrow">→</span>
                <span class="section-new">${escapeHtml(a.converted)}</span>
                <span class="text-gray-500 text-xs">(${escapeHtml(a.new_act)})</span>
            </div>
        `).join('');
    } else {
        outputPanel.classList.add('hidden');
    }
}

// ─── Utilities ────────────────────────────────────────────────────────

function setLoading(active, type) {
    const indicator = document.getElementById('loading-indicator');
    const btnGeneric = document.getElementById('btn-generic');
    const btnVerified = document.getElementById('btn-verified');

    if (active) {
        indicator.classList.remove('hidden');
        if (type === 'generic') {
            btnGeneric.disabled = true;
            btnGeneric.classList.add('opacity-50');
        } else {
            btnVerified.disabled = true;
            btnVerified.classList.add('opacity-50');
        }
    } else {
        indicator.classList.add('hidden');
        btnGeneric.disabled = false;
        btnGeneric.classList.remove('opacity-50');
        btnVerified.disabled = false;
        btnVerified.classList.remove('opacity-50');
    }
}

function getStatusColor(status) {
    const colors = {
        'VERIFIED': 'text-green-400',
        'CORRECTED': 'text-yellow-400',
        'UNVERIFIED': 'text-orange-400',
        'HALLUCINATED': 'text-red-400',
        'NOT_FOUND': 'text-red-400',
    };
    return colors[status] || 'text-gray-400';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}