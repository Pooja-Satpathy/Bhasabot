// src/components/ChatWindow.jsx
import React, { useState, useRef, useEffect, useCallback } from "react";
import { Send, MessageSquare, Sparkles } from "lucide-react";
import MessageBubble from "./MessageBubble";
import { sendChatMessage } from "../api/client";

const WelcomeState = ({ filename }) => (
  <div className="flex flex-col items-center justify-center h-full text-center px-8 py-12">
    <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-500/20 to-purple-600/20 border border-brand-500/20 flex items-center justify-center mb-5">
      <Sparkles size={28} className="text-brand-400" />
    </div>
    <h2 className="text-xl font-semibold text-slate-200 mb-2">Ask BhashaBot anything</h2>
    <p className="text-sm text-slate-500 max-w-[280px] leading-relaxed">
      {filename ? (
        <>Your document <span className="text-brand-400 font-medium">{filename}</span> is ready. Ask questions in any language!</>
      ) : (
        "Upload a PDF to get started. You can ask questions in Hindi, Tamil, English, and 50+ languages."
      )}
    </p>
    <div className="mt-6 flex flex-wrap gap-2 justify-center">
      {["Summarize this document", "इस दस्तावेज़ का सारांश दें", "What are the key findings?"].map((example) => (
        <span key={example} className="text-xs px-3 py-1.5 rounded-full glass border border-surface-500 text-slate-400">{example}</span>
      ))}
    </div>
  </div>
);

const ChatWindow = ({ sessionId, filename }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const generateId = () => `msg_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;

  const handleSendMessage = useCallback(async () => {
    const query = inputValue.trim();
    if (!query || isLoading) return;
    if (!sessionId) { alert("Please upload a PDF document first!"); return; }
    setInputValue("");
    setIsLoading(true);
    const userMessage = { id: generateId(), role: "user", content: query, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMessage]);
    const typingId = generateId();
    setMessages((prev) => [...prev, { id: typingId, role: "bot", content: "", isTyping: true, timestamp: new Date().toISOString() }]);
    try {
      const response = await sendChatMessage(query, sessionId);
      setMessages((prev) => prev.map((msg) => msg.id === userMessage.id ? { ...msg, detectedLanguage: response.detected_language } : msg));
      setMessages((prev) => prev.map((msg) => msg.id === typingId ? { ...msg, content: response.answer, sources: response.sources, isTyping: false, timestamp: new Date().toISOString() } : msg));
    } catch (error) {
      setMessages((prev) => prev.map((msg) => msg.id === typingId ? { ...msg, content: `Sorry, I encountered an error: ${error.message}. Please try again.`, isTyping: false, timestamp: new Date().toISOString() } : msg));
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }, [inputValue, isLoading, sessionId]);

  const handleKeyDown = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSendMessage(); } };

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  return (
    <div className="flex flex-col h-full">
      <div id="chat-message-list" className="flex-1 overflow-y-auto px-4 py-4 space-y-5" role="log" aria-live="polite" aria-label="Chat messages">
        {messages.length === 0 ? <WelcomeState filename={filename} /> : messages.map((message) => <MessageBubble key={message.id} message={message} />)}
        <div ref={messagesEndRef} />
      </div>
      <div className="px-4 pb-4 pt-2 border-t border-surface-500/50">
        {!sessionId && <p className="text-xs text-amber-400/80 mb-2 text-center">⚠️ Upload a PDF to enable chat</p>}
        <div className={`flex items-end gap-2 glass rounded-xl p-2 ${!sessionId ? "opacity-60" : ""}`}>
          <textarea
            ref={inputRef} id="chat-input" value={inputValue} onChange={handleInputChange} onKeyDown={handleKeyDown}
            placeholder={sessionId ? "Ask in any language... (Enter to send, Shift+Enter for newline)" : "Upload a PDF to start chatting..."}
            disabled={!sessionId || isLoading} rows={1} aria-label="Chat message input"
            className="flex-1 bg-transparent text-sm text-slate-200 placeholder-slate-600 resize-none outline-none py-1.5 px-2 max-h-[120px] disabled:cursor-not-allowed"
          />
          <button
            id="chat-send-btn" onClick={handleSendMessage} disabled={!inputValue.trim() || !sessionId || isLoading} aria-label="Send message"
            className={`flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center transition-all duration-200 ${
              inputValue.trim() && sessionId && !isLoading ? "bg-gradient-to-br from-brand-500 to-brand-600 text-white shadow-lg btn-glow hover:scale-105 active:scale-95" : "bg-surface-600 text-slate-600 cursor-not-allowed"
            }`}
          >
            {isLoading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Send size={15} />}
          </button>
        </div>
        {inputValue.length > 1800 && <p className="text-xs text-amber-400 mt-1 text-right">{2000 - inputValue.length} characters remaining</p>}
        {messages.length > 0 && <p className="text-xs text-slate-700 text-center mt-1">{messages.filter((m) => !m.isTyping).length} messages • <MessageSquare size={10} className="inline" /> BhashaBot</p>}
      </div>
    </div>
  );
};

export default ChatWindow;
