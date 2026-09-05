/**
 * ShelfIQ - Retail Sales & Inventory Copilot
 * Production Frontend Application Script (Phase 7)
 * Consumes FastAPI backend endpoints cleanly.
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
    isLoading: false,
    error: null
};

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initGlobalControls();
    initModal();
    loadPage(state.currentPage);
});

// -------------------------------------------------------------
// NAVIGATION & GLOBAL CONTROLS
// -------------------------------------------------------------
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item[data-page]');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.getAttribute('data-page');

            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            state.currentPage = page;
            loadPage(page);
        });
    });
}

function initGlobalControls() {
    const storeSelect = document.getElementById('store-select');
    const dateSelect = document.getElementById('date-range-select');
    const refreshBtn = document.getElementById('btn-refresh');

    if (storeSelect) {
        storeSelect.addEventListener('change', (e) => {
            state.selectedStore = e.target.value;
            loadPage(state.currentPage);
        });
    }

    if (dateSelect) {
        dateSelect.addEventListener('change', (e) => {
            state.selectedDateRange = e.target.value;
            loadPage(state.currentPage);
        });
    }

    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            loadPage(state.currentPage);
        });
    }
}

function initModal() {
    const modal = document.getElementById('product-modal');
    const closeBtn = document.getElementById('modal-close');

    if (closeBtn && modal) {
        closeBtn.addEventListener('click', () => modal.classList.add('hidden'));
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.classList.add('hidden');
        });
    }
}

// -------------------------------------------------------------
// PAGE ROUTER & DATA FETCHING
// -------------------------------------------------------------
async function loadPage(pageName) {
    const titleEl = document.getElementById('page-title');
    const subtitleEl = document.getElementById('page-subtitle');
    const viewport = document.getElementById('content-viewport');

    const pageTitles = {
        dashboard: { title: 'Dashboard', subtitle: "Good morning. Here's what needs your attention today." },
        inventory: { title: 'Inventory Management', subtitle: 'Monitor stock levels, sales velocity, and stock-out risks.' },
        sales: { title: 'Sales Analytics', subtitle: 'Analyze revenue, units sold, and performance trends.' },
        attention: { title: 'Attention Required', subtitle: 'Critical operational findings, evidence, and recommendations.' },
        copilot: { title: 'Ask ShelfIQ', subtitle: 'Ask questions about your sales, inventory, and store operations.' },
        settings: { title: 'System Settings', subtitle: 'Dataset status and application configuration.' }
    };

    const config = pageTitles[pageName] || { title: 'ShelfIQ', subtitle: '' };
    if (titleEl) titleEl.textContent = config.title;
    if (subtitleEl) subtitleEl.textContent = config.subtitle;

    // Show loading state
    viewport.innerHTML = `
        <div class="loading-state">
            <h3>⏳ Loading store data...</h3>
            <p style="margin-top: 8px;">Fetching latest metrics from backend.</p>
        </div>
    `;

    try {
        // Fetch attention badge count in background
        fetchAttentionBadge();

        switch (pageName) {
            case 'dashboard':
                await renderDashboardPage(viewport);
                break;
            case 'inventory':
                await renderInventoryPage(viewport);
                break;
            case 'sales':
                await renderSalesPage(viewport);
                break;
            case 'attention':
                await renderAttentionPage(viewport);
                break;
            case 'copilot':
                renderCopilotPage(viewport);
                break;
            case 'settings':
                await renderSettingsPage(viewport);
                break;
            default:
                await renderDashboardPage(viewport);
        }
    } catch (err) {
        console.error("Error loading page:", err);
        viewport.innerHTML = `
            <div class="error-state">
                <h3>Unable to load ${escapeHTML(config.title)}</h3>
                <p style="margin-top: 8px;">Unable to connect to ShelfIQ. Please try again.</p>
                <button class="btn btn-secondary" onclick="loadPage('${pageName}')" style="margin-top: 16px;">Try Again</button>
            </div>
        `;
    }
}

async function fetchAttentionBadge() {
    try {
        const url = state.selectedStore !== 'all' ? `/api/attention?store_id=${state.selectedStore}` : '/api/attention';
        const res = await fetch(url);
        if (res.ok) {
            const data = await res.json();
            const badge = document.getElementById('attention-badge');
            if (badge) {
                const count = data.count || 0;
                badge.textContent = count;
                if (count > 0) badge.classList.remove('hidden');
                else badge.classList.add('hidden');
            }
        }
    } catch (e) {
        // Silent catch for background badge
    }
}

// -------------------------------------------------------------
// PAGE 1: DASHBOARD
// -------------------------------------------------------------
function buildSalesQueryParams() {
    const params = new URLSearchParams();
    if (state.selectedStore !== 'all') params.set('store_id', state.selectedStore);

    const endDate = '2026-08-29';
    const ranges = {
        last_30_days: '2026-07-31',
        last_14_days: '2026-08-16',
        last_7_days: '2026-08-23'
    };
    if (state.selectedDateRange !== 'all' && ranges[state.selectedDateRange]) {
        params.set('start_date', ranges[state.selectedDateRange]);
        params.set('end_date', endDate);
    }

    const query = params.toString();
    return query ? `?${query}` : '';
}

async function renderDashboardPage(container) {
    const storeParam = state.selectedStore !== 'all' ? `?store_id=${state.selectedStore}` : '';
    const [summaryRes, attentionRes] = await Promise.all([
        fetch(`/api/summary`),
        fetch(`/api/attention${storeParam}`)
    ]);

    if (!summaryRes.ok || !attentionRes.ok) throw new Error("Failed to fetch dashboard data.");

    const summary = await summaryRes.json();
    const attention = await attentionRes.json();

    state.summaryData = summary;
    state.attentionData = attention.attention_items || [];

    const storeSummary = state.selectedStore !== 'all' 
        ? summary.stores_summary.find(s => s.store_id === state.selectedStore) || summary
        : summary;

    const totalSales = state.selectedStore !== 'all' ? storeSummary.total_sales_amount : summary.total_sales;
    const invValue = state.selectedStore !== 'all' ? storeSummary.inventory_value : summary.inventory_value;
    const critCount = attention.severity_counts ? (attention.severity_counts.CRITICAL + attention.severity_counts.HIGH) : 0;

    const topAttentions = (attention.attention_items || []).slice(0, 5);
    const salesRes = await fetch(`/api/sales${buildSalesQueryParams()}`);
    const salesData = salesRes.ok ? await salesRes.json() : { daily_trend: [], product_performance: [], sales_growth: summary.sales_growth };
    const topProducts = [...(salesData.product_performance || [])]
        .sort((a, b) => b.total_sales_amount - a.total_sales_amount)
        .slice(0, 5);
    const salesGrowth = salesData.sales_growth || summary.sales_growth || {};
    const growthValue = salesGrowth.percentage_change;
    const growthDisplay = growthValue === null || growthValue === undefined ? 'N/A' : `${growthValue > 0 ? '+' : ''}${growthValue}%`;

    // Build top products ranked list HTML
    const maxRevenue = topProducts.length > 0 ? topProducts[0].total_sales_amount : 1;
    const rankColors = ['#2563EB', '#7C3AED', '#059669', '#D97706', '#DC2626'];
    const rankEmojis = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣'];

    const topProductCardsHTML = topProducts.map((p, i) => {
        const barPct = Math.max(8, Math.round((p.total_sales_amount / maxRevenue) * 100));
        const color = rankColors[i] || '#64748B';
        return `
            <div class="top-product-card" onclick="openProductModal('${p.product_id}')" title="Click to view details">
                <div class="top-product-rank" style="background:${color};">${i + 1}</div>
                <div class="top-product-info">
                    <div class="top-product-name">${escapeHTML(p.product_name)}</div>
                    <div class="top-product-meta">
                        <span class="top-product-category">${escapeHTML(p.category)}</span>
                        <span class="top-product-units">${formatNumber(p.total_units_sold)} units</span>
                    </div>
                    <div class="top-product-bar-wrap">
                        <div class="top-product-bar" style="width:${barPct}%; background:${color};"></div>
                    </div>
                </div>
                <div class="top-product-revenue" style="color:${color};">${formatINR(p.total_sales_amount)}</div>
            </div>
        `;
    }).join('');

    container.innerHTML = `
        <!-- KPI Cards -->
        <div class="kpi-grid">
            <div class="kpi-card kpi-card--revenue">
                <div class="kpi-card-icon">💰</div>
                <div class="kpi-card-body">
                    <div class="kpi-label">Total Revenue</div>
                    <div class="kpi-value">${formatINR(totalSales)}</div>
                    <div class="kpi-sub">📅 ${summary.date_range.start_date} → ${summary.date_range.end_date}</div>
                </div>
            </div>
            <div class="kpi-card kpi-card--growth">
                <div class="kpi-card-icon">${growthValue >= 0 ? '📈' : '📉'}</div>
                <div class="kpi-card-body">
                    <div class="kpi-label">Sales Growth</div>
                    <div class="kpi-value" style="color: ${growthValue >= 0 ? '#047857' : '#B91C1C'};">${growthDisplay}</div>
                    <div class="kpi-sub">${escapeHTML(salesGrowth.period || 'Selected period comparison')}</div>
                </div>
            </div>
            <div class="kpi-card kpi-card--inventory">
                <div class="kpi-card-icon">📦</div>
                <div class="kpi-card-body">
                    <div class="kpi-label">Inventory Value</div>
                    <div class="kpi-value">${formatINR(invValue)}</div>
                    <div class="kpi-sub">Current total stock value</div>
                </div>
            </div>
            <div class="kpi-card kpi-card--alerts">
                <div class="kpi-card-icon">${critCount > 0 ? '🚨' : '✅'}</div>
                <div class="kpi-card-body">
                    <div class="kpi-label">Urgent Issues</div>
                    <div class="kpi-value" style="color: ${critCount > 0 ? '#B91C1C' : '#047857'};">${critCount}</div>
                    <div class="kpi-sub">Critical &amp; High severity alerts</div>
                </div>
            </div>
        </div>

        <!-- Two column: Top Products + Inventory Health -->
        <div class="dashboard-top-row">
            <!-- Top Products: Ranked Cards -->
            <div class="section-card">
                <div class="section-header">
                    <div>
                        <h2 class="section-title">🏆 Top Products</h2>
                        <div class="subtitle" style="margin-top:2px;">By revenue — click any card to drill down</div>
                    </div>
                    <span class="badge badge-info">Top 5</span>
                </div>
                <div class="top-products-list">
                    ${topProductCardsHTML || '<div class="empty-state"><p>No product data available.</p></div>'}
                </div>
            </div>

            <!-- Inventory Health -->
            <div class="section-card">
                <div class="section-header">
                    <h2 class="section-title">📊 Inventory Health</h2>
                </div>
                <div class="health-grid" style="grid-template-columns: 1fr;">
                    <div class="health-card critical">
                        <div class="health-count">${attention.severity_counts ? attention.severity_counts.CRITICAL : 0}</div>
                        <div class="health-label">🔴 Critical Stock-Out Risk</div>
                    </div>
                    <div class="health-card watch">
                        <div class="health-count">${attention.severity_counts ? attention.severity_counts.HIGH : 0}</div>
                        <div class="health-label">🟠 High Priority Risks</div>
                    </div>
                    <div class="health-card healthy">
                        <div class="health-count">${Math.max(0, summary.total_products * summary.total_stores - (attention.count || 0))}</div>
                        <div class="health-label">🟢 Healthy Items</div>
                    </div>
                </div>
                <div style="margin-top:16px; padding-top:16px; border-top: 1px solid var(--border-color);">
                    <div class="section-title" style="font-size:13px; margin-bottom:10px;">Store Coverage</div>
                    <div style="display:flex; gap:8px; flex-wrap: wrap;">
                        <span class="badge badge-info">📍 ${summary.total_stores} Stores</span>
                        <span class="badge badge-info">📦 ${summary.total_products} Products</span>
                        <span class="badge badge-info">📊 ${summary.total_transactions || 'N/A'} Txns</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Sales Trend Chart -->
        <div class="section-card">
            <div class="section-header">
                <div>
                    <h2 class="section-title">📈 Daily Sales Trend</h2>
                    <div class="subtitle" style="margin-top:2px;">Revenue over the selected period</div>
                </div>
                <span class="badge badge-info">Daily Revenue</span>
            </div>
            <div id="dashboard-chart-container" class="chart-container">
                <!-- SVG Chart injected below -->
            </div>
        </div>

        <!-- Attention Required Top Issues -->
        <div class="section-card">
            <div class="section-header">
                <div>
                    <h2 class="section-title">⚠️ Attention Required Today</h2>
                    <div class="subtitle" style="margin-top:2px;">Top ${topAttentions.length} urgent alerts</div>
                </div>
                <a href="#attention" class="btn btn-secondary btn-sm" onclick="event.preventDefault(); loadPage('attention');">View All ${attention.count || 0} Alerts →</a>
            </div>
            ${topAttentions.length === 0 ? `
                <div class="empty-state">
                    <p>✅ All inventory systems are healthy. No items require immediate attention.</p>
                </div>
            ` : `
                <div class="attention-grid">
                    ${topAttentions.map(item => renderAttentionCardHTML(item)).join('')}
                </div>
            `}
        </div>
    `;

    renderSalesTrendSVG(document.getElementById('dashboard-chart-container'), salesData.daily_trend || []);
}

// -------------------------------------------------------------
// PAGE 2: INVENTORY MANAGEMENT
// -------------------------------------------------------------
async function renderInventoryPage(container) {
    let url = '/api/inventory';
    if (state.selectedStore !== 'all') url += `?store_id=${state.selectedStore}`;

    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to load inventory data.");

    const data = await res.json();
    state.inventoryData = data.inventory || [];

    container.innerHTML = `
        <div class="section-card">
            <!-- Filter Controls Bar -->
            <div class="section-header" style="flex-wrap: wrap; gap: 12px;">
                <div style="display: flex; gap: 12px; flex: 1; flex-wrap: wrap;">
                    <input type="text" id="inv-search" class="form-input" placeholder="🔍 Search product name or ID..." style="min-width: 220px;">
                    
                    <select id="inv-category" class="form-select">
                        <option value="all">All Categories</option>
                        <option value="Groceries">Groceries</option>
                        <option value="Beverages">Beverages</option>
                        <option value="Snacks">Snacks</option>
                        <option value="Personal Care">Personal Care</option>
                        <option value="Household">Household</option>
                        <option value="Dairy">Dairy</option>
                    </select>

                    <select id="inv-status" class="form-select">
                        <option value="all">All Statuses</option>
                        <option value="CRITICAL">Critical</option>
                        <option value="HIGH">Low Stock / High</option>
                        <option value="MEDIUM">Watch / Medium</option>
                        <option value="HEALTHY">Healthy</option>
                        <option value="OVERSTOCKED">Overstocked</option>
                        <option value="SLOW_MOVING">Slow Moving</option>
                    </select>
                </div>

                <div class="subtitle" id="inv-count-label">Showing ${state.inventoryData.length} records</div>
            </div>

            <!-- Inventory Data Table -->
            <div class="table-container">
                <table class="data-table" id="inventory-table">
                    <thead>
                        <tr>
                            <th>Product Name</th>
                            <th>Category</th>
                            <th>Store</th>
                            <th>Current Stock</th>
                            <th>Daily Sales</th>
                            <th>Days Remaining</th>
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
    `;

    // Bind Inventory Controls
    const searchInput = document.getElementById('inv-search');
    const categorySelect = document.getElementById('inv-category');
    const statusSelect = document.getElementById('inv-status');

    function applyInventoryFilters() {
        const q = (searchInput.value || '').toLowerCase().strip ? searchInput.value.toLowerCase().trim() : searchInput.value.toLowerCase();
        const cat = categorySelect.value;
        const stat = statusSelect.value;

        const filtered = state.inventoryData.filter(item => {
            const matchesSearch = !q || item.product_name.toLowerCase().includes(q) || item.product_id.toLowerCase().includes(q);
            const matchesCat = cat === 'all' || item.category === cat;
            const matchesStat = stat === 'all' || item.status.toUpperCase() === stat.toUpperCase();
            return matchesSearch && matchesCat && matchesStat;
        });

        document.getElementById('inventory-table-body').innerHTML = renderInventoryTableRows(filtered);
        document.getElementById('inv-count-label').textContent = `Showing ${filtered.length} of ${state.inventoryData.length} records`;
    }

    if (searchInput) searchInput.addEventListener('input', applyInventoryFilters);
    if (categorySelect) categorySelect.addEventListener('change', applyInventoryFilters);
    if (statusSelect) statusSelect.addEventListener('change', applyInventoryFilters);
}

function renderInventoryTableRows(items) {
    if (!items || items.length === 0) {
        return `
            <tr>
                <td colspan="8" class="empty-state" style="padding: 32px; text-align: center;">
                    No products match the selected filter criteria.
                </td>
            </tr>
        `;
    }

    return items.map(item => {
        const daysDisplay = item.days_remaining_display !== 'UNAVAILABLE' ? `${item.days_remaining}d` : 'N/A';
        const badgeClass = getBadgeClassForStatus(item.status);

        return `
            <tr onclick="openProductModal('${item.product_id}')">
                <td>
                    <div style="font-weight: 600;">${item.product_name}</div>
                    <div class="subtitle" style="font-size: 11px;">${item.product_id}</div>
                </td>
                <td>${item.category}</td>
                <td>${item.store_name}</td>
                <td class="number-cell">${formatNumber(item.current_stock)}</td>
                <td class="number-cell">${item.average_daily_units_sold} u/d</td>
                <td class="number-cell">${daysDisplay}</td>
                <td><span class="badge ${badgeClass}">${item.status}</span></td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); openProductModal('${item.product_id}');">
                        Details
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

// -------------------------------------------------------------
// PAGE 3: SALES ANALYTICS
// -------------------------------------------------------------
async function renderSalesPage(container) {
    let url = `/api/sales${buildSalesQueryParams()}`;

    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to load sales analytics data.");

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
        <!-- Sales KPI Grid -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Total Revenue</div>
                <div class="kpi-value">${formatINR(summary.total_sales_amount || 0)}</div>
                <div class="kpi-sub">Period: ${summary.date_range ? summary.date_range.start_date : 'N/A'} to ${summary.date_range ? summary.date_range.end_date : 'N/A'}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Total Units Sold</div>
                <div class="kpi-value">${formatNumber(summary.total_units_sold || 0)}</div>
                <div class="kpi-sub">Total item volume</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Average Daily Revenue</div>
                <div class="kpi-value">${formatINR(summary.avg_daily_sales_amount || 0)}/day</div>
                <div class="kpi-sub">Across active observation period</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Sales Growth</div>
                <div class="kpi-value" style="color: ${growthValue >= 0 ? '#047857' : '#B91C1C'};">${growthDisplay}</div>
                <div class="kpi-sub">Recent half vs previous half</div>
            </div>
        </div>

        <!-- Sales Trend Chart -->
        <div class="section-card">
            <div class="section-header">
                <h2 class="section-title">Sales Revenue Trend</h2>
                <span class="badge badge-info">Historical Performance</span>
            </div>
            <div id="sales-chart-container" class="chart-container">
                <!-- SVG Chart injected -->
            </div>
        </div>

        <!-- Top & Bottom Product Tables -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
            <div class="section-card">
                <div class="section-header">
                    <h2 class="section-title">Top 5 Revenue Products</h2>
                </div>
                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Product</th>
                                <th>Category</th>
                                <th class="number-cell">Revenue</th>
                                <th class="number-cell">Units</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${topProducts.map(p => `
                                <tr onclick="openProductModal('${p.product_id}')">
                                    <td><strong>${p.product_name}</strong></td>
                                    <td>${p.category}</td>
                                    <td class="number-cell">${formatINR(p.total_sales_amount)}</td>
                                    <td class="number-cell">${formatNumber(p.total_units_sold)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="section-card">
                <div class="section-header">
                    <h2 class="section-title">Bottom 5 Revenue Products</h2>
                </div>
                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Product</th>
                                <th>Category</th>
                                <th class="number-cell">Revenue</th>
                                <th class="number-cell">Units</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${bottomProducts.map(p => `
                                <tr onclick="openProductModal('${p.product_id}')">
                                    <td><strong>${p.product_name}</strong></td>
                                    <td>${p.category}</td>
                                    <td class="number-cell">${formatINR(p.total_sales_amount)}</td>
                                    <td class="number-cell">${formatNumber(p.total_units_sold)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;

    renderSalesTrendSVG(document.getElementById('sales-chart-container'), data.daily_trend || []);
}

// -------------------------------------------------------------
// PAGE 4: ATTENTION REQUIRED
// -------------------------------------------------------------
async function renderAttentionPage(container) {
    let url = '/api/attention';
    if (state.selectedStore !== 'all') url += `?store_id=${state.selectedStore}`;

    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to load attention alerts.");

    const data = await res.json();
    state.attentionData = data.attention_items || [];

    container.innerHTML = `
        <div class="section-card">
            <!-- Filter Bar -->
            <div class="section-header" style="flex-wrap: wrap; gap: 12px;">
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <button class="btn btn-secondary btn-sm att-type-btn active" data-type="all">All Alerts (${data.count || 0})</button>
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

            <div id="attention-list-container" class="attention-grid">
                ${state.attentionData.length === 0 ? `
                    <div class="empty-state">
                        <p>✅ Zero active attention findings. Store operations are optimal.</p>
                    </div>
                ` : state.attentionData.map(item => renderAttentionCardHTML(item)).join('')}
            </div>
        </div>
    `;

    // Filter Handlers
    const typeBtns = container.querySelectorAll('.att-type-btn');
    const sevSelect = container.querySelector('#att-severity-select');

    let activeType = 'all';
    let activeSev = 'all';

    function filterAttentionList() {
        const filtered = state.attentionData.filter(item => {
            const matchType = activeType === 'all' || item.attention_type === activeType;
            const matchSev = activeSev === 'all' || item.severity === activeSev;
            return matchType && matchSev;
        });

        const listContainer = document.getElementById('attention-list-container');
        if (filtered.length === 0) {
            listContainer.innerHTML = `<div class="empty-state"><p>No attention items match the selected filter criteria.</p></div>`;
        } else {
            listContainer.innerHTML = filtered.map(item => renderAttentionCardHTML(item)).join('');
        }
    }

    typeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            typeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeType = btn.getAttribute('data-type');
            filterAttentionList();
        });
    });

    if (sevSelect) {
        sevSelect.addEventListener('change', (e) => {
            activeSev = e.target.value;
            filterAttentionList();
        });
    }
}

function renderAttentionCardHTML(item) {
    const badgeClass = getBadgeClassForSeverity(item.severity);
    const typeLabel = item.attention_type.replace(/_/g, ' ');

    return `
        <div class="attention-card ${item.severity.toLowerCase()}">
            <div class="attention-card-header">
                <div>
                    <span class="badge ${badgeClass}">${item.severity}</span>
                    <span class="badge badge-info" style="margin-left: 6px;">${typeLabel}</span>
                </div>
                <div class="attention-store">${item.store_name}</div>
            </div>

            <div>
                <div class="attention-title" onclick="openProductModal('${item.product_id}')" style="cursor: pointer;">
                    ${item.product_name} <span class="subtitle">(${item.product_id})</span>
                </div>
                <p style="font-size: 13px; color: var(--text-secondary); margin-top: 4px;">
                    ${item.metric_summary}
                </p>
            </div>

            <!-- Factual Evidence Box -->
            <div class="evidence-box">
                <div style="font-weight: 700; color: var(--text-primary); margin-bottom: 4px;">📊 Factual Evidence (Python Engine)</div>
                <div><strong>Metric:</strong> ${item.evidence.metric || 'N/A'}</div>
                <div><strong>Observation Period:</strong> ${item.evidence.calculation_period || 'Historical 90-day window'}</div>
                <div><strong>Threshold Applied:</strong> ${item.evidence.threshold_used || 'Centralized Business Rule'}</div>
            </div>

            <!-- Decision-Support Recommendation -->
            <div class="recommendation-box">
                <strong>💡 Recommended Action:</strong> ${item.recommendation}
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: var(--text-muted);">
                <span>Assumptions: ${item.assumptions ? item.assumptions[0] : 'Historical velocity continuation.'}</span>
                <span class="badge badge-healthy">Data: ${item.data_sufficiency}</span>
            </div>
        </div>
    `;
}

// -------------------------------------------------------------
// PAGE 5: AI COPILOT PLACEHOLDER
// -------------------------------------------------------------
let copilotHistory = [];
let copilotLastIntent = null;
let copilotLastProductId = null;

function renderCopilotPage(container) {
    container.innerHTML = `
        <div class="copilot-container">
            <div class="copilot-header-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                    <div>
                        <h2 style="font-size: 20px; font-weight: 700; color: var(--text-primary);">🤖 Ask ShelfIQ</h2>
                        <p class="subtitle">Get evidence-based answers about your sales and inventory.</p>
                    </div>
                    <span class="badge badge-healthy">Grounded AI Active</span>
                </div>

                <div style="margin-top: 16px;">
                    <div class="copilot-section-title">💡 Sample Questions You Can Ask:</div>
                    <div class="sample-questions-grid">
                        <div class="sample-pill" onclick="askCopilotQuestion('What needs attention today?')">
                            <span>⚠️</span> What needs attention today?
                        </div>
                        <div class="sample-pill" onclick="askCopilotQuestion('Which products may run out soon?')">
                            <span>🚨</span> Which products may run out soon?
                        </div>
                        <div class="sample-pill" onclick="askCopilotQuestion('What is overstocked?')">
                            <span>📦</span> What is overstocked?
                        </div>
                        <div class="sample-pill" onclick="askCopilotQuestion('Which products are selling slowly?')">
                            <span>📉</span> Which products are selling slowly?
                        </div>
                        <div class="sample-pill" onclick="askCopilotQuestion('Did sales spike anywhere?')">
                            <span>🚀</span> Did sales spike anywhere?
                        </div>
                        <div class="sample-pill" onclick="askCopilotQuestion('How are my sales performing?')">
                            <span>📊</span> How are my sales performing?
                        </div>
                    </div>
                </div>

                <form id="copilot-form" onsubmit="handleCopilotSubmit(event)" class="copilot-input-area">
                    <input type="text" id="copilot-input" class="form-input" placeholder="Ask a question about inventory, sales, products, or stores..." autocomplete="off">
                    <button type="submit" id="btn-copilot-submit" class="btn btn-primary">
                        Send ➔
                    </button>
                </form>
            </div>

            <!-- Loading State Container -->
            <div id="copilot-loading" class="loading-state hidden">
                <div style="font-size: 15px; font-weight: 600; color: var(--primary-color);">⌛ Analyzing your store data...</div>
                <p style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">Fetching deterministic evidence and synthesizing grounded decision support.</p>
            </div>

            <!-- Results Viewport -->
            <div id="copilot-results" style="display: flex; flex-direction: column; gap: 20px;">
                ${copilotHistory.length === 0 ? `
                    <div class="empty-state">
                        <div style="font-size: 32px; margin-bottom: 8px;">📊</div>
                        <div style="font-weight: 600; color: var(--text-primary);">No questions asked yet.</div>
                        <p style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">Click any sample question above or type your query in the search box.</p>
                    </div>
                ` : copilotHistory.map(item => renderCopilotResponseHTML(item)).join('')}
            </div>
        </div>
    `;
}

async function handleCopilotSubmit(e) {
    if (e) e.preventDefault();
    const input = document.getElementById('copilot-input');
    if (!input || !input.value.trim()) return;

    const q = input.value.trim();
    input.value = '';
    await askCopilotQuestion(q);
}

async function askCopilotQuestion(questionText) {
    const loading = document.getElementById('copilot-loading');
    const submitBtn = document.getElementById('btn-copilot-submit');

    if (loading) loading.classList.remove('hidden');
    if (submitBtn) submitBtn.disabled = true;

    // Get active store filter from navbar dropdown if set
    const storeSelect = document.getElementById('store-select');
    const selectedStore = (storeSelect && storeSelect.value !== 'all') ? storeSelect.value : null;

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
            throw new Error(errData.detail || "Copilot query failed");
        }

        const data = await res.json();
        copilotLastIntent = data.intent;

        // Track product ID if present in evidence
        if (data.evidence && data.evidence.length > 0 && data.evidence[0].product_id) {
            copilotLastProductId = data.evidence[0].product_id;
        }

        copilotHistory.unshift(data);
        const resultsContainer = document.getElementById('copilot-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = copilotHistory.map(item => renderCopilotResponseHTML(item)).join('');
        }
    } catch (err) {
        const resultsContainer = document.getElementById('copilot-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = renderCopilotErrorHTML() + copilotHistory.map(item => renderCopilotResponseHTML(item)).join('');
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
    const suffClass = data.data_sufficiency === 'SUFFICIENT' ? 'badge-healthy' :
                      data.data_sufficiency === 'LIMITED' ? 'badge-medium' : 'badge-critical';

    const supportingNumbersHTML = supportingNumbers.length > 0 ? `
        <div>
            <div class="copilot-section-title">📊 Supporting Numbers</div>
            <div class="supporting-numbers-grid">
                ${supportingNumbers.map(num => `
                    <div class="supporting-number-card">
                        <div style="font-size: 11px; font-weight: 600; color: var(--text-muted);">${escapeHTML(num.product_name || 'Retail Metric')}</div>
                        <div style="font-size: 16px; font-weight: 700; color: var(--text-primary);">${escapeHTML(num.value)}</div>
                        <div style="font-size: 11px; color: var(--text-secondary);">${escapeHTML(num.metric)} (${escapeHTML(num.store_name || 'All Stores')})</div>
                    </div>
                `).join('')}
            </div>
        </div>
    ` : '';

    const evidenceHTML = evidence.length > 0 ? `
        <div>
            <div class="copilot-section-title">🔎 Factual Evidence (Python Backend)</div>
            ${evidence.map(ev => {
                const sourceLabel = escapeHTML(ev.source || "Inventory analysis");
                const pName = ev.product_name ? `${escapeHTML(ev.product_name)} (${escapeHTML(ev.product_id || '')})` : '';
                const sName = ev.store_name ? `@ ${escapeHTML(ev.store_name)}` : '';
                const details = ev.supporting_values ? escapeHTML(JSON.stringify(ev.supporting_values).replace(/["{}]/g, '')) : '';
                return `
                    <div class="evidence-item-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span class="source-badge">Source: ${sourceLabel}</span>
                            <span style="font-size: 11px; color: var(--text-muted);">Period: ${escapeHTML(ev.period || 'Last 90 days')}</span>
                        </div>
                        <div><strong>${pName} ${sName}</strong></div>
                        <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">
                            <strong>Metric:</strong> ${escapeHTML(ev.metric || 'metric_value')} = ${escapeHTML(ev.value)}
                            ${details ? ` | <span>Details: ${details}</span>` : ''}
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    ` : '';

    return `
        <div class="copilot-response-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid var(--border-color); padding-bottom: 12px;">
                <div>
                    <span style="font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">User Question</span>
                    <h3 style="font-size: 16px; font-weight: 700; color: var(--text-primary); margin-top: 2px;">"${escapeHTML(data.question || '')}"</h3>
                </div>
                <span class="badge ${suffClass}">Data: ${escapeHTML(data.data_sufficiency || 'INSUFFICIENT')}</span>
            </div>

            <!-- Executive Answer -->
            <div>
                <div class="copilot-section-title">💬 Answer</div>
                <div class="copilot-answer-text">
                    ${escapeHTML(data.answer || 'Analysis complete.')}
                </div>
            </div>

            ${supportingNumbersHTML}
            ${evidenceHTML}

            <!-- Key Points -->
            ${keyPoints.length > 0 ? `
                <div>
                    <div class="copilot-section-title">📌 Key Takeaways</div>
                    <ul style="padding-left: 20px; font-size: 13px; color: var(--text-primary); display: flex; flex-direction: column; gap: 4px;">
                        ${keyPoints.map(kp => `<li>${escapeHTML(kp)}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}

            <!-- Recommended Action Callout -->
            <div class="recommendation-box">
                <strong>💡 Recommended Action:</strong> ${escapeHTML(data.recommendation || 'Continue standard inventory monitoring.')}
            </div>

            <!-- Assumptions & Transparency -->
            <div style="font-size: 11px; color: var(--text-muted); border-top: 1px solid var(--border-color); padding-top: 12px; display: flex; justify-content: space-between;">
                <span><strong>Assumptions:</strong> ${escapeHTML(assumptions.length > 0 ? assumptions[0] : 'Based on factual daily sales velocity.')}</span>
                <span><strong>Intent:</strong> ${escapeHTML(data.intent || 'UNKNOWN')}</span>
            </div>
        </div>
    `;
}

function renderCopilotErrorHTML() {
    return `
        <div class="copilot-error-card">
            <div class="error-icon">!</div>
            <div class="error-body">
                <div class="error-title">Copilot is temporarily unavailable</div>
                <div class="error-message">Please try again in a moment. Backend details and credentials remain hidden.</div>
            </div>
        </div>
    `;
}

function escapeHTML(value) {
    return String(value === null || value === undefined ? '' : value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// -------------------------------------------------------------
// PAGE 6: SETTINGS
// -------------------------------------------------------------
async function renderSettingsPage(container) {
    const res = await fetch('/api/health');
    const health = res.ok ? await res.json() : {};

    container.innerHTML = `
        <div class="section-card" style="max-width: 700px;">
            <div class="section-header">
                <h2 class="section-title">System Settings & Data Status</h2>
            </div>
            
            <div style="display: flex; flex-direction: column; gap: 16px;">
                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-color); padding-bottom: 12px;">
                    <strong>Application Version:</strong>
                    <span>ShelfIQ v1.0.0</span>
                </div>
                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-color); padding-bottom: 12px;">
                    <strong>Backend Status:</strong>
                    <span class="badge badge-healthy">${health.status || 'OK'}</span>
                </div>
                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-color); padding-bottom: 12px;">
                    <strong>CSV Data Load Status:</strong>
                    <span class="badge ${health.data_loaded ? 'badge-healthy' : 'badge-critical'}">${health.data_loaded ? 'LOADED & VALIDATED' : 'FAILED'}</span>
                </div>
                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-color); padding-bottom: 12px;">
                    <strong>Supported Stores:</strong>
                    <span>4 Stores (Hyderabad Central, Banjara Hills, Kukatpally, Secunderabad)</span>
                </div>
                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-color); padding-bottom: 12px;">
                    <strong>Catalogue Size:</strong>
                    <span>55 Products across 6 Categories</span>
                </div>
            </div>
        </div>
    `;
}

// -------------------------------------------------------------
// PRODUCT DETAIL MODAL
// -------------------------------------------------------------
async function openProductModal(productId) {
    const modal = document.getElementById('product-modal');
    const body = document.getElementById('modal-body');
    const nameEl = document.getElementById('modal-product-name');
    const subEl = document.getElementById('modal-product-sub');

    if (!modal || !body) return;

    body.innerHTML = '<div class="loading-state">Loading product details...</div>';
    modal.classList.remove('hidden');

    try {
        const res = await fetch(`/api/products/${productId}`);
        if (!res.ok) throw new Error("Product not found");

        const data = await res.json();
        
        nameEl.textContent = data.product_name;
        subEl.textContent = `ID: ${data.product_id} | Category: ${data.category}`;

        const perf = data.sales_performance || {};

        body.innerHTML = `
            <div class="kpi-grid" style="grid-template-columns: 1fr 1fr 1fr; margin-bottom: 20px;">
                <div class="kpi-card">
                    <div class="kpi-label">Unit Price</div>
                    <div class="kpi-value">${formatINR(data.unit_price)}</div>
                    <div class="kpi-sub">Cost: ${formatINR(data.cost_price)}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Total Units Sold</div>
                    <div class="kpi-value">${formatNumber(perf.total_units_sold || 0)}</div>
                    <div class="kpi-sub">Revenue: ${formatINR(perf.total_sales_amount || 0)}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Sales Trend</div>
                    <div class="kpi-value">${perf.sales_trend || 'STABLE'}</div>
                    <div class="kpi-sub">Avg ${perf.avg_daily_units || 0} u/day</div>
                </div>
            </div>

            <h4 style="margin-bottom: 12px;">Store Inventory Breakdown</h4>
            <div class="table-container" style="margin-bottom: 20px;">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Store</th>
                            <th>Current Stock</th>
                            <th>Daily Sales</th>
                            <th>Days Left</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.inventory_metrics.map(inv => `
                            <tr>
                                <td>${inv.store_name}</td>
                                <td class="number-cell">${formatNumber(inv.current_stock)}</td>
                                <td class="number-cell">${inv.average_daily_units_sold} u/d</td>
                                <td class="number-cell">${inv.days_remaining_display}</td>
                                <td><span class="badge ${getBadgeClassForStatus(inv.status)}">${inv.status}</span></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>

            ${data.attention_items && data.attention_items.length > 0 ? `
                <h4 style="margin-bottom: 12px;">Active Operational Alerts</h4>
                <div class="attention-grid">
                    ${data.attention_items.map(item => renderAttentionCardHTML(item)).join('')}
                </div>
            ` : '<p style="color: var(--text-muted); font-size: 13px;">No critical alerts active for this product.</p>'}
        `;
    } catch (err) {
        body.innerHTML = `<div class="error-state">Failed to load details for product ${productId}.</div>`;
    }
}

// -------------------------------------------------------------
// CUSTOM OFFLINE SVG CHART RENDERER
// -------------------------------------------------------------
function renderSalesTrendSVG(container, dailyTrend = []) {
    if (!container) return;

    const trend = Array.isArray(dailyTrend) ? dailyTrend : [];
    if (trend.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>Not enough sales data to render a trend chart.</p>
            </div>
        `;
        return;
    }

    const recentTrend = trend.slice(-30);
    const salesPoints = recentTrend.map(item => Number(item.sales_amount) || 0);

    const maxVal = Math.max(...salesPoints, 100) * 1.15;
    const width = 600;
    const height = 210;
    const paddingBottom = 26;
    const paddingTop = 15;
    const chartHeight = height - paddingBottom - paddingTop;
    const barWidth = Math.max(6, (width / salesPoints.length) - 6);

    // Generate SVG bars with blue gradient fill
    const svgBars = salesPoints.map((val, idx) => {
        const barHeight = Math.max(4, (val / maxVal) * chartHeight);
        const x = idx * (barWidth + 6) + 12;
        const y = height - paddingBottom - barHeight;
        const dateStr = recentTrend[idx].date || '';

        return `
            <rect class="chart-bar" x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" rx="4" fill="url(#barGrad)">
                <title>${escapeHTML(dateStr)}: ${formatINR(val)}</title>
            </rect>
        `;
    }).join('');

    // Generate ~5 evenly spaced X-axis date labels
    const step = Math.ceil(recentTrend.length / 5);
    const dateLabels = recentTrend.map((item, idx) => {
        if (idx % step === 0 || idx === recentTrend.length - 1) {
            const x = idx * (barWidth + 6) + 12 + barWidth / 2;
            const dateParts = item.date ? item.date.split('-') : [];
            const label = dateParts.length === 3 ? `${dateParts[1]}/${dateParts[2]}` : item.date;
            return `<text class="chart-axis-text" x="${x}" y="${height - 6}" text-anchor="middle">${escapeHTML(label)}</text>`;
        }
        return '';
    }).join('');

    // Horizontal grid lines
    const gridY1 = height - paddingBottom - chartHeight * 0.5;
    const gridY2 = height - paddingBottom - chartHeight * 0.95;

    container.innerHTML = `
        <svg class="svg-chart" viewBox="0 0 ${width} ${height}">
            <defs>
                <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#3B82F6"/>
                    <stop offset="100%" stop-color="#1D4ED8"/>
                </linearGradient>
            </defs>
            <line x1="10" y1="${gridY1}" x2="${width - 10}" y2="${gridY1}" stroke="#E2E8F0" stroke-width="1" stroke-dasharray="4" />
            <line x1="10" y1="${gridY2}" x2="${width - 10}" y2="${gridY2}" stroke="#E2E8F0" stroke-width="1" stroke-dasharray="4" />
            <line x1="10" y1="${height - paddingBottom}" x2="${width - 10}" y2="${height - paddingBottom}" stroke="#CBD5E1" stroke-width="1" />
            ${svgBars}
            ${dateLabels}
        </svg>
    `;
}

// -------------------------------------------------------------
// UTILITY HELPERS
// -------------------------------------------------------------
function formatINR(val) {
    if (val === null || val === undefined || isNaN(val)) return '₹0.00';
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(val);
}

function formatNumber(val) {
    if (val === null || val === undefined || isNaN(val)) return '0';
    return new Intl.NumberFormat('en-IN').format(val);
}

function getBadgeClassForStatus(status) {
    switch ((status || '').toUpperCase()) {
        case 'CRITICAL': return 'badge-critical';
        case 'HIGH': case 'LOW STOCK': return 'badge-high';
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
