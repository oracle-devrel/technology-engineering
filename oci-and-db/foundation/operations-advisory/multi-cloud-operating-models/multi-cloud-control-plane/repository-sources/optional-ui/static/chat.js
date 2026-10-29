/* Only the server's HTML-disabled Markdown renderer supplies bubble HTML. */
(() => {
    let active = null;
    let view = null;
    let transcript = [];
    let project = null;
    let needsReset = false;
    let panel = null;
    let panelRevision = 0;
    let pendingRefresh = null;
    let conversationId = null;
    let restoring = null;
    let restoreTimer = null;
    let remoteBusy = false;
    let resetting = false;

    let followTimer = null;
    let followDelay = 20000;
    let followStopped = false;
    let navigationRequest = null;
    let renderedPanel = null;
    let renderedRoot = null;

    function locked() {
        return Boolean(active || remoteBusy || restoring || resetting);
    }

    function terminal() {
        const stages = panel && panel.stages || [];
        return stages[3]?.state === 'closed' ||
            (stages[3]?.state === 'done' && ['done', 'failed'].includes(stages[4]?.state));
    }

    function scopeMatches(root) {
        const selector = document.getElementById('projectSelector');
        return !selector || selector.value === root.dataset.project;
    }

    function canFollow(root) {
        return view === root && root?.isConnected && !document.hidden && !locked() &&
            !needsReset && !followStopped && !navigationRequest && scopeMatches(root) && panel?.kind === 'pr' && !terminal();
    }

    function updateFollowing(root) {
        const following = root.querySelector('[data-chat-following]');
        following.hidden = !canFollow(root);
        const stages = panel?.stages || [];
        let text = '';
        let tone = 'text-muted';
        if (panel?.kind === 'pr') {
            if (stages[3]?.state === 'closed') text = 'PR closed without merge.';
            else if (stages[3]?.state === 'done') {
                if (stages[4]?.state === 'done') { text = 'Execution completed'; tone = 'text-success'; }
                else if (stages[4]?.state === 'failed') { text = 'Execution failed'; tone = 'text-error'; }
                else if (stages[4]?.state === 'unknown') text = 'Execution not verified. Open GitHub for details.';
                else text = 'Execution in progress. Waiting for verified execution evidence.';
            } else if (stages.some(step => step.state === 'unknown')) text = 'Status not verified. Retrying automatically when the chat is visible.';
            else if (stages[2]?.state === 'done') text = 'Waiting for independent human review and merge in GitHub.';
            else if (stages[2]?.state === 'failed') text = 'Checks failed. Following further commits.';
            else text = 'Checks in progress.';
        }
        const note = root.querySelector('[data-chat-panel-status]');
        if (note.textContent !== text) note.textContent = text;
        note.className = 'text-sm ' + tone;
    }

    function cancelFollowing() {
        clearTimeout(followTimer);
        followTimer = null;
        panelRevision += 1;
        if (pendingRefresh) pendingRefresh.abort();
        if (view) updateFollowing(view);
    }

    function scheduleFollowing(root) {
        clearTimeout(followTimer);
        followTimer = null;
        updateFollowing(root);
        if (canFollow(root) && !pendingRefresh) {
            followTimer = setTimeout(() => { followTimer = null; refreshPanel(root); }, followDelay);
        }
    }

    async function refreshPanel(root) {
        if (view !== root || !root.isConnected || document.hidden || locked() || needsReset || followStopped || navigationRequest || !scopeMatches(root) || panel?.kind !== 'pr') return;
        if (pendingRefresh) return;
        clearTimeout(followTimer);
        followTimer = null;
        const revision = panelRevision;
        const selectedProject = root.dataset.project;
        const selectedConversation = conversationId;
        const selectedPanel = panel;
        const controller = new AbortController();
        pendingRefresh = controller;
        renderControls(root);
        const current = () => view === root && revision === panelRevision && !controller.signal.aborted &&
            !navigationRequest && scopeMatches(root) && project === selectedProject && conversationId === selectedConversation && panel === selectedPanel && !locked();
        try {
            const response = await fetch('/api/chat/panel', {
                method: 'POST', headers: {'Content-Type': 'application/json'}, cache: 'no-store',
                body: JSON.stringify({project: selectedProject, conversation_id: selectedConversation}), signal: controller.signal
            });
            if (!current()) return;
            if ([401, 403, 410].includes(response.status)) {
                followStopped = true;
                needsReset = true;
                root.querySelector('[data-chat-status]').textContent = response.status === 403 ?
                    'Project write access is required. Sign in again.' : 'The chat expired. Select New chat or sign in again.';
                if (response.status === 401) window.location.assign('/login');
                return;
            }
            if (response.status === 409) { followDelay = 20000; return; }
            if (!response.ok) throw new Error('Unable to refresh. Status not verified.');
            const result = await response.json();
            if (!current()) return;
            panel = result.panel;
            followDelay = panel?.stages?.some(step => step.state === 'unknown') ? 60000 : 20000;
            renderPanel(root);
        } catch (error) {
            if (!current()) return;
            followDelay = 60000;
            panel = {...panel, source: 'Refresh failed. Previous GitHub status is no longer verified.',
                stages: panel.stages.map(step => ({...step, state: 'unknown', detail: 'Refresh required.'}))};
            renderPanel(root);
        } finally {
            if (pendingRefresh === controller) pendingRefresh = null;
            if (view) { renderControls(view); scheduleFollowing(view); }
        }
    }

    function renderPanel(root) {
        const content = root.querySelector('[data-chat-panel-content]');
        const intro = root.querySelector('[data-chat-panel-intro]');
        const stages = root.querySelector('[data-chat-stages]');
        const source = root.querySelector('[data-chat-panel-source]');
        const link = root.querySelector('[data-chat-pr-link]');
        const refresh = root.querySelector('[data-chat-panel-refresh]');
        const fingerprint = JSON.stringify({...panel, checked_at: null, needsReset});
        updateFollowing(root);
        if (renderedRoot === root && renderedPanel === fingerprint) {
            source.textContent = panel ? panel.source : 'Deployment status comes from GitHub evidence.';
            if (panel?.checked_at) source.textContent += ' · Checked ' + new Date(panel.checked_at).toLocaleTimeString();
            if (panel && needsReset) source.textContent += ' · Chat stopped; start a new chat before continuing.';
            return;
        }
        renderedRoot = root;
        renderedPanel = fingerprint;
        content.replaceChildren();
        link.hidden = true;
        link.removeAttribute('href');
        refresh.hidden = true;
        refresh.disabled = locked() || Boolean(pendingRefresh) || needsReset;
        root.querySelector('form [type=submit]').disabled = locked() || needsReset;

        intro.textContent = panel ? (panel.kind === 'proposal' ? 'Proposed change · awaiting confirmation' : panel.title || 'Pull request evidence') : 'No active request. A proposal will appear here when its candidate is ready.';
        const list = document.createElement('dl');
        function field(label, value, code = false) {
            const dt = document.createElement('dt');
            dt.textContent = label;
            const dd = document.createElement('dd');
            dd.textContent = value;
            if (code) dd.className = 'chat-summary-code';
            list.append(dt, dd);
        }
        if (panel) {
            field('Project', panel.project);
            field('Scope', 'OCI · ' + panel.environment + ' · ' + panel.region);
            if (panel.crq) field('Change request', panel.crq, true);
            if (panel.operation_type) field('Operation', panel.operation_type);
            if (panel.summary) field('Action', panel.summary);
            for (const resource of panel.resources || []) {
                const resourceView = document.createElement('div');
                resourceView.className = 'chat-summary-resource';
                const name = document.createElement('strong');
                name.textContent = resource.name;
                const details = document.createElement('small');
                details.textContent = resource.details || resource.key;
                resourceView.append(name, details);
                content.append(resourceView);
            }
            if (panel.manifest_path) field('Manifest', panel.manifest_path, true);
            if (panel.files) field('Changed files', panel.files.join('\n'), true);
            if (panel.secret_keys && panel.secret_keys.length) field('Runtime secret keys · values stay outside chat', panel.secret_keys.join(', '), true);
            content.append(list);
            if (panel.kind === 'pr' && Number.isInteger(panel.pr_number) && panel.pr_number > 0) {
                link.href = 'https://github.com/multicloud-control-plane/' + encodeURIComponent(root.dataset.project) + '/pull/' + panel.pr_number;
                link.textContent = 'Open PR #' + panel.pr_number;
                link.hidden = false;
                refresh.hidden = false;
            }
        }
        const labels = ['Proposal', 'Confirmation', 'PR & checks', 'Review & merge', 'Execution'];
        const states = {waiting: 'Waiting', done: 'Verified', current: 'In progress', failed: 'Failed', unknown: 'Not verified', external: 'Recorded outside this panel', closed: 'Closed'};
        stages.replaceChildren();
        labels.forEach((label, index) => {
            const step = panel && panel.stages ? panel.stages[index] : null;
            const state = step && states[step.state] ? step.state : 'waiting';
            const row = document.createElement('li');
            row.dataset.state = state;
            const marker = document.createElement('span');
            marker.className = 'chat-step-marker';
            marker.setAttribute('aria-hidden', 'true');
            marker.textContent = state === 'done' ? '✓' : String(index + 1);
            const text = document.createElement('div');
            const title = document.createElement('strong');
            title.textContent = label;
            const detail = document.createElement('span');
            detail.className = 'chat-step-state';
            detail.textContent = (step && step.detail) || states[state];
            text.append(title, detail);
            row.append(marker, text);
            stages.append(row);
        });
        source.textContent = panel ? panel.source : 'Deployment status comes from GitHub evidence.';
        if (panel && panel.checked_at) source.textContent += ' · Checked ' + new Date(panel.checked_at).toLocaleTimeString();
        if (panel && needsReset) source.textContent += ' · Chat stopped; start a new chat before continuing.';
    }

    function renderAnswer(bubble, answer) {
        if (typeof answer.html === 'string') {
            bubble.classList.remove('whitespace-pre-wrap');
            bubble.classList.add('chat-markdown');
            bubble.innerHTML = answer.html;
            bubble.querySelectorAll('a[href]').forEach(link => {
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
            });
        } else {
            bubble.textContent = answer.text;
        }
    }

    function message(root, role, text, html) {
        const row = document.createElement('div');
        row.className = role === 'You' ? 'chat chat-end' : 'chat chat-start';
        const label = document.createElement('div');
        label.className = 'chat-header text-xs opacity-60';
        label.textContent = role === 'Project GitOps' ? 'AI Operations' : role;
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble whitespace-pre-wrap break-words max-w-full';
        bubble.textContent = text;
        if (role === 'Project GitOps') renderAnswer(bubble, {text, html});
        row.append(label, bubble);
        root.querySelector('[data-chat-messages]').append(row);
        return bubble;
    }

    function renderControls(root) {
        root.querySelector('form [type=submit]').disabled = locked() || needsReset;
        root.querySelector('[data-chat-reset]').disabled = Boolean(active || remoteBusy || resetting);
        root.querySelector('[data-chat-stop]').disabled = !active;
        root.querySelector('[data-chat-panel-refresh]').disabled = locked() || Boolean(pendingRefresh) || needsReset;
        root.querySelector('[data-chat-starters]').hidden = transcript.length > 0;
        root.querySelectorAll('[data-chat-starter]').forEach(button => { button.disabled = locked() || needsReset; });
    }

    function renderTranscript(root) {
        root.querySelector('[data-chat-messages]').replaceChildren();
        for (const item of transcript) message(root, item.role, item.text, item.html);
        const log = root.querySelector('[data-chat-messages]');
        log.scrollTop = log.scrollHeight;
    }

    function cancelRecovery() {
        if (restoring) restoring.abort();
        restoring = null;
        clearTimeout(restoreTimer);
        restoreTimer = null;
    }

    async function restore(root) {
        if (resetting) { renderControls(root); return; }
        const controller = new AbortController();
        restoring = controller;
        renderControls(root);
        const status = root.querySelector('[data-chat-status]');
        status.textContent = 'Recovering conversation…';
        try {
            const response = await fetch('/api/chat?project=' + encodeURIComponent(root.dataset.project), {
                cache: 'no-store', signal: controller.signal
            });
            if (response.status === 401) { window.location.assign('/login'); return; }
            if (!response.ok) throw new Error('Unable to recover this chat. Select New chat or sign in again.');
            const state = await response.json();
            if (view !== root || controller.signal.aborted) return;
            if (state.project !== root.dataset.project) throw new Error('The chat scope changed. Select New chat.');
            const previous = readChatView();
            const knownId = conversationId || (previous && previous.project === project && previous.conversation_id);
            const expired = !state.exists && knownId;
            conversationId = expired ? knownId : state.conversation_id;
            // Navigation can outlive the server thread. Keep what this tab
            // already displays, but never append to a silently replaced chat.
            if (!expired) {
                followStopped = false;
                transcript = state.messages;
                panel = state.panel;
            }
            remoteBusy = state.busy;
            needsReset = Boolean(state.needs_reset || expired);
            rememberChatView(project, conversationId);
            renderTranscript(root);
            renderPanel(root);
            status.textContent = expired ? 'The chat expired or the server restarted. Messages still available in this tab are preserved. Select New chat to continue.' : state.status;
            if (remoteBusy) {
                restoreTimer = setTimeout(() => { if (view === root) restore(root); }, 1500);
            }
        } catch (error) {
            if (controller.signal.aborted || view !== root) return;
            needsReset = true;
            status.textContent = error.message;
        } finally {
            if (restoring === controller) restoring = null;
            if (view === root) { renderControls(root); followDelay = panel?.stages?.some(step => step.state === 'unknown') ? 60000 : 20000; scheduleFollowing(root); }
        }
    }

    async function reset(root) {
        cancelFollowing();
        followStopped = false;
        followDelay = 20000;
        cancelRecovery();
        if (pendingRefresh) pendingRefresh.abort();
        pendingRefresh = null;
        if (active) active.abort();
        const response = await fetch('/api/chat?project=' + encodeURIComponent(root.dataset.project), {method: 'DELETE'});
        if (response.status === 401) { window.location.assign('/login'); throw new Error('Sign in again.'); }
        if (!response.ok) throw new Error('Unable to reset chat. Sign in again if your session expired.');
        transcript = [];
        panel = null;
        conversationId = null;
        remoteBusy = false;
        needsReset = false;
        if (view && view.dataset.project === root.dataset.project) rememberChatView(root.dataset.project, null);
    }

    function init() {
        const root = document.getElementById('gitops-chat');
        if (root !== view) {
            cancelRecovery();
            cancelFollowing();
            if (pendingRefresh) pendingRefresh.abort();
            pendingRefresh = null;
            if (active) { needsReset = true; active.abort(); }
        }
        view = root;
        navigationRequest = null;
        if (!root || root.dataset.initialized) return;
        root.dataset.initialized = 'true';
        const status = root.querySelector('[data-chat-status]');
        const form = root.querySelector('form');
        const stop = root.querySelector('[data-chat-stop]');
        const fresh = root.querySelector('[data-chat-reset]');
        const refresh = root.querySelector('[data-chat-panel-refresh]');
        if (project && project !== root.dataset.project) {
            followStopped = false;
            transcript = [];
            panel = null;
            conversationId = null;
            needsReset = false;
        }
        project = root.dataset.project;
        renderTranscript(root);
        renderPanel(root);
        root.querySelectorAll('[data-chat-starter]').forEach(button => {
            button.onclick = () => {
                if (locked() || needsReset) return;
                form.elements.message.value = button.dataset.prompt;
                form.elements.message.focus();
            };
        });
        refresh.onclick = () => refreshPanel(root);
        stop.onclick = () => {
            needsReset = true;
            if (active) active.abort();
            status.textContent = 'Stopped. Your messages are preserved. Select New chat to continue.';
        };
        fresh.onclick = async () => {
            if (active || remoteBusy || resetting) return;
            resetting = true;
            cancelFollowing();
            renderControls(root);
            try {
                await reset(root);
                if (view === root) {
                    renderTranscript(root);
                    renderPanel(root);
                    root.querySelector('[data-chat-elapsed]').textContent = '';
                    status.textContent = 'New chat ready.';
                }
            } catch (error) { status.textContent = error.message; }
            finally {
                resetting = false;
                if (view && view !== root) await restore(view);
                else if (view) { renderControls(view); scheduleFollowing(view); }
            }
        };
        form.onsubmit = async (event) => {
            event.preventDefault();
            if (locked() || needsReset) return;
            const input = form.elements.message;
            const text = input.value.trim();
            if (!text) return;
            transcript.push({role: 'You', text});
            message(root, 'You', text);
            input.value = '';
            const answer = {role: 'Project GitOps', text: ''};
            transcript.push(answer);
            const bubble = message(root, answer.role, '');
            const controller = new AbortController();
            active = controller;
            cancelFollowing();
            renderControls(root);
            status.textContent = 'Connecting to AI Operations…';
            const elapsed = root.querySelector('[data-chat-elapsed]');
            const started = Date.now();
            elapsed.textContent = '0s';
            const timer = setInterval(() => { elapsed.textContent = Math.floor((Date.now() - started) / 1000) + 's'; }, 1000);
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({project: root.dataset.project, message: text, conversation_id: conversationId}), signal: controller.signal
                });
                if (!response.ok) {
                    if (response.status === 401) {
                        window.location.assign('/login');
                        throw new Error('Your session expired. Sign in again to continue.');
                    }
                    const error = await response.json();
                    throw new Error(typeof error.detail === 'string' ? error.detail : 'Unable to send this message.');
                }
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                let finished = false;
                while (true) {
                    const {value, done} = await reader.read();
                    if (done) break;
                    if (view !== root || controller.signal.aborted) break;
                    buffer += decoder.decode(value, {stream: true});
                    let end;
                    while ((end = buffer.indexOf('\n')) !== -1) {
                        const item = JSON.parse(buffer.slice(0, end));
                        buffer = buffer.slice(end + 1);
                        if (item.type === 'session') {
                            conversationId = item.conversation_id;
                            if (view === root) rememberChatView(project, conversationId);
                        } else if (item.type === 'delta') {
                            answer.text += item.text;
                            answer.html = item.html;
                            renderAnswer(bubble, answer);
                            const log = root.querySelector('[data-chat-messages]');
                            log.scrollTop = log.scrollHeight;
                        } else if (item.type === 'error') {
                            throw new Error(item.text);
                        } else if (item.type === 'status') {
                            status.textContent = item.text;
                        } else if (item.type === 'panel') {
                            panelRevision += 1;
                            panel = item.panel;
                            followDelay = panel?.stages?.some(step => step.state === 'unknown') ? 60000 : 20000;
                            if (view === root) renderPanel(root);
                        } else if (item.type === 'done') {
                            finished = true;
                            needsReset = item.status !== 'completed';
                            status.textContent = needsReset ? 'Response interrupted. Select New chat to continue.' : 'Ready.';
                        }
                    }
                }
                if (!finished) throw new Error('Connection ended. Your messages are preserved. Select New chat to continue.');
            } catch (error) {
                if (view === root) needsReset = true;
                status.textContent = error.name === 'AbortError' ? 'Stopped. Your messages are preserved. Select New chat to continue.' : error.message;
            } finally {
                clearInterval(timer);
                elapsed.textContent = Math.floor((Date.now() - started) / 1000) + 's';
                if (active === controller) active = null;
                if (view === root) { renderPanel(root); renderControls(root); scheduleFollowing(root); }
            }
        };
        return restore(root);
    }
    document.body.addEventListener('htmx:beforeRequest', event => {
        if (event.detail.target.id !== 'main') return;
        navigationRequest = event.detail.xhr;
        cancelRecovery();
        cancelFollowing();
    });
    document.body.addEventListener('htmx:afterRequest', event => {
        if (event.detail.xhr !== navigationRequest) return;
        navigationRequest = null;
        if (view) scheduleFollowing(view);
    });
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) cancelFollowing();
        else if (view) scheduleFollowing(view);
    });
    document.addEventListener('DOMContentLoaded', init);
    document.body.addEventListener('htmx:afterSwap', init);
    document.body.addEventListener('htmx:beforeSwap', (event) => {
        if (event.detail.target.id === 'main') {
            cancelFollowing();
            if (active) { needsReset = true; active.abort(); }
            view = null;
        }
    });
})();
