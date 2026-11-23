/* Project-scoped navigation shared by the existing HTMX screens. */
function chatViewKey() {
    const login = document.body.dataset.userLogin;
    return login ? 'mccp.chat.view:' + login : null;
}

function readChatView() {
    try {
        const key = chatViewKey();
        const saved = key && JSON.parse(window.sessionStorage.getItem(key) || 'null');
        return saved && typeof saved.project === 'string' ? saved : null;
    } catch (_) { return null; }
}

function rememberChatView(project, conversationId) {
    try {
        const key = chatViewKey();
        if (!key) return;
        if (!project) { window.sessionStorage.removeItem(key); return; }
        const previous = readChatView();
        const id = conversationId === undefined && previous && previous.project === project
            ? previous.conversation_id : conversationId;
        // No transcript, HTML, token or secret is saved in the browser.
        window.sessionStorage.setItem(key, JSON.stringify({project, conversation_id: id || null}));
    } catch (_) { /* Chat still works when browser storage is unavailable. */ }
}

function openProject(project) {
    const selector = document.getElementById('projectSelector');
    if (project !== undefined) selector.value = project;
    const assistant = document.querySelector('.mcp-sidebar [data-route="/partials/chat"]');
    const route = assistant
        ? '/partials/chat' : '/partials/dashboard';
    navTo(route);
}

function filterCatalog(cloud) {
    document.querySelectorAll('[data-catalog-cloud]').forEach(section => {
        section.hidden = cloud !== 'all' && section.dataset.catalogCloud !== cloud;
    });
    document.querySelectorAll('[data-catalog-filter]').forEach(button => {
        button.setAttribute('aria-pressed', String(button.dataset.catalogFilter === cloud));
    });
}

function navTo(partial) {
    const project = document.getElementById('projectSelector').value;
    if (partial.split('?')[0] === '/partials/chat') {
        if (!project) {
            htmx.ajax('GET', '/partials/chat', {target: '#main'});
            return;
        }
    }
    if (!project) {
        htmx.ajax('GET', '/partials/overview', {target: '#main'});
        return;
    }
    const separator = partial.includes('?') ? '&' : '?';
    htmx.ajax('GET', partial + separator + 'project=' + encodeURIComponent(project), {target: '#main'});
}

document.body.addEventListener('htmx:afterSwap', function (event) {
    if (event.detail.target.id !== 'main') return;
    const errorBanner = document.getElementById('request-error-banner');
    if (errorBanner) errorBanner.style.display = 'none';
    const requestUrl = new URL(event.detail.pathInfo.requestPath, window.location.origin);
    const route = requestUrl.pathname;
    const chatProject = route === '/partials/chat' ? requestUrl.searchParams.get('project') : null;
    rememberChatView(chatProject);
    const screens = {
        '/partials/overview': ['Dashboard', 'All projects · select a project to manage its infrastructure requests.'],
        '/partials/dashboard': ['Dashboard', 'Project infrastructure and pull request status'],
        '/partials/resources-catalog': ['Catalog', 'Approved resources and operations for your project'],
        '/partials/resource-form': ['Resource Request', 'Prepare a governed change from the approved catalog'],
        '/partials/operations': ['Catalog', 'Approved resources and operations for your project'],
        '/partials/operation-form': ['Operation Request', 'Review the target and supply the required values'],
        '/partials/resources': ['Resource Inventory', 'Resources declared in your project repository'],
        '/partials/cloud-regions': ['Clouds & Regions', 'Project scope across cloud providers'],
        '/partials/tree': ['Project Manifests', 'Browse the committed project configuration'],
        '/partials/manifest': ['Manifest', 'Review the declared resource configuration'],
        '/partials/resource-delete': ['Resource Removal Request', 'Review the selected resource before creating a removal request'],
        '/partials/pr-plan': ['Pull Request Checks', 'Review checks, the proposed change and execution evidence'],
        '/partials/audit': ['Activity', 'Review requests, approvals and recorded execution evidence'],
        '/partials/chat': ['AI Operations', 'Describe your intent. Review the action. Follow the result.']
    };
    const current = screens[route];
    if (current) {
        document.getElementById('pageTitle').textContent = current[0];
        document.getElementById('pageSubtitle').textContent = current[1];
        document.title = route === '/partials/chat' ? 'AI Operations' : current[0] + ' · AI Operations';
        const parents = {'/partials/overview': '/partials/dashboard', '/partials/operations': '/partials/resources-catalog', '/partials/resource-form': '/partials/resources-catalog', '/partials/operation-form': '/partials/resources-catalog', '/partials/cloud-regions': '/partials/dashboard', '/partials/tree': '/partials/resources', '/partials/manifest': '/partials/resources', '/partials/resource-delete': '/partials/resources', '/partials/pr-plan': '/partials/audit'};
        const activeRoute = parents[route] || route;
        document.querySelectorAll('.mcp-sidebar [data-route]').forEach(button => {
            const selected = button.dataset.route === activeRoute;
            button.classList.toggle('active', selected);
            if (selected) button.setAttribute('aria-current', 'page');
            else button.removeAttribute('aria-current');
        });
    }
    document.getElementById('my-drawer-2').checked = false;
    window.scrollTo({top: 0, behavior: 'instant'});
});

function showRequestError(event, fallback) {
    const xhr = event.detail.xhr;
    if (xhr && xhr.status === 401) {
        window.location.assign('/login');
        return;
    }
    let message = fallback;
    if (xhr && [400, 403, 404, 409, 429, 503].includes(xhr.status)) {
        try {
            const response = JSON.parse(xhr.responseText);
            if (typeof response.detail === 'string') message = response.detail;
        } catch (_) { /* Keep a readable fallback for HTML and proxy errors. */ }
    }
    const banner = document.getElementById('request-error-banner');
    if (banner) {
        banner.querySelector('[data-request-error]').textContent = message;
        banner.style.display = 'flex';
    }
}

document.body.addEventListener('htmx:responseError', event => {
    showRequestError(event, 'The request could not be completed. Check its current status before trying again.');
});
document.body.addEventListener('htmx:sendError', event => {
    showRequestError(event, 'The connection was interrupted. Check the local server and network, then reopen this view.');
});
document.body.addEventListener('htmx:timeout', event => {
    showRequestError(event, 'The request timed out. Check its current status before trying again.');
});

document.addEventListener('DOMContentLoaded', () => {
    const initialRoute = document.body.dataset.initialRoute || '/partials/dashboard';
    const initial = Array.from(document.querySelectorAll('.mcp-sidebar [data-route]')).find(button => button.dataset.route === initialRoute);
    if (initial) {
        initial.classList.add('active');
        initial.setAttribute('aria-current', 'page');
    }
    const saved = readChatView();
    const selector = document.getElementById('projectSelector');
    if (saved && document.querySelector('.mcp-sidebar [data-route="/partials/chat"]')
            && Array.from(selector.options).some(option => option.value && option.value === saved.project)) {
        selector.value = saved.project;
        navTo('/partials/chat');
    }
});
