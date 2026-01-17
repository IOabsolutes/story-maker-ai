/**
 * Interactive Story Generator - Polling and UI Utilities
 * Handles chapter generation status polling, toast notifications, and loading states
 */

'use strict';

/**
 * Escape HTML to prevent XSS attacks
 * @param {string} str - String to escape
 * @returns {string} Escaped string safe for HTML insertion
 */
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/**
 * Toast notification helper
 */
const Toast = {
    /**
     * Show a toast notification
     * @param {string} message - The message to display
     * @param {string} type - Type: 'success', 'error', 'warning', 'info'
     */
    show: function(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            console.warn('Toast container not found, falling back to alert');
            alert(message);
            return;
        }

        // Escape HTML to prevent XSS
        const safeMessage = escapeHtml(message);

        const bgClass = {
            success: 'bg-success',
            error: 'bg-danger',
            warning: 'bg-warning text-dark',
            info: 'bg-info text-dark',
        }[type] || 'bg-info text-dark';

        const iconClass = {
            success: 'bi-check-circle-fill',
            error: 'bi-exclamation-triangle-fill',
            warning: 'bi-exclamation-circle-fill',
            info: 'bi-info-circle-fill',
        }[type] || 'bi-info-circle-fill';

        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-white ${bgClass} border-0`;
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi ${iconClass} me-2"></i>${safeMessage}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto"
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        toastContainer.appendChild(toastEl);

        const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
        toast.show();

        toastEl.addEventListener('hidden.bs.toast', function() {
            toastEl.remove();
        });
    },

    success: function(message) { this.show(message, 'success'); },
    error: function(message) { this.show(message, 'error'); },
    warning: function(message) { this.show(message, 'warning'); },
    info: function(message) { this.show(message, 'info'); },
};

/**
 * Loading state helper for buttons
 */
const LoadingButton = {
    /**
     * Start loading state
     * @param {HTMLElement} button - The button element
     */
    start: function(button) {
        if (!button || button.disabled) return;

        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
            Loading...
        `;
    },

    /**
     * Stop loading state
     * @param {HTMLElement} button - The button element
     */
    stop: function(button) {
        if (!button) return;

        button.disabled = false;
        if (button.dataset.originalText) {
            button.innerHTML = button.dataset.originalText;
            delete button.dataset.originalText;
        }
    },
};

/**
 * Polling module for chapter generation status
 */
