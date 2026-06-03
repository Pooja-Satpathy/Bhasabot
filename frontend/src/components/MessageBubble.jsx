// src/components/MessageBubble.jsx
import React from "react";
import ReactMarkdown from "react-markdown";
import { Bot, User, FileText, ChevronDown, ChevronUp } from "lucide-react";
import LangBadge from "./LangBadge";

const TypingIndicator = () => (
  <div className="flex items-center gap-1.5 py-2 px-1">
    <span className="typing-dot" />
    <span className="typing-dot" />
    <span className="typing-dot" />
    <span className="text-xs text-slate-500 ml-1">Thinking...</span>
  </div>
);

const SourceAccordion = ({ sources }) => {
  const [open, setOpen] = React.useState(false);
  if (!sources || sources.length === 0) return null;
  return (
    <div className="mt-3 border border-surface-500/50 rounded-lg overflow-hidden">
      <button
        id="source-accordion-toggle"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-3 py-2 text-xs text-slate-400 hover:text-slate-300 hover:bg-surface-600/40 transition-colors"
        aria-expanded={open}
      >
        <span className="flex items-center gap-1.5">
          <FileText size={12} />
          {sources.length} source{sources.length !== 1 ? "s" : ""} referenced
        </span>
        {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>
      {open && (
        <div className="border-t border-surface-500/50 divide-y divide-surface-500/30">
          {sources.map((src, idx) => (
            <div key={idx} className="px-3 py-2 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText size={11} className="text-brand-400 flex-shrink-0" />
                <span className="text-xs text-slate-400 truncate max-w-[200px]">{src.filename}</span>
                <span className="text-xs text-slate-600">• Chunk #{src.chunk_index + 1}</span>
              </div>
              <span className="text-xs font-mono bg-brand-600/20 text-brand-300 px-2 py-0.5 rounded-full">
                {(src.relevance_score * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const MessageBubble = ({ message }) => {
  const isUser = message.role === "user";
  const isBot = message.role === "bot";
  return (
    <div className={`message-enter flex items-start gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? "bg-gradient-to-br from-brand-500 to-purple-600" : "bg-gradient-to-br from-emerald-600 to-teal-700"
        }`}
        aria-hidden="true"
      >
        {isUser ? <User size={14} className="text-white" /> : <Bot size={14} className="text-white" />}
      </div>
      <div className={`flex flex-col gap-1 max-w-[78%] ${isUser ? "items-end" : "items-start"}`}>
        <div className={`flex items-center gap-2 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
          <span className="text-xs font-medium text-slate-500">{isUser ? "You" : "BhashaBot"}</span>
          {isUser && message.detectedLanguage && <LangBadge language={message.detectedLanguage} size="xs" />}
        </div>
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? "bg-gradient-to-br from-brand-600 to-brand-700 text-white rounded-tr-sm"
              : "glass text-slate-200 rounded-tl-sm prose-dark"
          }`}
        >
          {message.isTyping ? (
            <TypingIndicator />
          ) : isBot ? (
            <ReactMarkdown
              components={{
                code: ({ children }) => (
                  <code className="bg-brand-600/20 text-brand-300 px-1.5 py-0.5 rounded text-xs font-mono">{children}</code>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          ) : (
            <p className="whitespace-pre-wrap">{message.content}</p>
          )}
        </div>
        {isBot && !message.isTyping && message.sources?.length > 0 && (
          <div className="w-full"><SourceAccordion sources={message.sources} /></div>
        )}
        {message.timestamp && !message.isTyping && (
          <span className="text-xs text-slate-600">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
