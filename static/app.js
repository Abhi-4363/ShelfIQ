/**
 * ShelfIQ v3.0 - Premium Dashboard Frontend
 * Redesigned to match the executive dashboard UI
 */

// Application State
const state = {
    currentPage: 'dashboard',
    selectedStore: 'all',
    selectedDateRange: 'all',
    summaryData: null,
    inventoryData: [],
    salesData: null,
    attentionData: [],
    storesList: [
        { id: 'STR001', name: 'Hyderabad Central' },
        { id: 'STR002', name: 'Banjara Hills' },
        { id: 'STR003', name: 'Kukatpally' },
        { id: 'STR004', name: 'Secunderabad' }
    ]
};

const CATEGORY_COLORS = {
    'Beverages':     '#2563EB',
    'Groceries':     '#059669',
    'Snacks':        '#F59E0B',
    'Personal Care': '#EC4899',
    'Household':     '#8B5CF6',
    'Others':        '#64748B',
    'Dairy':         '#06B6D4'
};

// ─── Init ───────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initModal();
    initAddProductForm();
    initAddProductBtn();
    loadPage('dashboard');
});

// ─── Navigation ─────────────────────────────────────────────────────────────
function initNavigation() {
    document.querySelectorAll('.nav-item[data-page]').forEach(item => {
        item.addEventListener('click', e => {
            e.preventDefault();
            const page = item.dataset.page;
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            item.classList.add('active');
            state.currentPage = page;
            loadPage(page);
        });
    });
}

// ─── Modal ──────────────────────────────────────────────────────────────────
function initModal() {
    const modal = document.getElementById('product-modal');
    const closeBtn = document.getElementById('modal-close');
    if (closeBtn && modal) {
        closeBtn.addEventListener('click', () => modal.classList.add('hidden'));
        modal.addEventListener('click', e => { if (e.target === modal) modal.classList.add('hidden'); });
    }
}

// ─── Add Product Button ──────────────────────────────────────────────────────
function initAddProductBtn() {
    document.addEventListener('click', e => {
        if (e.target.closest('#btn-add-product')) {
            document.getElementById('add-product-modal').classList.remove('hidden');
            document.getElementById('add-product-result').classList.add('hidden');
            document.getElementById('add-product-form').reset();
        }
    });
}

