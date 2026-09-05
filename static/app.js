/**
 * ShelfIQ - Retail Sales & Inventory Copilot
 * Frontend application client script
 */

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    loadPage('dashboard');
});

function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item[data-page]');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.getAttribute('data-page');
            
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            loadPage(page);
        });
    });
}

function loadPage(pageName) {
    const titleEl = document.getElementById('page-title');
    const subtitleEl = document.getElementById('page-subtitle');
    const viewport = document.getElementById('content-viewport');

    const pageTitles = {
        dashboard: { title: 'Dashboard', subtitle: "Good morning. Here's what needs your attention today." },
        inventory: { title: 'Inventory Management', subtitle: 'Monitor stock levels, daily sales velocity, and stock-out risks.' },
        sales: { title: 'Sales Analytics', subtitle: 'Analyze revenue, units sold, and growth trends across products & stores.' },
        attention: { title: 'Attention Required', subtitle: 'Critical operational findings and actionable recommendations.' },
        copilot: { title: 'Ask ShelfIQ', subtitle: 'Ask questions about your sales, inventory, and store operations.' },
        settings: { title: 'Settings', subtitle: 'Manage application configuration and data sources.' }
    };

    const config = pageTitles[pageName] || { title: 'ShelfIQ', subtitle: '' };
    titleEl.textContent = config.title;
    subtitleEl.textContent = config.subtitle;

    viewport.innerHTML = `
        <div style="background: white; padding: 24px; border-radius: 8px; border: 1px solid #E2E8F0;">
            <h3>${config.title} Placeholder</h3>
            <p style="color: #64748B; margin-top: 8px;">Phase 1 skeleton initialization complete. Core logic will be populated in subsequent phases.</p>
        </div>
    `;
}