const ChapterPolling = (function() {
    // Configuration
    const CONFIG = {
        POLL_INTERVAL: 5000,  // 5 seconds
        MAX_POLLS: 60,        // 5 minutes max (60 * 5s = 300s)
    };

    // State
    let pollCount = 0;
    let pollTimer = null;
    let startTime = null;
    let elapsedTimer = null;

    // DOM elements (cached)
    let container = null;
    let progressBar = null;
    let statusText = null;
    let elapsedTimeEl = null;

    /**
     * Get CSRF token from meta tag or cookie
     */
    function getCSRFToken() {
        // Try meta tag first
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.content;
        }

        // Fall back to cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return decodeURIComponent(value);
            }
        }
        return null;
    }

    /**
     * Initialize polling if generation is in progress
     */
    function init() {
        container = document.getElementById('story-container');
        if (!container) return;

        const isGenerating = container.dataset.isGenerating === 'true';
        const taskId = container.dataset.taskId;

        if (!isGenerating || !taskId) {
            console.log('Polling: No active generation task');
            return;
        }

        console.log('Polling: Starting for task', taskId);

        // Cache DOM elements
        progressBar = document.getElementById('progress-bar');
        statusText = document.getElementById('status-text');
        elapsedTimeEl = document.getElementById('elapsed-time');

        // Start polling
        startTime = Date.now();
        startElapsedTimer();
        poll(taskId);
    }

    /**
     * Update elapsed time display
     */
    function startElapsedTimer() {
        elapsedTimer = setInterval(function() {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            if (elapsedTimeEl) {
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;
                if (minutes > 0) {
                    elapsedTimeEl.textContent = `Elapsed: ${minutes}m ${seconds}s`;
                } else {
                    elapsedTimeEl.textContent = `Elapsed: ${seconds}s`;
                }
            }
        }, 1000);
    }

    /**
     * Stop all timers
     */
    function stopTimers() {
        if (pollTimer) {
            clearTimeout(pollTimer);
            pollTimer = null;
        }
        if (elapsedTimer) {
            clearInterval(elapsedTimer);
            elapsedTimer = null;
        }
    }

    /**
     * Update progress bar
     * @param {number} percentage - Progress percentage (0-100)
     */
    function updateProgress(percentage) {
        if (progressBar) {
            progressBar.style.width = percentage + '%';
            progressBar.setAttribute('aria-valuenow', percentage);
        }
    }

    /**
     * Update status text
     * @param {string} text - Status message
     * @param {boolean} isSuccess - Whether this is a success state
     */
    function updateStatus(text, isSuccess = false) {
        if (statusText) {
            statusText.textContent = text;
        }
        if (isSuccess && progressBar) {
            progressBar.classList.remove('progress-bar-animated', 'progress-bar-striped');
            progressBar.classList.add('bg-success');
        }
    }

    /**
     * Poll task status
     * @param {string} taskId - The Celery task ID
     */
    async function poll(taskId) {
        if (pollCount >= CONFIG.MAX_POLLS) {
            stopTimers();
            updateStatus('Generation is taking longer than expected. Please refresh the page.');
            Toast.warning('Generation timed out. Please refresh the page to check status.');
            return;
        }

        pollCount++;

        // Update progress (10% base + 1.5% per poll, max 90%)
        const progress = Math.min(10 + (pollCount * 1.5), 90);
        updateProgress(progress);

        try {
            const csrfToken = getCSRFToken();
            const apiUrl = `/api/task-status/${taskId}/`;

            const response = await fetch(apiUrl, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                credentials: 'same-origin',
            });

            if (!response.ok) {
                if (response.status === 404) {
                    // Task not found - might have been cleaned up
                    console.log('Polling: Task not found, reloading page');
                    location.reload();
                    return;
                }
                throw new Error(`HTTP error: ${response.status}`);
            }

            const data = await response.json();
            console.log('Polling: Status', data.status);

            switch (data.status) {
                case 'pending':
                    updateStatus('Task queued, waiting to start...');
                    schedulePoll(taskId);
                    break;

                case 'processing':
                    updateStatus('Generating chapter content...');
                    schedulePoll(taskId);
                    break;

                case 'completed':
                    stopTimers();
                    updateProgress(100);
                    updateStatus('Chapter generated! Reloading...', true);
                    Toast.success('Chapter generated successfully!');
                    setTimeout(function() {
                        location.reload();
                    }, 500);
                    break;

                case 'failed':
                    stopTimers();
                    updateStatus('Generation failed.');
                    updateProgress(0);
                    if (progressBar) {
                        progressBar.classList.remove('progress-bar-animated', 'progress-bar-striped');
                        progressBar.classList.add('bg-danger');
                    }
                    const errorMsg = data.error_message || 'Unknown error occurred.';
                    Toast.error(`Generation failed: ${errorMsg}`);
                    break;

                default:
                    console.warn('Polling: Unknown status', data.status);
                    schedulePoll(taskId);
            }

        } catch (error) {
            console.error('Polling error:', error);

            // Continue polling on network errors (might be temporary)
            if (pollCount < CONFIG.MAX_POLLS) {
                schedulePoll(taskId);
            } else {
                stopTimers();
                Toast.error('Connection error. Please refresh the page.');
            }
        }
    }

    /**
     * Schedule next poll
     * @param {string} taskId - The task ID
     */
    function schedulePoll(taskId) {
        pollTimer = setTimeout(function() {
            poll(taskId);
        }, CONFIG.POLL_INTERVAL);
    }

    // Public API
    return {
        init: init,
    };
})();

/**
 * Initialize everything on DOM ready
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize polling
    ChapterPolling.init();

    // Add loading state to all forms
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function() {
            // Don't add loading state to forms with confirm dialogs
            // (they might be cancelled)
            const hasConfirm = form.hasAttribute('onsubmit') &&
                              form.getAttribute('onsubmit').includes('confirm');

            if (!hasConfirm) {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    LoadingButton.start(submitBtn);
                }
            }
        });
    });

    console.log('Story Generator: Initialized');
});

// Export for use in other scripts if needed
window.Toast = Toast;
window.LoadingButton = LoadingButton;
