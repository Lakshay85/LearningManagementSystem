// RAG API Client - Communicates with RAG backend using JWT auth from LMS
const RAG_API_URL = import.meta.env.VITE_RAG_API_URL || "http://localhost:3001";
const RAG_API_KEY = import.meta.env.VITE_RAG_API_KEY;

/**
 * Get the access token from localStorage
 */
const getAccessToken = () => {
  return localStorage.getItem("accessToken");
};

/**
 * Make authenticated request to RAG API
 */
const ragFetch = async (endpoint, options = {}) => {
  const token = getAccessToken();

  const headers = {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
    ...(RAG_API_KEY && { "x-api-key": RAG_API_KEY }),
    ...options.headers,
  };

  const response = await fetch(`${RAG_API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ message: "Request failed" }));
    throw new Error(error.message || `HTTP error ${response.status}`);
  }

  return response.json();
};

// ==================== Chat Session APIs ====================

/**
 * Create a new chat session
 * @param {Object} options - Session options
 * @param {string} [options.courseId] - Optional course ID to link session to
 * @param {string} [options.title] - Optional session title
 * @param {string[]} [options.documentIds] - Optional document IDs to include
 */
export const createChatSession = async (options = {}) => {
  return ragFetch("/v1/rag/sessions", {
    method: "POST",
    body: JSON.stringify(options),
  });
};

/**
 * Get user's chat sessions
 * @param {string} [courseId] - Optional course ID to filter sessions
 */
export const getChatSessions = async (courseId = null) => {
  const query = courseId ? `?courseId=${courseId}` : "";
  return ragFetch(`/v1/rag/sessions${query}`);
};

/**
 * Get a specific chat session with messages
 * @param {string} sessionId - Session ID
 */
export const getChatSession = async (sessionId) => {
  return ragFetch(`/v1/rag/sessions/${sessionId}`);
};

/**
 * Update chat session title
 * @param {string} sessionId - Session ID
 * @param {string} title - New title
 */
export const updateChatSessionTitle = async (sessionId, title) => {
  return ragFetch(`/v1/rag/sessions/${sessionId}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });
};

/**
 * Delete a chat session
 * @param {string} sessionId - Session ID
 */
export const deleteChatSession = async (sessionId) => {
  return ragFetch(`/v1/rag/sessions/${sessionId}`, {
    method: "DELETE",
  });
};

// ==================== Query APIs ====================

/**
 * Get document ingestion status
 * @param {string} docId - Document ID
 */
export const getDocumentStatus = async (docId) => {
  return ragFetch(`/v1/rag/status/${docId}`);
};

/**
 * Delete a document
 * @param {string} docId - Document ID
 */
export const deleteDocument = async (docId) => {
  return ragFetch(`/v1/rag/document/${docId}`, {
    method: "DELETE",
  });
};

/**
 * Health check for RAG service
 */
export const healthCheck = async () => {
  return ragFetch("/v1/rag/health");
};

/**
 * Stream a query to the RAG system with real-time updates
 * @param {Object} options - Query options
 * @param {string} options.query - The question to ask
 * @param {string} [options.sessionId] - Optional session ID for conversation context
 * @param {number} [options.topK] - Number of relevant chunks to retrieve
 * @param {Object} [options.filters] - Optional metadata filters
 * @param {Function} options.onStatus - Callback for status updates
 * @param {Function} options.onChunk - Callback for response text chunks
 * @param {Function} options.onError - Callback for errors
 * @param {Function} options.onDone - Callback when complete
 * @returns {Function} Abort function to cancel the stream
 */
export const queryRagStream = ({
  query,
  sessionId,
  topK,
  filters,
  onStatus,
  onChunk,
  onError,
  onDone,
}) => {
  const controller = new AbortController();
  const token = localStorage.getItem("accessToken");

  const headers = {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
    ...(RAG_API_KEY && { "x-api-key": RAG_API_KEY }),
  };

  fetch(`${RAG_API_URL}/v1/rag/query/stream`, {
    method: "POST",
    headers,
    body: JSON.stringify({ query, sessionId, topK, filters }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (data.type) {
                case "status":
                  onStatus?.(data.message);
                  break;
                case "chunk":
                  onChunk?.(data.text);
                  break;
                case "error":
                  onError?.(new Error(data.message));
                  break;
                case "done":
                  onDone?.();
                  break;
              }
            } catch (e) {
              console.warn("Failed to parse SSE data:", line);
            }
          }
        }
      }

      onDone?.();
    })
    .catch((err) => {
      if (err.name !== "AbortError") {
        onError?.(err);
      }
    });

  // Return abort function
  return () => controller.abort();
};

export default {
  createChatSession,
  getChatSessions,
  getChatSession,
  updateChatSessionTitle,
  deleteChatSession,
  queryRagStream,
  getDocumentStatus,
  deleteDocument,
  healthCheck,
};