// ─── Add Product Form ────────────────────────────────────────────────────────
function initAddProductForm() {
    const form = document.getElementById('add-product-form');
    if (!form) return;
    form.addEventListener('submit', async e => {
        e.preventDefault();
        const btn = document.getElementById('btn-add-product-submit');
        const resultDiv = document.getElementById('add-product-result');
        btn.disabled = true;
        btn.textContent = 'Adding...';

        const payload = {
            product_name: document.getElementById('ap-name').value.trim(),
            category: document.getElementById('ap-category').value,
            unit_price: parseFloat(document.getElementById('ap-price').value),
            cost_price: parseFloat(document.getElementById('ap-cost').value),
            store_id: document.getElementById('ap-store').value || null,
            initial_stock: parseInt(document.getElementById('ap-stock').value) || 50
        };

        try {
            const res = await fetch('/api/products', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (res.ok) {
                resultDiv.className = 'recommendation-box';
                resultDiv.textContent = `✅ Product "${data.product?.product_name || payload.product_name}" added successfully!`;
                resultDiv.classList.remove('hidden');
                setTimeout(() => {
                    document.getElementById('add-product-modal').classList.add('hidden');
                    if (state.currentPage === 'inventory') loadPage('inventory');
                }, 1800);
            } else {
                throw new Error(data.detail || 'Failed to add product');
            }
        } catch (err) {
            resultDiv.className = 'evidence-box';
            resultDiv.style.color = 'var(--red-text)';
            resultDiv.textContent = `❌ Error: ${err.message}`;
            resultDiv.classList.remove('hidden');
        } finally {
            btn.disabled = false;
            btn.textContent = '+ Add Product';
        }
    });
}

// ─── Page Router ────────────────────────────────────────────────────────────
async function loadPage(pageName) {
    const viewport = document.getElementById('content-viewport');
    viewport.innerHTML = `<div class="loading-state" style="margin:24px 28px;"><h3>⏳ Loading...</h3></div>`;

    try {
        fetchAttentionBadge();
        switch (pageName) {
            case 'dashboard': await renderDashboardPage(viewport); break;
            case 'inventory': await renderInventoryPage(viewport); break;
            case 'sales':     await renderSalesPage(viewport); break;
            case 'attention': await renderAttentionPage(viewport); break;
            case 'copilot':   renderCopilotPage(viewport); break;
            case 'settings':  await renderSettingsPage(viewport); break;
            default:          await renderDashboardPage(viewport);
        }
    } catch (err) {
        console.error('Page load error:', err);
        viewport.innerHTML = `
            <div class="error-state" style="margin:24px 28px;">
                <h3>Unable to load page</h3>
                <p style="margin-top:8px;">Cannot connect to ShelfIQ backend.</p>
                <button class="btn btn-secondary" onclick="loadPage('${pageName}')" style="margin-top:16px;">Try Again</button>
            </div>`;
    }
}

async function fetchAttentionBadge() {
    try {
        const url = state.selectedStore !== 'all' ? `/api/attention?store_id=${state.selectedStore}` : '/api/attention';
        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();
        const badge = document.getElementById('attention-badge');
        const notifBadge = document.getElementById('notif-badge');
        const count = data.count || 0;
        if (badge) {
            badge.textContent = count;
            count > 0 ? badge.classList.remove('hidden') : badge.classList.add('hidden');
        }
        if (notifBadge) {
            const critCount = data.severity_counts ? (data.severity_counts.CRITICAL || 0) : 0;
            notifBadge.textContent = critCount;
            critCount > 0 ? notifBadge.classList.remove('hidden') : notifBadge.classList.add('hidden');
        }
    } catch (_) { /* silent */ }
}

// ─── Build params ────────────────────────────────────────────────────────────
function buildSalesQueryParams() {
    const params = new URLSearchParams();
    if (state.selectedStore !== 'all') params.set('store_id', state.selectedStore);
    const endDate = '2026-08-29';
    const ranges = { last_30_days: '2026-07-31', last_14_days: '2026-08-16', last_7_days: '2026-08-23' };
    if (state.selectedDateRange !== 'all' && ranges[state.selectedDateRange]) {
        params.set('start_date', ranges[state.selectedDateRange]);
        params.set('end_date', endDate);
    }
    const q = params.toString();
    return q ? `?${q}` : '';
}

// ═══════════════════════════════════════════════════════════════════════════════
// PAGE 1: DASHBOARD
// ═══════════════════════════════════════════════════════════════════════════════
async function renderDashboardPage(container) {
    const storeParam = state.selectedStore !== 'all' ? `?store_id=${state.selectedStore}` : '';
    const [summaryRes, attentionRes, salesRes] = await Promise.all([
        fetch('/api/summary'),
        fetch(`/api/attention${storeParam}`),
        fetch(`/api/sales${buildSalesQueryParams()}`)
    ]);

    if (!summaryRes.ok) throw new Error('Failed to fetch dashboard data.');

    const summary = await summaryRes.json();
    const attention = attentionRes.ok ? await attentionRes.json() : { attention_items: [], severity_counts: {}, count: 0 };
    const salesData = salesRes.ok ? await salesRes.json() : { daily_trend: [], product_performance: [], sales_growth: {} };

    state.summaryData = summary;
    state.attentionData = attention.attention_items || [];

    const totalSales = state.selectedStore !== 'all'
        ? (summary.stores_summary?.find(s => s.store_id === state.selectedStore)?.total_sales_amount || summary.total_sales)
        : summary.total_sales;

    const invValue = state.selectedStore !== 'all'
        ? (summary.stores_summary?.find(s => s.store_id === state.selectedStore)?.inventory_value || summary.inventory_value)
        : summary.inventory_value;

    const critCount = (attention.severity_counts?.CRITICAL || 0) + (attention.severity_counts?.HIGH || 0);
    const salesGrowth = salesData.sales_growth || summary.sales_growth || {};
    const growthValue = salesGrowth.percentage_change;
    const growthDisplay = growthValue === null || growthValue === undefined
        ? 'N/A'
        : `${growthValue > 0 ? '+' : ''}${growthValue}%`;
    const growthUp = growthValue >= 0;

    // Top products
    const topProducts = [...(salesData.product_performance || [])]
        .sort((a, b) => b.total_sales_amount - a.total_sales_amount)
        .slice(0, 5);

    // Category distribution from products
    const catMap = {};
    (salesData.product_performance || []).forEach(p => {
        catMap[p.category] = (catMap[p.category] || 0) + p.total_sales_amount;
    });
    const totalCatSales = Object.values(catMap).reduce((s, v) => s + v, 0) || 1;
    const categories = Object.entries(catMap).sort((a, b) => b[1] - a[1]).slice(0, 6);

    // Inventory health
    const totalItems = (summary.total_products || 0) * (summary.total_stores || 1);
    const critItems = attention.severity_counts?.CRITICAL || 0;
    const highItems = attention.severity_counts?.HIGH || 0;
    const lowStock = critItems + highItems;
    const outOfStock = critItems;
    const inStock = Math.max(0, totalItems - lowStock);
    const healthPct = totalItems > 0 ? Math.round((inStock / totalItems) * 100) : 78;

    // Recent alerts (top 3)
    const recentAlerts = (attention.attention_items || []).slice(0, 3);

    // greeting
    const hour = new Date().getHours();
    const greeting = hour < 12 ? 'Good Morning' : hour < 17 ? 'Good Afternoon' : 'Good Evening';
    const greetIcon = hour < 12 ? '🌤️' : hour < 17 ? '☀️' : '🌙';

    const storeName = state.selectedStore !== 'all'
        ? (state.storesList.find(s => s.id === state.selectedStore)?.name || 'Selected Store')
        : 'All Stores';

    const dateLabel = summary.date_range
        ? `${formatDateShort(summary.date_range.start_date)} - ${formatDateShort(summary.date_range.end_date)}`
        : '';

    container.innerHTML = `
        <!-- Page Header -->
        <div class="page-header">
            <div class="page-greeting">
                <div class="page-greeting-icon">${greetIcon}</div>
                <div>
                    <div class="page-greeting-title">${greeting}, Abhi!</div>
                    <div class="page-greeting-sub">Here's what's happening with your store today.</div>
                </div>
            </div>
            <div class="page-controls">
                <div class="filter-pill">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
                    <select id="store-select" onchange="state.selectedStore=this.value;loadPage('dashboard');">
                        <option value="all">All Stores</option>
                        ${state.storesList.map(s => `<option value="${s.id}" ${state.selectedStore === s.id ? 'selected' : ''}>${s.name}</option>`).join('')}
                    </select>
                </div>
                <div class="filter-pill">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                    <span>${dateLabel}</span>
                </div>
                <button class="btn btn-primary" id="btn-add-product">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    Add Product
                </button>
            </div>
        </div>

        <div class="page-content">
            <!-- KPI Grid -->
            <div class="kpi-grid">
                <div class="kpi-card kpi-card--revenue">
                    <div class="kpi-icon-wrap kpi-icon-wrap--blue">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>
                    </div>
                    <div class="kpi-body">
                        <div class="kpi-label">Total Revenue</div>
                        <div class="kpi-value">${formatINR(totalSales)}</div>
                        <div class="kpi-change up">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="18 15 12 9 6 15"/></svg>
                            +12% vs previous period
                        </div>
                    </div>
                    <div class="kpi-chart-btn">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                    </div>
                </div>

                <div class="kpi-card kpi-card--growth">
                    <div class="kpi-icon-wrap kpi-icon-wrap--green">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>
                    </div>
                    <div class="kpi-body">
                        <div class="kpi-label">Sales Growth</div>
                        <div class="kpi-value" style="color: ${growthUp ? 'var(--green)' : 'var(--red)'};">${growthDisplay}</div>
                        <div class="kpi-change ${growthUp ? 'up' : 'down'}">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="${growthUp ? '18 15 12 9 6 15' : '18 9 12 15 6 9'}"/></svg>
                            ${growthDisplay} vs previous period
                        </div>
                    </div>
                    <div class="kpi-chart-btn">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="18" y="3" width="4" height="18"/><rect x="10" y="8" width="4" height="13"/><rect x="2" y="13" width="4" height="8"/></svg>
                    </div>
                </div>

                <div class="kpi-card kpi-card--inventory">
                    <div class="kpi-icon-wrap kpi-icon-wrap--purple">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/></svg>
                    </div>
                    <div class="kpi-body">
                        <div class="kpi-label">Inventory Value</div>
                        <div class="kpi-value">${formatINR(invValue)}</div>
                        <div class="kpi-change up">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="18 15 12 9 6 15"/></svg>
                            +5% vs previous period
                        </div>
                    </div>
                    <div class="kpi-chart-btn">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8"/></svg>
                    </div>
                </div>

                <div class="kpi-card kpi-card--alerts">
                    <div class="kpi-icon-wrap kpi-icon-wrap--red">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>
                    </div>
                    <div class="kpi-body">
                        <div class="kpi-label">Urgent Issues</div>
                        <div class="kpi-value" style="color: ${critCount > 0 ? 'var(--red)' : 'var(--green)'};">${critCount}</div>
                        <div class="kpi-change ${critCount > 0 ? 'down' : 'up'}">
                            Critical &amp; High severity alerts
                            <a href="#attention" onclick="event.preventDefault();loadPage('attention');" style="margin-left:4px;font-size:11px;color:var(--primary);text-decoration:underline;">›</a>
                        </div>
                    </div>
                    <div class="kpi-chart-btn" onclick="loadPage('attention')" title="View Alerts">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
                    </div>
                </div>
            </div>

            <!-- Main 3-column grid: Sales Trend | Category Donut | Quick Actions -->
            <div class="dashboard-main-grid">
                <!-- Sales Trend -->
                <div class="section-card" style="grid-column: span 1;">
                    <div class="section-header">
                        <div>
                            <div class="section-title">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>
                                Sales Trend
                            </div>
                        </div>
                        <select class="period-select" onchange="state.selectedDateRange=this.value;loadPage('dashboard');">
                            <option value="all">Last 3 Months</option>
                            <option value="last_30_days">Last 30 Days</option>
                            <option value="last_14_days">Last 14 Days</option>
                            <option value="last_7_days">Last 7 Days</option>
                        </select>
                    </div>
                    <div id="dashboard-chart-container" class="chart-container"></div>
                    <div class="chart-legend">
                        <div class="chart-legend-item">
                            <div class="chart-legend-dot" style="background:#2563EB;"></div> Revenue
                        </div>
                        <div class="chart-legend-item">
                            <div class="chart-legend-dot" style="background:#059669;"></div> Units Sold
                        </div>
                    </div>
                </div>

                <!-- Category Distribution Donut -->
                <div class="section-card">
                    <div class="section-header">
                        <div class="section-title">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                            Category Distribution
                        </div>
                    </div>
                    <div class="donut-container">
                        <div class="donut-chart-wrap">
                            ${renderDonutSVG(categories, totalCatSales, invValue)}
                        </div>
                        <div class="donut-legend">
                            ${categories.map(([cat, val]) => `
                                <div class="donut-legend-item">
                                    <div class="donut-legend-left">
                                        <div class="donut-legend-dot" style="background:${CATEGORY_COLORS[cat] || '#64748B'};"></div>
                                        ${escapeHTML(cat)}
                                    </div>
                                    <span class="donut-legend-pct">${Math.round((val / totalCatSales) * 100)}%</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <!-- Quick Actions -->
                <div class="section-card">
                    <div class="section-header">
                        <div class="section-title">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                            Quick Actions
                        </div>
                    </div>
                    <div class="quick-actions-grid">
                        <button class="quick-action-btn" id="btn-add-product">
                            <div class="quick-action-icon" style="background:#EFF6FF;">➕</div>
                            Add Product
                        </button>
                        <button class="quick-action-btn" onclick="loadPage('inventory')">
                            <div class="quick-action-icon" style="background:#F0FDF4;">📦</div>
                            Update Stock
                        </button>
                        <button class="quick-action-btn" onclick="loadPage('sales')">
                            <div class="quick-action-icon" style="background:#FFF7ED;">🛒</div>
                            Record Sale
                        </button>
                        <button class="quick-action-btn" onclick="loadPage('sales')">
                            <div class="quick-action-icon" style="background:#FFF7ED;">📊</div>
                            Generate Report
                        </button>
                        <button class="quick-action-btn" onclick="loadPage('attention')">
                            <div class="quick-action-icon" style="background:#FEF2F2;">🔔</div>
                            View Alerts
                        </button>
                        <button class="quick-action-btn" onclick="loadPage('copilot')">
                            <div class="quick-action-icon" style="background:#F5F3FF;">🤖</div>
                            AI Assistant
                        </button>
                    </div>
                </div>
            </div>

            <!-- Bottom grid: Top Products | Right Panel -->
            <div class="dashboard-bottom-grid">
                <!-- Top Products Table -->
                <div class="section-card">
                    <div class="section-header">
                        <div>
                            <div class="section-title">
                                🏆 Top Products
                            </div>
                        </div>
                        <a class="view-all-link" onclick="loadPage('inventory')">View All</a>
                    </div>
                    <div class="table-container">
                        <table class="top-products-table">
                            <thead>
                                <tr>
                                    <th style="width:32px;">#</th>
                                    <th>Product Name</th>
                                    <th>Category</th>
                                    <th class="number-cell">Units Sold</th>
                                    <th class="number-cell">Revenue</th>
                                    <th>Stock Status</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${topProducts.map((p, i) => {
                                    const emoji = ['🥇','🥈','🥉','4️⃣','5️⃣'][i] || (i + 1);
                                    const stockStatus = p.status || 'HEALTHY';
                                    const stockBadge = stockBadgeHTML(stockStatus);
                                    return `
                                        <tr onclick="openProductModal('${p.product_id}')">
                                            <td><span class="rank-num">${i + 1}</span></td>
                                            <td>
                                                <div class="product-name-cell">
                                                    <div class="product-img-placeholder">${getCatEmoji(p.category)}</div>
                                                    <span class="product-name-text">${escapeHTML(p.product_name)}</span>
                                                </div>
                                            </td>
                                            <td style="color:var(--text-secondary);">${escapeHTML(p.category)}</td>
                                            <td class="number-cell">${formatNumber(p.total_units_sold)}</td>
                                            <td class="number-cell" style="font-weight:700;">${formatINR(p.total_sales_amount)}</td>
                                            <td>${stockBadge}</td>
                                            <td>
                                                <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation();openProductModal('${p.product_id}')">
                                                    ⋯
                                                </button>
                                            </td>
                                        </tr>
                                    `;
                                }).join('') || `<tr><td colspan="7" style="text-align:center;padding:24px;color:var(--text-muted);">No product data available.</td></tr>`}
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Right panel: Inventory Health + Recent Alerts -->
                <div style="display:flex;flex-direction:column;gap:16px;">
                    <!-- Inventory Health -->
                    <div class="section-card">
                        <div class="section-header">
                            <div class="section-title">
                                ❤️ Inventory Health
                            </div>
                            <a class="view-all-link" onclick="loadPage('inventory')">View Details</a>
                        </div>
                        <div class="inv-health-donut-wrap">
                            <div class="inv-health-donut-svg-wrap">
                                ${renderHealthDonut(healthPct)}
                                <div class="inv-health-center">
                                    <div class="inv-health-pct">${healthPct}%</div>
                                    <div class="inv-health-label">Healthy</div>
                                </div>
                            </div>
                            <div class="inv-health-stats">
                                <div class="inv-health-stat">
                                    <div class="inv-health-stat-label">
                                        <div class="inv-stat-dot" style="background:var(--green);"></div> In Stock
                                    </div>
                                    <div class="inv-health-stat-val">${formatNumber(inStock)}</div>
                                </div>
                                <div class="inv-health-stat">
                                    <div class="inv-health-stat-label">
                                        <div class="inv-stat-dot" style="background:#F59E0B;"></div> Low Stock
                                    </div>
                                    <div class="inv-health-stat-val">${formatNumber(lowStock)}</div>
                                </div>
                                <div class="inv-health-stat">
                                    <div class="inv-health-stat-label">
                                        <div class="inv-stat-dot" style="background:var(--red);"></div> Out of Stock
                                    </div>
                                    <div class="inv-health-stat-val">${formatNumber(outOfStock)}</div>
                                </div>
                                <div class="inv-health-stat" style="border-top:1px solid var(--border);padding-top:8px;margin-top:4px;">
                                    <div class="inv-health-stat-label" style="font-weight:700;color:var(--text-primary);">Total Products</div>
                                    <div class="inv-health-stat-val">${summary.total_products || 0}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Recent Alerts -->
                    <div class="section-card">
                        <div class="section-header">
                            <div class="section-title" style="color:var(--red);">
                                🔔 Recent Alerts
                            </div>
                            <a class="view-all-link" onclick="loadPage('attention')">View All</a>
                        </div>
                        <div class="recent-alerts-list">
                            ${recentAlerts.length === 0
                                ? `<div style="padding:20px;text-align:center;color:var(--text-muted);font-size:13px;">✅ No active alerts</div>`
                                : recentAlerts.map(a => {
                                    const dotColor = a.severity === 'CRITICAL' ? 'alert-dot--red' : a.severity === 'HIGH' ? 'alert-dot--orange' : 'alert-dot--yellow';
                                    const desc = a.metric_summary || a.attention_type?.replace(/_/g,' ') || '';
                                    return `
                                        <div class="recent-alert-item" onclick="openProductModal('${a.product_id}')">
                                            <div class="alert-dot ${dotColor}"></div>
                                            <div class="alert-item-body">
                                                <div class="alert-item-name">${escapeHTML(a.product_name)}</div>
                                                <div class="alert-item-desc">${escapeHTML(desc)}</div>
                                            </div>
                                            <div class="alert-item-time">now</div>
                                            <svg class="alert-arrow" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
                                        </div>
                                    `;
                                }).join('')
                            }
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Render the sales trend SVG chart
    renderSalesTrendLine(document.getElementById('dashboard-chart-container'), salesData.daily_trend || []);
}

// ─── Donut chart helpers ─────────────────────────────────────────────────────
function renderDonutSVG(categories, total, invValue) {
    const cx = 80, cy = 80, r = 65, innerR = 44;
    const circumference = 2 * Math.PI * r;
    let offset = 0;

    const slices = categories.map(([cat, val]) => {
        const pct = val / total;
        const dashLen = pct * circumference;
        const gap = circumference - dashLen;
        const slice = { cat, val, pct, dashLen, gap, offset, color: CATEGORY_COLORS[cat] || '#64748B' };
        offset += dashLen;
        return slice;
    });

    const paths = slices.map(s => `
        <circle
            cx="${cx}" cy="${cy}" r="${r}"
            fill="none"
            stroke="${s.color}"
            stroke-width="24"
            stroke-dasharray="${s.dashLen} ${s.gap}"
            stroke-dashoffset="${-s.offset + circumference * 0.25}"
            style="transition: stroke-dashoffset 0.5s ease;"
        />
    `).join('');

    const valShort = formatINRShort(invValue);

    return `
        <svg width="160" height="160" viewBox="0 0 160 160">
            <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="#F1F5F9" stroke-width="24"/>
            ${paths}
            <circle cx="${cx}" cy="${cy}" r="${innerR}" fill="white"/>
        </svg>
        <div class="donut-center-label">
            <div class="donut-center-value">${valShort}</div>
            <div class="donut-center-sub">Total Value</div>
        </div>
    `;
}

function renderHealthDonut(pct) {
    const cx = 50, cy = 50, r = 40;
    const circ = 2 * Math.PI * r;
    const filled = (pct / 100) * circ;
    return `
        <svg width="100" height="100" viewBox="0 0 100 100">
            <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="#F1F5F9" stroke-width="14"/>
            <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="#059669" stroke-width="14"
                stroke-dasharray="${filled} ${circ - filled}"
                stroke-dashoffset="${circ * 0.25}"
                stroke-linecap="round"/>
        </svg>
    `;
}

function stockBadgeHTML(status) {
    const s = (status || '').toUpperCase();
    if (s === 'CRITICAL' || s === 'OUT_OF_STOCK') return `<span class="badge badge-out-of-stock">● Out of Stock</span>`;
    if (s === 'HIGH' || s === 'LOW STOCK' || s === 'LOW_STOCK') return `<span class="badge badge-low-stock">● Low Stock</span>`;
    return `<span class="badge badge-in-stock">● In Stock</span>`;
}

function getCatEmoji(cat) {
    const map = { 'Beverages': '🧃', 'Groceries': '🛒', 'Snacks': '🍿', 'Personal Care': '🧴', 'Household': '🏠', 'Dairy': '🥛', 'Others': '📦' };
    return map[cat] || '📦';
}

function formatDateShort(dateStr) {
    if (!dateStr) return '';
    const [y, m, d] = dateStr.split('-');
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    return `${parseInt(d)} ${months[parseInt(m) - 1]} ${y}`;
}

function formatINRShort(val) {
    if (!val) return '₹0';
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(1)}Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`;
    if (val >= 1000) return `₹${(val / 1000).toFixed(1)}K`;
    return `₹${val}`;
}

// ─── Line Chart ──────────────────────────────────────────────────────────────
function renderSalesTrendLine(container, dailyTrend) {
    if (!container) return;
    const trend = Array.isArray(dailyTrend) ? dailyTrend.slice(-60) : [];
    if (trend.length < 2) {
        container.innerHTML = `<div class="empty-state" style="height:100%;border:none;"><p>Not enough data for chart.</p></div>`;
        return;
    }

    const W = 560, H = 190;
    const padL = 10, padR = 10, padT = 20, padB = 30;
    const cW = W - padL - padR;
    const cH = H - padT - padB;

    const sales = trend.map(d => +d.sales_amount || 0);
    const units = trend.map(d => +d.units_sold || 0);
    const maxSales = Math.max(...sales, 1);
    const maxUnits = Math.max(...units, 1);

    const xPos = (i) => padL + (i / (trend.length - 1)) * cW;
    const yPosSales = (v) => padT + cH - (v / maxSales) * cH;
    const yPosUnits = (v) => padT + cH - (v / maxUnits) * cH;

    const salesPath = trend.map((d, i) => `${i === 0 ? 'M' : 'L'}${xPos(i)},${yPosSales(+d.sales_amount || 0)}`).join(' ');
    const unitsPath = trend.map((d, i) => `${i === 0 ? 'M' : 'L'}${xPos(i)},${yPosUnits(+d.units_sold || 0)}`).join(' ');
    const areaPath = salesPath + ` L${xPos(trend.length-1)},${padT+cH} L${padL},${padT+cH} Z`;

    // Peak annotation
    const peakIdx = sales.indexOf(maxSales);
    const peakX = xPos(peakIdx);
    const peakY = yPosSales(maxSales);
    const peakDate = trend[peakIdx]?.date || '';
    const peakLabel = peakDate ? peakDate.slice(5).replace('-', '/') : '';

    // X-axis labels (every ~10 points)
    const step = Math.max(1, Math.floor(trend.length / 5));
    const xLabels = trend.map((d, i) => {
        if (i % step !== 0 && i !== trend.length - 1) return '';
        const parts = (d.date || '').split('-');
        const label = parts.length === 3 ? parts.slice(1).join('/') : '';
        return `<text x="${xPos(i)}" y="${H - 5}" text-anchor="middle" class="chart-axis-text">${label}</text>`;
    }).join('');

    // Grid lines
    const grid = [0.25, 0.5, 0.75, 1].map(f => {
        const y = padT + cH - f * cH;
        const val = formatINRShort(maxSales * f);
        return `
            <line x1="${padL}" y1="${y}" x2="${W - padR}" y2="${y}" stroke="#E2E8F0" stroke-width="1" stroke-dasharray="4"/>
            <text x="${padL}" y="${y - 3}" class="chart-axis-text" text-anchor="start">${val}</text>
        `;
    }).join('');

    container.innerHTML = `
        <svg viewBox="0 0 ${W} ${H}" class="svg-chart">
            <defs>
                <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#2563EB" stop-opacity="0.15"/>
                    <stop offset="100%" stop-color="#2563EB" stop-opacity="0"/>
                </linearGradient>
            </defs>
            ${grid}
            <path d="${areaPath}" fill="url(#areaGrad)"/>
            <path d="${salesPath}" class="chart-line-path"/>
            <path d="${unitsPath}" class="chart-line-path-green"/>
            <!-- Peak annotation -->
            <circle cx="${peakX}" cy="${peakY}" r="4" fill="#2563EB"/>
            <rect x="${peakX - 40}" y="${peakY - 28}" width="80" height="22" rx="4" fill="#1E293B"/>
            <text x="${peakX}" y="${peakY - 13}" text-anchor="middle" font-size="10" fill="#fff" font-weight="700" font-family="Inter,sans-serif">${formatINRShort(maxSales)}</text>
            <text x="${peakX}" y="${peakY - 4}" text-anchor="middle" font-size="8.5" fill="#94A3B8" font-family="Inter,sans-serif">${peakLabel}</text>
            ${xLabels}
        </svg>
    `;
}

// ═══════════════════════════════════════════════════════════════════════════════
// PAGE 2: INVENTORY
// ═══════════════════════════════════════════════════════════════════════════════
async function renderInventoryPage(container) {
    let url = '/api/inventory';
    if (state.selectedStore !== 'all') url += `?store_id=${state.selectedStore}`;

    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load inventory data.');
    const data = await res.json();
    state.inventoryData = data.inventory || [];

    container.innerHTML = `
        <div class="page-header">
            <div class="page-greeting">
                <div class="page-greeting-icon">📦</div>
                <div>
                    <div class="page-greeting-title">Inventory Management</div>
                    <div class="page-greeting-sub">Monitor stock levels, sales velocity, and stock-out risks.</div>
                </div>
            </div>
            <div class="page-controls">
                <div class="filter-pill">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
                    <select onchange="state.selectedStore=this.value;loadPage('inventory');">
                        <option value="all">All Stores</option>
                        ${state.storesList.map(s => `<option value="${s.id}" ${state.selectedStore === s.id ? 'selected' : ''}>${s.name}</option>`).join('')}
                    </select>
                </div>
                <button class="btn btn-primary" id="btn-add-product">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    Add Product
                </button>
            </div>
        </div>
        <div class="page-content">
            <div class="section-card">
                <div class="section-header">
                    <div style="display:flex;gap:10px;flex:1;flex-wrap:wrap;">
                        <input type="text" id="inv-search" class="form-input" placeholder="🔍 Search product name or ID..." style="min-width:220px;">
                        <select id="inv-category" class="form-select">
                            <option value="all">All Categories</option>
                            <option>Beverages</option><option>Groceries</option><option>Snacks</option>
                            <option>Personal Care</option><option>Household</option><option>Dairy</option>
                        </select>
                        <select id="inv-status" class="form-select">
                            <option value="all">All Statuses</option>
                            <option value="CRITICAL">Critical</option>
                            <option value="HIGH">Low Stock</option>
                            <option value="MEDIUM">Watch</option>
                            <option value="HEALTHY">Healthy</option>
                            <option value="OVERSTOCKED">Overstocked</option>
                            <option value="SLOW_MOVING">Slow Moving</option>
                        </select>
                    </div>
                    <div class="subtitle" id="inv-count-label">Showing ${state.inventoryData.length} records</div>
                </div>
                <div class="table-container">
                    <table class="data-table" id="inventory-table">
                        <thead>
                            <tr>
                                <th>Product Name</th>
                                <th>Category</th>
                                <th>Store</th>
                                <th class="number-cell">Current Stock</th>
                                <th class="number-cell">Daily Sales</th>
                                <th class="number-cell">Days Remaining</th>
                                <th>Status</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody id="inventory-table-body">
                            ${renderInventoryTableRows(state.inventoryData)}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;

    const search = document.getElementById('inv-search');
    const catSel = document.getElementById('inv-category');
    const statSel = document.getElementById('inv-status');

    function applyFilters() {
        const q = search.value.toLowerCase().trim();
        const cat = catSel.value;
        const stat = statSel.value;
        const filtered = state.inventoryData.filter(item => {
            const mS = !q || item.product_name.toLowerCase().includes(q) || item.product_id.toLowerCase().includes(q);
            const mC = cat === 'all' || item.category === cat;
            const mSt = stat === 'all' || item.status.toUpperCase() === stat.toUpperCase();
            return mS && mC && mSt;
        });
        document.getElementById('inventory-table-body').innerHTML = renderInventoryTableRows(filtered);
        document.getElementById('inv-count-label').textContent = `Showing ${filtered.length} of ${state.inventoryData.length} records`;
    }

    if (search) search.addEventListener('input', applyFilters);
    if (catSel) catSel.addEventListener('change', applyFilters);
    if (statSel) statSel.addEventListener('change', applyFilters);
}

