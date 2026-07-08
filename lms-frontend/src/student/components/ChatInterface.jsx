import { useState, useEffect, useRef } from "react";
import ConfirmationModal from "../../components/common/ConfirmationModal";
import {
  queryRagStream,
  getChatSessions,
  getChatSession,
  createChatSession,
  deleteChatSession,
} from "../../utils/rag";
import "./ChatInterface.css";

/**
 * Chat interface component for RAG-based Q&A
 * @param {Object} props
 * @param {string} [props.courseId] - Optional course ID for course-specific context
 * @param {string} [props.courseName] - Optional course name for display
 * @param {boolean} [props.isOpen] - Whether the chat panel is open
 * @param {Function} [props.onClose] - Callback when chat is closed
 */
export default function ChatInterface({
  courseId,
  courseName,
  isOpen = true,
  onClose,
}) {
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [streamingStatus, setStreamingStatus] = useState("");
  const [error, setError] = useState(null);
  const [showSessions, setShowSessions] = useState(true);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState(null);
  const messagesEndRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, [courseId]);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadSessions = async () => {
    try {
      const response = await getChatSessions(courseId);
      setSessions(response.data || []);
    } catch (err) {
      console.error("Failed to load sessions:", err);
      setError("Failed to load chat history");
    }
  };

  const loadSession = async (sessionId) => {
    try {
      setIsLoading(true);
      const response = await getChatSession(sessionId);
      setActiveSession(response.data.session);
      // Map DB messages to ensure consistent format for rendering
      const dbMessages = (response.data.messages || []).map((msg) => ({
        ...msg,
        id: msg.id || msg._id || Date.now().toString(),
        role: msg.role,
        content: msg.content,
        createdAt: msg.createdAt || msg.created_at,
        isStreaming: false,
      }));
      setMessages(dbMessages);
      setShowSessions(false);
    } catch (err) {
      console.error("Failed to load session:", err);
      setError("Failed to load chat session");
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    // Lazy creation: only reset local state, session is created on first message send
    setActiveSession(null);
    setMessages([]);
    setShowSessions(false);
    setError(null);
  };

  const handleDeleteSession = (sessionId, e) => {
    e.stopPropagation();
    setSessionToDelete(sessionId);
    setDeleteModalOpen(true);
  };

  const confirmDeleteSession = async () => {
    if (!sessionToDelete) return;

    try {
      await deleteChatSession(sessionToDelete);
      setSessions(sessions.filter((s) => s.id !== sessionToDelete));
      if (activeSession?.id === sessionToDelete) {
        setActiveSession(null);
        setMessages([]);
        setShowSessions(true);
      }
    } catch (err) {
      console.error("Failed to delete session:", err);
      setError("Failed to delete chat");
    } finally {
      setDeleteModalOpen(false);
      setSessionToDelete(null);
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current();
      abortControllerRef.current = null;
      setIsLoading(false);
      setStreamingStatus("");

      // Update the last message to stop showing as streaming
      setMessages((prev) => {
        if (prev.length === 0) return prev;
        const newMessages = [...prev];
        const lastMsg = newMessages[newMessages.length - 1];
        if (lastMsg.role === 'assistant') {
          lastMsg.isStreaming = false;
        }
        return newMessages;
      });
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");

    // Add user message to UI immediately
    const userMsg = {
      id: Date.now().toString(),
      role: "user",
      content: userMessage,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setError(null);
    setStreamingStatus("");

    // Create placeholder for assistant message
    const assistantId = (Date.now() + 1).toString();
    setMessages((prev) => [
      ...prev,
      {
        id: assistantId,
        role: "assistant",
        content: "",
        createdAt: new Date().toISOString(),
        isStreaming: true,
      },
    ]);

    try {
      // If no active session, create one
      let sessionId = activeSession?.id;
      if (!sessionId) {
        const sessionResponse = await createChatSession({
          courseId,
          title: userMessage.substring(0, 50),
        });
        setActiveSession(sessionResponse.data);
        sessionId = sessionResponse.data.id;
        await loadSessions();
      }

      // Send streaming query to RAG
      // Store the abort function
      abortControllerRef.current = queryRagStream({
        query: userMessage,
        sessionId,
        topK: 5,
        filters: courseId ? { courseId } : undefined,
        onStatus: (status) => {
          setStreamingStatus(status);
        },
        onChunk: (text) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantId
                ? { ...msg, content: msg.content + text }
                : msg
            )
          );
        },
        onError: (err) => {
          console.error("Streaming error:", err);
          setError(err.message || "Failed to get AI response");
          // Remove the empty assistant message on error
          setMessages((prev) => prev.filter((m) => m.id !== assistantId));
          setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
          setInput(userMessage);
          setIsLoading(false);
          setStreamingStatus("");
          abortControllerRef.current = null;
        },
        onDone: () => {
          // Mark message as complete
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantId
                ? { ...msg, isStreaming: false }
                : msg
            )
          );
          setIsLoading(false);
          setStreamingStatus("");
          abortControllerRef.current = null;
        },
      });
    } catch (err) {
      console.error("Failed to get response:", err);
      setError(err.message || "Failed to get AI response");
      // Remove user message on error
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
      setMessages((prev) => prev.filter((m) => m.id !== assistantId));
      setInput(userMessage);
      setIsLoading(false);
      setStreamingStatus("");
    }
  };

  const handleBackToSessions = () => {
    setActiveSession(null);
    setMessages([]);
    setShowSessions(true);
    loadSessions(); // Reload to get accurate session list (only sessions with messages)
  };

  if (!isOpen) return null;

  return (
    <div className="chat-interface">

      <div className="chat-header">
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {!showSessions && (
            <button
              className="chat-btn chat-btn-secondary"
              onClick={handleBackToSessions}
            >
              ← Back
            </button>
          )}
          <h3>
            {activeSession?.title ||
              (courseName ? `Chat - ${courseName}` : "AI Assistant")}
          </h3>
        </div>
        <div className="chat-header-buttons">
          <button className="chat-btn chat-btn-primary" onClick={handleNewChat}>
            + New Chat
          </button>
          {onClose && (
            <button className="chat-btn chat-btn-secondary" onClick={onClose}>
              ✕
            </button>
          )}
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {showSessions ? (
        <div className="sessions-list">
          {sessions.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">💬</div>
              <h4>No conversations yet</h4>
              <p>
                Start a new chat to ask questions about your course materials
              </p>
              {/* <button
                className="chat-btn chat-btn-primary"
                onClick={handleNewChat}
                style={{ marginTop: "16px" }}
              >
                Start New Chat
              </button> */}
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className="session-item"
                onClick={() => loadSession(session.id)}
              >
                <span className="session-title">{session.title}</span>
                <span className="session-date">
                  {new Date(session.lastActivityAt).toLocaleDateString()}
                </span>
                <button
                  className="chat-btn chat-btn-danger"
                  onClick={(e) => handleDeleteSession(session.id, e)}
                >
                  🗑
                </button>
              </div>
            ))
          )}
        </div>
      ) : (
        <>
          <div className="messages-container">
            {messages.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">🤖</div>
                <h4>Ask me anything!</h4>
                <p>I can help answer questions about your course materials</p>
              </div>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className={`message message-${msg.role}`}>
                  <div className="message-content">{msg.content}</div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="loading-indicator">
                <div className="loading-dots">
                  <div className="loading-dot"></div>
                  <div className="loading-dot"></div>
                  <div className="loading-dot"></div>
                </div>
                <span>{streamingStatus || "AI is thinking..."}</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-container">
            <form className="chat-input-form" onSubmit={handleSendMessage}>
              <input
                type="text"
                className="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a question about the course..."
                disabled={isLoading}
              />
              {isLoading ? (
                <button
                  type="button"
                  className="stop-btn"
                  onClick={handleStop}
                  title="Stop generating"
                >
                  <div className="stop-icon"></div>
                </button>
              ) : (
                <button
                  type="submit"
                  className="send-btn"
                  disabled={!input.trim()}
                >
                  Send
                </button>
              )}
            </form>
          </div>
        </>
      )}
      <ConfirmationModal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={confirmDeleteSession}
        title="Delete Chat"
        message="Are you sure you want to delete this chat session? This action cannot be undone."
        confirmText="Delete"
        isDanger={true}
      />
    </div>
  );
}
