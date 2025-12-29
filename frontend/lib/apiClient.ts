/**
 * API Client - Centralized backend API calls
 * 
 * All backend API interactions should go through these functions
 * for consistency, error handling, and maintainability.
 */

const getBackendUrl = () => {
    return (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000').replace(/\/$/, '');
};

// ==================== Query API ====================

export interface QueryRequest {
    user_id: string;
    session_id: string;
    query: string;
    model_name: string;
    model_provider: string;
    web_search?: boolean;
    use_memory?: boolean;
    history?: Array<{ role: string; content: string }>;
    location?: any;
    attachments?: any[];
    mode?: 'chat' | 'shopping';
}

export interface QueryResponse {
    response: string;
    citations?: Array<{ title: string; url: string }>;
    product_cards?: any[];
    options?: string[];
    memory_context?: any;
}

/**
 * Send query to backend (streaming)
 */
export async function streamQuery(request: QueryRequest): Promise<ReadableStream> {
    const url = `${getBackendUrl()}/api/v1/query/stream`;
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        throw new Error(`Query failed: ${response.status}`);
    }

    if (!response.body) {
        throw new Error('No response body');
    }

    return response.body;
}

/**
 * Send query to backend (standard)
 */
export async function sendQuery(request: QueryRequest): Promise<QueryResponse> {
    const url = `${getBackendUrl()}/api/v1/query/`;
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        throw new Error(`Query failed: ${response.status}`);
    }

    return response.json();
}

/**
 * Get query history for a user
 */
export async function getQueryHistory(userId: string): Promise<any[]> {
    const url = `${getBackendUrl()}/api/v1/query/history/${encodeURIComponent(userId)}`;
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`Failed to get query history: ${response.status}`);
    }

    return response.json();
}

// ==================== Session API ====================

export interface SessionStartRequest {
    session_id: string;
    user_id: string;
    experiment_id?: string;
    environment: {
        device: string;
        browser: string;
        os: string;
        viewport: { width: number; height: number };
        language?: string;
        connection?: string;
        location?: any;
    };
}

export interface SessionEventRequest {
    session_id: string;
    event: {
        t: number;  // timestamp
        type: string;
        data: Record<string, any>;
    };
}

/**
 * Start a new session
 */
export async function startSession(request: SessionStartRequest): Promise<any> {
    const url = `${getBackendUrl()}/api/v1/session/start`;
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        throw new Error(`Failed to start session: ${response.status}`);
    }

    return response.json();
}

/**
 * End a session
 */
export async function endSession(sessionId: string): Promise<any> {
    const url = `${getBackendUrl()}/api/v1/session/end`;
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
    });

    if (!response.ok) {
        throw new Error(`Failed to end session: ${response.status}`);
    }

    return response.json();
}

/**
 * Log an event to a session
 */
export async function logSessionEvent(request: SessionEventRequest): Promise<void> {
    const url = `${getBackendUrl()}/api/v1/session/event`;
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        // Don't throw for event logging failures (fire and forget)
        console.warn(`Failed to log event: ${response.status}`);
    }
}

/**
 * Get session data
 */
export async function getSession(sessionId: string, includeEvents = false): Promise<any> {
    const url = `${getBackendUrl()}/api/v1/session/${encodeURIComponent(sessionId)}${includeEvents ? '?include_events=true' : ''}`;
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`Failed to get session: ${response.status}`);
    }

    return response.json();
}

/**
 * Get session experiment data
 */
export async function getSessionExperiment(sessionId: string): Promise<any> {
    const url = `${getBackendUrl()}/api/v1/session/${encodeURIComponent(sessionId)}/experiment`;
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`Failed to get experiment: ${response.status}`);
    }

    return response.json();
}

/**
 * Update session experiment data
 */
export async function updateSessionExperiment(
    sessionId: string,
    experimentData: { experiment_id?: string; model_group?: string }
): Promise<any> {
    const url = `${getBackendUrl()}/api/v1/session/${encodeURIComponent(sessionId)}/experiment`;
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(experimentData),
    });

    if (!response.ok) {
        throw new Error(`Failed to update experiment: ${response.status}`);
    }

    return response.json();
}

// ==================== Products API ====================

/**
 * Search products
 */
export async function searchProducts(query: string, options?: any): Promise<any> {
    const url = `${getBackendUrl()}/api/v1/products/search`;
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, ...options }),
    });

    if (!response.ok) {
        throw new Error(`Product search failed: ${response.status}`);
    }

    return response.json();
}

// ==================== Files API ====================

/**
 * Upload a file
 */
export async function uploadFile(file: File, userId: string): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);

    const url = `${getBackendUrl()}/api/v1/files/upload`;
    const response = await fetch(url, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        throw new Error(`File upload failed: ${response.status}`);
    }

    return response.json();
}

/**
 * List user files
 */
export async function listFiles(userId: string): Promise<any[]> {
    const url = `${getBackendUrl()}/api/v1/files/?user_id=${encodeURIComponent(userId)}`;
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`Failed to list files: ${response.status}`);
    }

    return response.json();
}

// ==================== Helper: Event Logging ====================

/**
 * Quick helper to log events without try/catch boilerplate
 * Silently ignores 404s (session not created yet)
 */
export function logEvent(
    sessionId: string,
    type: string,
    data: Record<string, any> = {}
): void {
    // Fire and forget
    logSessionEvent({
        session_id: sessionId,
        event: {
            t: Date.now(),
            type,
            data,
        },
    }).catch((err) => {
        // Silently ignore 404s (session not created yet during initialization)
        // This is a race condition that resolves itself within ~500ms
        if (!err || !err.toString().includes('404')) {
            console.warn('Event logging failed:', err);
        }
    });
}