function renderInventoryTableRows(items) {
    if (!items || items.length === 0) {
        return `<tr><td colspan="8" style="text-align:center;padding:32px;color:var(--text-muted);">No products match the selected filter criteria.</td></tr>`;
    }
    return items.map(item => {
        const daysDisplay = item.days_remaining_display !== 'UNAVAILABLE' ? `${item.days_remaining}d` : 'N/A';
        const badgeClass = getBadgeClassForStatus(item.status);
        return `
            <tr onclick="openProductModal('${item.product_id}')">
                <td>
                    <div style="font-weight:600;">${escapeHTML(item.product_name)}</div>
                    <div class="subtitle">${escapeHTML(item.product_id)}</div>
                </td>
                <td>${escapeHTML(item.category)}</td>
                <td>${escapeHTML(item.store_name)}</td>
                <td class="number-cell">${formatNumber(item.current_stock)}</td>
                <td class="number-cell">${item.average_daily_units_sold} u/d</td>
                <td class="number-cell">${daysDisplay}</td>
                <td><span class="badge ${badgeClass}">${escapeHTML(item.status)}</span></td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation();openProductModal('${item.product_id}');">Details</button>
                </td>
            </tr>
        `;
    }).join('');
}

// ═══════════════════════════════════════════════════════════════════════════════
// PAGE 3: SALES
// ═══════════════════════════════════════════════════════════════════════════════
async function renderSalesPage(container) {
    const res = await fetch(`/api/sales${buildSalesQueryParams()}`);
    if (!res.ok) throw new Error('Failed to load sales data.');
    const data = await res.json();
    state.salesData = data;

    const summary = data.summary || {};
    const products = data.product_performance || [];
    const salesGrowth = data.sales_growth || {};
    const growthValue = salesGrowth.percentage_change;
    const growthDisplay = growthValue === null || growthValue === undefined ? 'N/A' : `${growthValue > 0 ? '+' : ''}${growthValue}%`;
    const topProducts = [...products].sort((a, b) => b.total_sales_amount - a.total_sales_amount).slice(0, 5);
    const bottomProducts = [...products].sort((a, b) => a.total_sales_amount - b.total_sales_amount).slice(0, 5);

    container.innerHTML = `
        <div class="page-header">
            <div class="page-greeting">
                <div class="page-greeting-icon">📈</div>
                <div>
                    <div class="page-greeting-title">Sales Analytics</div>
                    <div class="page-greeting-sub">Analyze revenue, units sold, and performance trends.</div>
                </div>
            </div>
            <div class="page-controls">
                <div class="filter-pill">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
                    <select onchange="state.selectedStore=this.value;loadPage('sales');">
                        <option value="all">All Stores</option>
                        ${state.storesList.map(s => `<option value="${s.id}" ${state.selectedStore === s.id ? 'selected' : ''}>${s.name}</option>`).join('')}
                    </select>
                </div>
                <select class="period-select" style="padding:7px 14px;border-radius:20px;" onchange="state.selectedDateRange=this.value;loadPage('sales');">
                    <option value="all">Last 3 Months</option>
                    <option value="last_30_days">Last 30 Days</option>
                    <option value="last_14_days">Last 14 Days</option>
                    <option value="last_7_days">Last 7 Days</option>
                </select>
            </div>
        </div>
        <div class="page-content">
            <div class="kpi-grid">
                <div class="kpi-card kpi-card--revenue">
                    <div class="kpi-icon-wrap kpi-icon-wrap--blue">💰</div>
                    <div class="kpi-body">
                        <div class="kpi-label">Total Revenue</div>
                        <div class="kpi-value">${formatINR(summary.total_sales_amount || 0)}</div>
                        <div class="kpi-change neutral">${summary.date_range?.start_date || ''} → ${summary.date_range?.end_date || ''}</div>
                    </div>
                </div>
                <div class="kpi-card kpi-card--growth">
                    <div class="kpi-icon-wrap kpi-icon-wrap--green">📦</div>
                    <div class="kpi-body">
                        <div class="kpi-label">Total Units Sold</div>
                        <div class="kpi-value">${formatNumber(summary.total_units_sold || 0)}</div>
                        <div class="kpi-change neutral">Total item volume</div>
                    </div>
                </div>
                <div class="kpi-card kpi-card--inventory">
                    <div class="kpi-icon-wrap kpi-icon-wrap--purple">📊</div>
                    <div class="kpi-body">
                        <div class="kpi-label">Avg Daily Revenue</div>
                        <div class="kpi-value">${formatINR(summary.avg_daily_sales_amount || 0)}</div>
                        <div class="kpi-change neutral">Per day average</div>
                    </div>
                </div>
                <div class="kpi-card kpi-card--alerts">
                    <div class="kpi-icon-wrap kpi-icon-wrap--${growthValue >= 0 ? 'green' : 'red'}">${growthValue >= 0 ? '📈' : '📉'}</div>
                    <div class="kpi-body">
                        <div class="kpi-label">Sales Growth</div>
                        <div class="kpi-value" style="color:${growthValue >= 0 ? 'var(--green)' : 'var(--red)'};">${growthDisplay}</div>
                        <div class="kpi-change ${growthValue >= 0 ? 'up' : 'down'}">Recent vs prior period</div>
                    </div>
                </div>
            </div>

            <div class="section-card" style="margin-bottom:16px;">
                <div class="section-header">
                    <div class="section-title">Sales Revenue Trend</div>
                    <span class="badge badge-info">Historical Performance</span>
                </div>
                <div id="sales-chart-container" class="chart-container"></div>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
                <div class="section-card">
                    <div class="section-header"><div class="section-title">🏆 Top 5 Revenue Products</div></div>
                    <div class="table-container">
                        <table class="data-table">
                            <thead><tr><th>Product</th><th>Category</th><th class="number-cell">Revenue</th><th class="number-cell">Units</th></tr></thead>
                            <tbody>
                                ${topProducts.map(p => `
                                    <tr onclick="openProductModal('${p.product_id}')">
                                        <td style="font-weight:600;">${escapeHTML(p.product_name)}</td>
                                        <td>${escapeHTML(p.category)}</td>
                                        <td class="number-cell">${formatINR(p.total_sales_amount)}</td>
                                        <td class="number-cell">${formatNumber(p.total_units_sold)}</td>
                                    </tr>`).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="section-card">
                    <div class="section-header"><div class="section-title">📉 Bottom 5 Revenue Products</div></div>
                    <div class="table-container">
                        <table class="data-table">
                            <thead><tr><th>Product</th><th>Category</th><th class="number-cell">Revenue</th><th class="number-cell">Units</th></tr></thead>
                            <tbody>
                                ${bottomProducts.map(p => `
                                    <tr onclick="openProductModal('${p.product_id}')">
                                        <td style="font-weight:600;">${escapeHTML(p.product_name)}</td>
                                        <td>${escapeHTML(p.category)}</td>
                                        <td class="number-cell">${formatINR(p.total_sales_amount)}</td>
                                        <td class="number-cell">${formatNumber(p.total_units_sold)}</td>
                                    </tr>`).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    `;

    renderSalesTrendLine(document.getElementById('sales-chart-container'), data.daily_trend || []);
}

