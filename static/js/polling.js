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
 *
 * Features:
 * - Pre-polling validation (empty taskId check)
 * - Error classification (terminal vs retryable)
 * - Exponential backoff with jitter
 * - Maximum attempts and total timeout limits
 * - AbortController for cleanup on page unload
 */
const ChapterPolling = (function() {
    // Configuration
    const CONFIG = {
        MAX_ATTEMPTS: 20,           // Maximum polling attempts
        TOTAL_TIMEOUT_MS: 300000,   // 5 minutes total timeout
        INITIAL_DELAY_MS: 1000,     // 1 second initial delay
        MAX_DELAY_MS: 32000,        // 32 seconds max delay
        BACKOFF_MULTIPLIER: 2,      // Exponential backoff multiplier
        JITTER_MAX_MS: 1000,        // Random jitter 0-1000ms
    };

    // Terminal HTTP status codes (stop polling immediately)
    const TERMINAL_STATUS_CODES = [400, 401, 403, 404, 422];

    // State
    let attemptCount = 0;
    let pollTimer = null;
    let startTime = null;
    let elapsedTimer = null;
    let abortController = null;

    // DOM elements (cached)
    let container = null;
    let progressBar = null;
    let statusText = null;
    let elapsedTimeEl = null;

    /**
     * Get CSRF token from meta tag or cookie
     */
    function getCSRFToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.content;
        }

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
     * Calculate delay with exponential backoff and jitter
     * Formula: min(2^attempt * 1000 + jitter, maxDelay)
     * @param {number} attempt - Current attempt number (0-based)
     * @returns {number} Delay in milliseconds
     */
    function calculateDelay(attempt) {
        const exponentialDelay = Math.pow(CONFIG.BACKOFF_MULTIPLIER, attempt) * CONFIG.INITIAL_DELAY_MS;
        const jitter = Math.floor(Math.random() * CONFIG.JITTER_MAX_MS);
        return Math.min(exponentialDelay + jitter, CONFIG.MAX_DELAY_MS);
    }

    /**
     * Check if HTTP status code is terminal (should stop polling)
     * @param {number} statusCode - HTTP status code
     * @returns {boolean}
     */
    function isTerminalStatusCode(statusCode) {
        return TERMINAL_STATUS_CODES.includes(statusCode);
    }

    /**
     * Check if total timeout has been exceeded
     * @returns {boolean}
     */
    function isTimeoutExceeded() {
        return (Date.now() - startTime) >= CONFIG.TOTAL_TIMEOUT_MS;
    }

    /**
     * Initialize polling if generation is in progress
     */
    function init() {
        container = document.getElementById('story-container');
        if (!container) return;

        const isGenerating = container.dataset.isGenerating === 'true';
        const taskId = container.dataset.taskId;

        // Pre-polling validation: check taskId before starting
        if (!isGenerating) {
            console.log('Polling: No active generation task');
            return;
        }

        if (!taskId || taskId.trim() === '' || taskId === 'None' || taskId === 'null') {
            console.error('Polling: Invalid or empty task ID');
            Toast.error('Generation task not found. Please try again.');
            return;
        }

        console.log('Polling: Starting for task', taskId);

        // Cache DOM elements
        progressBar = document.getElementById('progress-bar');
        statusText = document.getElementById('status-text');
        elapsedTimeEl = document.getElementById('elapsed-time');

        // Create AbortController for cleanup
        abortController = new AbortController();

        // Register cleanup on page unload
        window.addEventListener('beforeunload', cleanup);

        // Start polling
        startTime = Date.now();
        startElapsedTimer();
        poll(taskId);
    }

    /**
     * Cleanup function - stop all timers and abort pending requests
     */
    function cleanup() {
        stopTimers();
        if (abortController) {
            abortController.abort();
            abortController = null;
        }
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
     * @param {string} state - 'normal', 'success', or 'error'
     */
    function updateStatus(text, state = 'normal') {
        if (statusText) {
            statusText.textContent = text;
        }
        if (progressBar) {
            progressBar.classList.remove('bg-success', 'bg-danger');
            if (state === 'success') {
                progressBar.classList.remove('progress-bar-animated', 'progress-bar-striped');
                progressBar.classList.add('bg-success');
            } else if (state === 'error') {
                progressBar.classList.remove('progress-bar-animated', 'progress-bar-striped');
                progressBar.classList.add('bg-danger');
            }
        }
    }

    /**
     * Handle terminal error - stop polling and show error message
     * @param {string} message - User-friendly error message
     */
    function handleTerminalError(message) {
        cleanup();
        updateProgress(0);
        updateStatus(message, 'error');
        Toast.error(message);
    }

    /**
     * Handle timeout - stop polling and show timeout message
     */
    function handleTimeout() {
        cleanup();
        updateStatus('This is taking longer than expected. The server may be busy.', 'normal');
        Toast.warning('Request timed out. Please try again later.');
    }

    /**
     * Poll task status
     * @param {string} taskId - The Celery task ID
     */
    async function poll(taskId) {
        // Check attempt limit
        if (attemptCount >= CONFIG.MAX_ATTEMPTS) {
            console.log('Polling: Max attempts reached');
            handleTimeout();
            return;
        }

        // Check total timeout
        if (isTimeoutExceeded()) {
            console.log('Polling: Total timeout exceeded');
            handleTimeout();
            return;
        }

        attemptCount++;
        console.log(`Polling: Attempt ${attemptCount}/${CONFIG.MAX_ATTEMPTS}`);

        // Update progress (10% base + 4% per attempt, max 90%)
        const progress = Math.min(10 + (attemptCount * 4), 90);
        updateProgress(progress);

        // Show "still working" message for long waits
        if (attemptCount > 5) {
            updateStatus('Still working, please wait...');
        }

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
                signal: abortController ? abortController.signal : undefined,
            });

            // Handle HTTP errors
            if (!response.ok) {
                const statusCode = response.status;
                console.log(`Polling: HTTP error ${statusCode}`);

                // Terminal errors - stop polling immediately
                if (isTerminalStatusCode(statusCode)) {
                    if (statusCode === 404) {
                        handleTerminalError('Task not found. Please start a new generation.');
                    } else if (statusCode === 401 || statusCode === 403) {
                        handleTerminalError('Access denied. Please log in and try again.');
                    } else {
                        handleTerminalError(`Request failed (${statusCode}). Please try again.`);
                    }
                    return;
                }

                // Retryable errors (5xx, 429) - use backoff
                if (statusCode === 429) {
                    // Honor Retry-After header if present
                    const retryAfter = response.headers.get('Retry-After');
                    const delay = retryAfter ? parseInt(retryAfter, 10) * 1000 : calculateDelay(attemptCount);
                    schedulePoll(taskId, delay);
                } else {
                    // 5xx errors - exponential backoff
                    schedulePoll(taskId, calculateDelay(attemptCount));
                }
                return;
            }

            const data = await response.json();
            console.log('Polling: Status', data.status);

            switch (data.status) {
                case 'pending':
                    updateStatus('Task queued, waiting to start...');
                    schedulePoll(taskId, calculateDelay(attemptCount));
                    break;

                case 'processing':
                    updateStatus('Generating chapter content...');
                    schedulePoll(taskId, calculateDelay(attemptCount));
                    break;

                case 'completed':
                    cleanup();
                    updateProgress(100);
                    updateStatus('Chapter generated! Reloading...', 'success');
                    Toast.success('Chapter generated successfully!');
                    setTimeout(function() {
                        location.reload();
                    }, 500);
                    break;

                case 'failed':
                    const errorMsg = data.error_message || 'Unknown error occurred.';
                    handleTerminalError(`Generation failed: ${errorMsg}`);
                    break;

                default:
                    console.warn('Polling: Unknown status', data.status);
                    // Treat unknown as pending
                    schedulePoll(taskId, calculateDelay(attemptCount));
            }

        } catch (error) {
            // Ignore abort errors (page unload)
            if (error.name === 'AbortError') {
                console.log('Polling: Aborted');
                return;
            }

            console.error('Polling error:', error);

            // Network errors are retryable
            if (attemptCount < CONFIG.MAX_ATTEMPTS && !isTimeoutExceeded()) {
                updateStatus('Connection issue, retrying...');
                schedulePoll(taskId, calculateDelay(attemptCount));
            } else {
                handleTimeout();
            }
        }
    }

    /**
     * Schedule next poll with specified delay
     * @param {string} taskId - The task ID
     * @param {number} delay - Delay in milliseconds
     */
    function schedulePoll(taskId, delay) {
        console.log(`Polling: Next attempt in ${delay}ms`);
        pollTimer = setTimeout(function() {
            poll(taskId);
        }, delay);
    }

    // Public API
    return {
        init: init,
        cleanup: cleanup,
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
