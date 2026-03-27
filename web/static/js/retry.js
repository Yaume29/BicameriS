/**
 * BICAMERIS - Retry Utilities
 * ===========================
 * Generic retry function for async operations.
 */

/**
 * Retry an async function with exponential or linear backoff.
 * @param {Function} fn - Async function to retry
 * @param {Object} options - Retry options
 * @param {number} options.maxAttempts - Maximum attempts (default: 3)
 * @param {number} options.baseDelay - Base delay in ms (default: 1000)
 * @param {string} options.backoff - "exponential" or "linear" (default: "exponential")
 * @returns {Promise<*>} - Result of the function
 * 
 * @example
 * const data = await retryAsync(() => fetch("/api/data"), {
 *   maxAttempts: 4,
 *   baseDelay: 2000,
 *   backoff: "exponential"
 * });
 */
async function retryAsync(fn, {
    maxAttempts = 3,
    baseDelay = 1000,
    backoff = "exponential"
} = {}) {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            return await fn();
        } catch (err) {
            if (attempt === maxAttempts) {
                console.error(`[Retry] Failed after ${maxAttempts} attempts:`, err);
                throw err;
            }
            const delay = backoff === "exponential"
                ? baseDelay * Math.pow(2, attempt - 1)
                : baseDelay * attempt;
            console.warn(`[Retry] Attempt ${attempt}/${maxAttempts} failed: ${err.message}. Retrying in ${delay}ms`);
            await new Promise(res => setTimeout(res, delay));
        }
    }
}

/**
 * Retry a fetch request with automatic error handling.
 * @param {string} url - URL to fetch
 * @param {Object} options - Fetch options
 * @param {Object} retryOptions - Retry options
 * @returns {Promise<Object>} - Parsed JSON response
 * 
 * @example
 * const data = await fetchWithRetry("/api/switches", {
 *   method: "POST",
 *   body: JSON.stringify({state: true})
 * });
 */
async function fetchWithRetry(url, options = {}, retryOptions = {}) {
    return await retryAsync(async () => {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    }, retryOptions);
}

// Export for module systems
if (typeof module !== "undefined" && module.exports) {
    module.exports = { retryAsync, fetchWithRetry };
}