// ═══════════════════════════════════════════════════════════════════════════════
// PAGE 4: ATTENTION / ALERTS
// ═══════════════════════════════════════════════════════════════════════════════
async function renderAttentionPage(container) {
    let url = '/api/attention';
    if (state.selectedStore !== 'all') url += `?store_id=${state.selectedStore}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load attention alerts.');
    const data = await res.json();
    state.attentionData = data.attention_items || [];

    container.innerHTML = `
        <div class="page-header">
            <div class="page-greeting">
                <div class="page-greeting-icon">🔔</div>
                <div>
                    <div class="page-greeting-title">Alerts & Attention Required</div>
                    <div class="page-greeting-sub">Critical operational findings, evidence, and recommendations.</div>
                </div>
            </div>
            <div class="page-controls">
                <div class="filter-pill">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
                    <select onchange="state.selectedStore=this.value;loadPage('attention');">
                        <option value="all">All Stores</option>
                        ${state.storesList.map(s => `<option value="${s.id}" ${state.selectedStore === s.id ? 'selected' : ''}>${s.name}</option>`).join('')}
                    </select>
                </div>
            </div>
        </div>
        <div class="page-content">
            <div class="section-card">
                <div class="section-header" style="flex-wrap:wrap;gap:10px;">
                    <div style="display:flex;gap:8px;flex-wrap:wrap;">
                        <button class="btn btn-secondary btn-sm att-type-btn active" data-type="all">All (${data.count || 0})</button>
                        <button class="btn btn-secondary btn-sm att-type-btn" data-type="STOCK_OUT_RISK">Stock-Out Risks</button>
                        <button class="btn btn-secondary btn-sm att-type-btn" data-type="SLOW_MOVING">Slow-Moving</button>
                        <button class="btn btn-secondary btn-sm att-type-btn" data-type="OVERSTOCK">Overstock</button>
                        <button class="btn btn-secondary btn-sm att-type-btn" data-type="SALES_SPIKE">Sales Spikes</button>
                        <button class="btn btn-secondary btn-sm att-type-btn" data-type="SALES_DROP">Sales Drops</button>
                    </div>
                    <select id="att-severity-select" class="form-select">
                        <option value="all">All Severities</option>
                        <option value="CRITICAL">Critical Only</option>
                        <option value="HIGH">High Only</option>
                        <option value="MEDIUM">Medium Only</option>
                    </select>
                </div>
                <div id="attention-list-container" class="attention-grid" style="padding:20px;">
                    ${state.attentionData.length === 0
                        ? `<div class="empty-state" style="border:none;"><p>✅ Zero active attention findings. Store operations are optimal.</p></div>`
                        : state.attentionData.map(item => renderAttentionCardHTML(item)).join('')}
                </div>
            </div>
        </div>
    `;

    const typeBtns = container.querySelectorAll('.att-type-btn');
    const sevSelect = container.querySelector('#att-severity-select');
    let activeType = 'all', activeSev = 'all';

    function filterAttentionList() {
        const filtered = state.attentionData.filter(item => {
            return (activeType === 'all' || item.attention_type === activeType)
                && (activeSev === 'all' || item.severity === activeSev);
        });
        const lc = document.getElementById('attention-list-container');
        lc.innerHTML = filtered.length === 0
            ? `<div class="empty-state" style="border:none;"><p>No items match the selected filters.</p></div>`
            : filtered.map(item => renderAttentionCardHTML(item)).join('');
    }

    typeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            typeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeType = btn.dataset.type;
            filterAttentionList();
        });
    });
    if (sevSelect) sevSelect.addEventListener('change', e => { activeSev = e.target.value; filterAttentionList(); });
}

function renderAttentionCardHTML(item) {
    const badgeClass = getBadgeClassForSeverity(item.severity);
    const typeLabel = item.attention_type.replace(/_/g, ' ');
    return `
        <div class="attention-card ${item.severity.toLowerCase()}">
            <div class="attention-card-header">
                <div style="display:flex;gap:6px;align-items:center;">
                    <span class="badge ${badgeClass}">${escapeHTML(item.severity)}</span>
                    <span class="badge badge-info">${escapeHTML(typeLabel)}</span>
                </div>
                <div class="attention-store">${escapeHTML(item.store_name)}</div>
            </div>
            <div>
                <div class="attention-title" onclick="openProductModal('${item.product_id}')" style="cursor:pointer;">
                    ${escapeHTML(item.product_name)} <span class="subtitle">(${escapeHTML(item.product_id)})</span>
                </div>
                <p style="font-size:13px;color:var(--text-secondary);margin-top:4px;">${escapeHTML(item.metric_summary)}</p>
            </div>
            <div class="evidence-box">
                <div style="font-weight:700;color:var(--text-primary);margin-bottom:4px;">📊 Factual Evidence</div>
                <div><strong>Metric:</strong> ${escapeHTML(item.evidence?.metric || 'N/A')}</div>
                <div><strong>Period:</strong> ${escapeHTML(item.evidence?.calculation_period || 'Historical 90-day window')}</div>
                <div><strong>Threshold:</strong> ${escapeHTML(item.evidence?.threshold_used || 'Centralized Business Rule')}</div>
            </div>
            <div class="recommendation-box">
                <strong>💡 Recommended Action:</strong> ${escapeHTML(item.recommendation)}
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;font-size:11px;color:var(--text-muted);">
                <span>Assumptions: ${escapeHTML(item.assumptions ? item.assumptions[0] : 'Historical velocity continuation.')}</span>
                <span class="badge badge-healthy">Data: ${escapeHTML(item.data_sufficiency)}</span>
            </div>
        </div>
    `;
}

// ═══════════════════════════════════════════════════════════════════════════════
// PAGE 5: AI COPILOT
// ═══════════════════════════════════════════════════════════════════════════════
let copilotHistory = [];
let copilotLastIntent = null;
let copilotLastProductId = null;

function renderCopilotPage(container) {
    container.innerHTML = `
        <div class="page-header">
            <div class="page-greeting">
                <div class="page-greeting-icon">🤖</div>
                <div>
                    <div class="page-greeting-title">AI Insights — Ask ShelfIQ</div>
                    <div class="page-greeting-sub">Get evidence-based answers about your sales and inventory.</div>
                </div>
            </div>
            <div class="page-controls">
                <span class="badge badge-healthy">Grounded AI Active</span>
            </div>
        </div>
        <div class="page-content">
            <div class="copilot-container">
                <div class="copilot-header-card">
                    <div class="copilot-section-title">💡 Sample Questions You Can Ask:</div>
                    <div class="sample-questions-grid">
                        <div class="sample-pill" onclick="askCopilotQuestion('What needs attention today?')">⚠️ What needs attention today?</div>
                        <div class="sample-pill" onclick="askCopilotQuestion('Which products may run out soon?')">🚨 Which products may run out soon?</div>
                        <div class="sample-pill" onclick="askCopilotQuestion('What is overstocked?')">📦 What is overstocked?</div>
                        <div class="sample-pill" onclick="askCopilotQuestion('Which products are selling slowly?')">📉 Which are selling slowly?</div>
                        <div class="sample-pill" onclick="askCopilotQuestion('Did sales spike anywhere?')">🚀 Did sales spike anywhere?</div>
                        <div class="sample-pill" onclick="askCopilotQuestion('How are my sales performing?')">📊 How are sales performing?</div>
                    </div>
                    <form id="copilot-form" onsubmit="handleCopilotSubmit(event)" class="copilot-input-area">
                        <input type="text" id="copilot-input" class="form-input" placeholder="Ask a question about inventory, sales, products, or stores..." autocomplete="off">
                        <button type="submit" id="btn-copilot-submit" class="btn btn-primary">Send ➔</button>
                    </form>
                </div>
                <div id="copilot-loading" class="loading-state hidden">
                    <div style="font-size:15px;font-weight:600;color:var(--primary);" class="copilot-loading-text">⌛ Analyzing your store data...</div>
                    <p style="font-size:13px;color:var(--text-muted);margin-top:4px;">Fetching deterministic evidence and synthesizing grounded decision support.</p>
                </div>
                <div id="copilot-results" style="display:flex;flex-direction:column;gap:18px;">
                    ${copilotHistory.length === 0 ? `
                        <div class="empty-state">
                            <div style="font-size:32px;margin-bottom:8px;">📊</div>
                            <div style="font-weight:600;color:var(--text-primary);">No questions asked yet.</div>
                            <p style="font-size:13px;color:var(--text-muted);margin-top:4px;">Click any sample question above or type your query.</p>
                        </div>
                    ` : copilotHistory.map(item => renderCopilotResponseHTML(item)).join('')}
                </div>
            </div>
        </div>
    `;
}

async function handleCopilotSubmit(e) {
    if (e) e.preventDefault();
    const input = document.getElementById('copilot-input');
    if (!input?.value?.trim()) return;
    const q = input.value.trim();
    input.value = '';
    await askCopilotQuestion(q);
}

async function askCopilotQuestion(questionText) {
    const loading = document.getElementById('copilot-loading');
    const submitBtn = document.getElementById('btn-copilot-submit');
    if (loading) loading.classList.remove('hidden');
    if (submitBtn) submitBtn.disabled = true;

    const selectedStore = state.selectedStore !== 'all' ? state.selectedStore : null;

    try {
        const payload = {
            question: questionText,
            store_id: selectedStore,
            previous_intent: copilotLastIntent,
            previous_product_id: copilotLastProductId
        };
        const res = await fetch('/api/ai/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || 'Copilot query failed');
        }
        const data = await res.json();
        copilotLastIntent = data.intent;
        if (data.evidence?.length > 0 && data.evidence[0].product_id) {
            copilotLastProductId = data.evidence[0].product_id;
        }
        copilotHistory.unshift(data);
        const results = document.getElementById('copilot-results');
        if (results) results.innerHTML = copilotHistory.map(item => renderCopilotResponseHTML(item)).join('');
    } catch (err) {
        const results = document.getElementById('copilot-results');
        if (results) {
            results.innerHTML = `
                <div class="copilot-error-card">
                    <span style="font-size:20px;">⚠️</span>
                    <div>
                        <div style="font-weight:700;margin-bottom:4px;">Copilot temporarily unavailable</div>
                        <div style="font-size:13px;opacity:0.85;">Please try again. Backend details remain hidden.</div>
                    </div>
                </div>
            ` + copilotHistory.map(item => renderCopilotResponseHTML(item)).join('');
        }
    } finally {
        if (loading) loading.classList.add('hidden');
        if (submitBtn) submitBtn.disabled = false;
    }
}

function renderCopilotResponseHTML(data) {
    const supportingNumbers = Array.isArray(data.supporting_numbers) ? data.supporting_numbers : [];
    const evidence = Array.isArray(data.evidence) ? data.evidence : [];
    const keyPoints = Array.isArray(data.key_points) ? data.key_points : [];
    const assumptions = Array.isArray(data.assumptions) ? data.assumptions : [];
    const suffClass = data.data_sufficiency === 'SUFFICIENT' ? 'badge-healthy' : data.data_sufficiency === 'LIMITED' ? 'badge-medium' : 'badge-critical';

    return `
        <div class="copilot-response-card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid var(--border);padding-bottom:12px;">
                <div>
                    <span style="font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;">Question</span>
                    <h3 style="font-size:15px;font-weight:700;color:var(--text-primary);margin-top:2px;">"${escapeHTML(data.question || '')}"</h3>
                </div>
                <span class="badge ${suffClass}">Data: ${escapeHTML(data.data_sufficiency || 'INSUFFICIENT')}</span>
            </div>
            <div>
                <div class="copilot-section-title">💬 Answer</div>
                <div class="copilot-answer-text">${escapeHTML(data.answer || 'Analysis complete.')}</div>
            </div>
            ${supportingNumbers.length > 0 ? `
                <div>
                    <div class="copilot-section-title">📊 Supporting Numbers</div>
                    <div class="supporting-numbers-grid">
                        ${supportingNumbers.map(num => `
                            <div class="supporting-number-card">
                                <div style="font-size:11px;font-weight:600;color:var(--text-muted);">${escapeHTML(num.product_name || 'Retail Metric')}</div>
                                <div style="font-size:16px;font-weight:700;color:var(--text-primary);">${escapeHTML(num.value)}</div>
                                <div style="font-size:11px;color:var(--text-secondary);">${escapeHTML(num.metric)} (${escapeHTML(num.store_name || 'All Stores')})</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            ${evidence.length > 0 ? `
                <div>
                    <div class="copilot-section-title">🔎 Factual Evidence</div>
                    ${evidence.map(ev => `
                        <div class="evidence-item-card">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                                <span class="source-badge">Source: ${escapeHTML(ev.source || 'Inventory analysis')}</span>
                                <span style="font-size:11px;color:var(--text-muted);">Period: ${escapeHTML(ev.period || 'Last 90 days')}</span>
                            </div>
                            <div><strong>${escapeHTML(ev.product_name || '')} ${ev.store_name ? `@ ${escapeHTML(ev.store_name)}` : ''}</strong></div>
                            <div style="font-size:12px;color:var(--text-secondary);margin-top:2px;">
                                <strong>Metric:</strong> ${escapeHTML(ev.metric || 'metric_value')} = ${escapeHTML(ev.value)}
                            </div>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            ${keyPoints.length > 0 ? `
                <div>
                    <div class="copilot-section-title">📌 Key Takeaways</div>
                    <ul style="padding-left:20px;font-size:13px;color:var(--text-primary);display:flex;flex-direction:column;gap:4px;">
                        ${keyPoints.map(kp => `<li>${escapeHTML(kp)}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            <div class="recommendation-box">
                <strong>💡 Recommended Action:</strong> ${escapeHTML(data.recommendation || 'Continue standard inventory monitoring.')}
            </div>
            <div class="copilot-footer-row">
                <span><strong>Assumptions:</strong> ${escapeHTML(assumptions.length > 0 ? assumptions[0] : 'Based on factual daily sales velocity.')}</span>
                <span><strong>Intent:</strong> ${escapeHTML(data.intent || 'UNKNOWN')}</span>
            </div>
        </div>
    `;
}

// ═══════════════════════════════════════════════════════════════════════════════
// PAGE 6: SETTINGS
// ═══════════════════════════════════════════════════════════════════════════════
async function renderSettingsPage(container) {
    const res = await fetch('/api/health');
    const health = res.ok ? await res.json() : {};

    container.innerHTML = `
        <div class="page-header">
            <div class="page-greeting">
                <div class="page-greeting-icon">⚙️</div>
                <div>
                    <div class="page-greeting-title">Store Settings</div>
                    <div class="page-greeting-sub">Dataset status and application configuration.</div>
                </div>
            </div>
        </div>
        <div class="page-content">
            <div class="section-card section-card-pad" style="max-width:680px;">
                <div class="section-header"><div class="section-title">System Settings & Data Status</div></div>
                <div style="padding:20px;display:flex;flex-direction:column;gap:0;">
                    <div class="settings-row"><strong>Application Version</strong><span>ShelfIQ v3.0</span></div>
                    <div class="settings-row"><strong>Backend Status</strong><span class="badge badge-healthy">${health.status || 'OK'}</span></div>
                    <div class="settings-row"><strong>CSV Data Load Status</strong><span class="badge ${health.data_loaded ? 'badge-healthy' : 'badge-critical'}">${health.data_loaded ? 'LOADED & VALIDATED' : 'FAILED'}</span></div>
                    <div class="settings-row"><strong>Supported Stores</strong><span>4 Stores (Hyderabad Central, Banjara Hills, Kukatpally, Secunderabad)</span></div>
                    <div class="settings-row"><strong>Catalogue Size</strong><span>55 Products across 6 Categories</span></div>
                    <div class="settings-row"><strong>AI Model</strong><span>gemini-3.6-flash (Grounded)</span></div>
                </div>
            </div>
        </div>
    `;
}

// ═══════════════════════════════════════════════════════════════════════════════
// PRODUCT MODAL
// ═══════════════════════════════════════════════════════════════════════════════
async function openProductModal(productId) {
    const modal = document.getElementById('product-modal');
    const body = document.getElementById('modal-body');
    const nameEl = document.getElementById('modal-product-name');
    const subEl = document.getElementById('modal-product-sub');
    if (!modal || !body) return;

    body.innerHTML = '<div class="loading-state" style="border:none;">Loading product details...</div>';
    modal.classList.remove('hidden');

    try {
        const res = await fetch(`/api/products/${productId}`);
        if (!res.ok) throw new Error('Product not found');
        const data = await res.json();
        nameEl.textContent = data.product_name;
        subEl.textContent = `ID: ${data.product_id} | Category: ${data.category}`;
        const perf = data.sales_performance || {};

        body.innerHTML = `
            <div class="kpi-grid" style="grid-template-columns:1fr 1fr 1fr;margin-bottom:20px;">
                <div class="kpi-card">
                    <div class="kpi-body">
                        <div class="kpi-label">Unit Price</div>
                        <div class="kpi-value">${formatINR(data.unit_price)}</div>
                        <div class="kpi-change neutral">Cost: ${formatINR(data.cost_price)}</div>
                    </div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-body">
                        <div class="kpi-label">Total Units Sold</div>
                        <div class="kpi-value">${formatNumber(perf.total_units_sold || 0)}</div>
                        <div class="kpi-change neutral">Revenue: ${formatINR(perf.total_sales_amount || 0)}</div>
                    </div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-body">
                        <div class="kpi-label">Sales Trend</div>
                        <div class="kpi-value">${perf.sales_trend || 'STABLE'}</div>
                        <div class="kpi-change neutral">Avg ${perf.avg_daily_units || 0} u/day</div>
                    </div>
                </div>
            </div>
            <h4 style="margin-bottom:12px;font-size:14px;">Store Inventory Breakdown</h4>
            <div class="table-container" style="margin-bottom:20px;">
                <table class="data-table">
                    <thead><tr><th>Store</th><th class="number-cell">Current Stock</th><th class="number-cell">Daily Sales</th><th class="number-cell">Days Left</th><th>Status</th></tr></thead>
                    <tbody>
                        ${data.inventory_metrics.map(inv => `
                            <tr>
                                <td>${escapeHTML(inv.store_name)}</td>
                                <td class="number-cell">${formatNumber(inv.current_stock)}</td>
                                <td class="number-cell">${inv.average_daily_units_sold} u/d</td>
                                <td class="number-cell">${escapeHTML(inv.days_remaining_display)}</td>
                                <td><span class="badge ${getBadgeClassForStatus(inv.status)}">${escapeHTML(inv.status)}</span></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            ${data.attention_items?.length > 0 ? `
                <h4 style="margin-bottom:12px;font-size:14px;">Active Operational Alerts</h4>
                <div class="attention-grid">
                    ${data.attention_items.map(item => renderAttentionCardHTML(item)).join('')}
                </div>
            ` : `<p style="color:var(--text-muted);font-size:13px;">No critical alerts active for this product.</p>`}
        `;
    } catch (err) {
        body.innerHTML = `<div class="error-state" style="border:none;">Failed to load details for product ${escapeHTML(productId)}.</div>`;
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════════════════════════════════════════
function escapeHTML(value) {
    return String(value === null || value === undefined ? '' : value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function formatINR(val) {
    if (val === null || val === undefined || isNaN(val)) return '₹0';
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);
}

function formatNumber(val) {
    if (val === null || val === undefined || isNaN(val)) return '0';
    return new Intl.NumberFormat('en-IN').format(val);
}

function getBadgeClassForStatus(status) {
    switch ((status || '').toUpperCase()) {
        case 'CRITICAL': return 'badge-critical';
        case 'HIGH': case 'LOW STOCK': case 'LOW_STOCK': return 'badge-high';
        case 'MEDIUM': case 'WATCH': return 'badge-medium';
        case 'HEALTHY': return 'badge-healthy';
        case 'OVERSTOCKED': return 'badge-overstocked';
        case 'SLOW_MOVING': return 'badge-slow';
        default: return 'badge-info';
    }
}

function getBadgeClassForSeverity(sev) {
    switch ((sev || '').toUpperCase()) {
        case 'CRITICAL': return 'badge-critical';
        case 'HIGH': return 'badge-high';
        case 'MEDIUM': return 'badge-medium';
        default: return 'badge-info';
    }
}
