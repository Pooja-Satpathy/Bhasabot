// src/pages/Home.jsx
import React, { useState } from "react";
import { Globe, ChevronRight, BookOpen, Zap, Shield } from "lucide-react";
import FileUpload from "../components/FileUpload";
import ChatWindow from "../components/ChatWindow";

const FeatureChip = ({ icon: Icon, text }) => (
  <div className="flex items-center gap-2 text-xs text-slate-500">
    <Icon size={12} className="text-brand-400 flex-shrink-0" />
    <span>{text}</span>
  </div>
);

const Home = () => {
  const [session, setSession] = useState(null);
  const handleUploadSuccess = (uploadResult) => { setSession(uploadResult); };

  return (
    <div className="min-h-screen bg-surface-900 flex flex-col" style={{ background: "var(--gradient-surface)" }}>
      <nav className="glass border-b border-surface-500/40 px-6 py-3 flex items-center justify-between flex-shrink-0" role="navigation" aria-label="Main navigation">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center shadow-lg">
            <Globe size={16} className="text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold gradient-text leading-none">BhashaBot</h1>
            <p className="text-xs text-slate-600 leading-none mt-0.5">Multilingual PDF AI</p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="hidden sm:block">50+ languages supported</span>
          <span className="sm:hidden">50+ langs</span>
        </div>
      </nav>
      <main className="flex-1 flex overflow-hidden">
        <aside className="w-72 lg:w-80 flex-shrink-0 border-r border-surface-500/40 flex flex-col overflow-y-auto" aria-label="Upload and session panel">
          <div className="p-5 flex flex-col gap-5 flex-1">
            <section>
              <div className="flex items-center gap-2 mb-3">
                <div className="w-5 h-5 rounded-md bg-brand-600/20 flex items-center justify-center">
                  <BookOpen size={12} className="text-brand-400" />
                </div>
                <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Document</h2>
              </div>
              <FileUpload onUploadSuccess={handleUploadSuccess} currentFile={session?.filename} />
            </section>
            {session && (
              <section id="session-info-panel" className="glass-light rounded-xl p-4 border border-surface-500/40 animate-fade-in" aria-label="Session information">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Session</h3>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-500">File</span>
                    <span className="text-slate-300 font-medium max-w-[140px] truncate" title={session.filename}>{session.filename}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-500">Chunks</span>
                    <span className="text-emerald-400 font-medium font-mono">{session.chunksStored}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-500">Session ID</span>
                    <span className="text-slate-600 font-mono text-xs truncate max-w-[120px]" title={session.sessionId}>{session.sessionId.slice(0, 12)}…</span>
                  </div>
                </div>
              </section>
            )}
            <div className="border-t border-surface-500/30" />
            <section>
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Capabilities</h3>
              <div className="space-y-2.5">
                <FeatureChip icon={Globe} text="50+ languages with E5-large embeddings" />
                <FeatureChip icon={Zap} text="Gemini 1.5 Flash for fast answers" />
                <FeatureChip icon={Shield} text="ChromaDB for local vector storage" />
                <FeatureChip icon={ChevronRight} text="Source citations with relevance scores" />
                <FeatureChip icon={BookOpen} text="IndicTrans2 ready for Indian languages" />
              </div>
            </section>
            <div className="flex-1" />
            <p className="text-xs text-slate-700 text-center leading-relaxed">
              Powered by <span className="text-brand-500">multilingual-e5-large</span> + <span className="text-purple-500">Gemini</span>
            </p>
          </div>
        </aside>
        <section className="flex-1 flex flex-col overflow-hidden" aria-label="Chat interface">
          <div className="px-5 py-3 border-b border-surface-500/30 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-sm font-medium text-slate-300">{session ? `Chatting about: ${session.filename}` : "BhashaBot Chat"}</span>
            </div>
            {session && <span className="text-xs text-slate-600">{session.chunksStored} chunks indexed</span>}
          </div>
          <div className="flex-1 overflow-hidden">
            <ChatWindow sessionId={session?.sessionId || null} filename={session?.filename || null} />
          </div>
        </section>
      </main>
    </div>
  );
};

export default Home;
