// src/pages/Home.jsx
import React, { useState, useEffect, useCallback } from "react";
import { Globe, ChevronRight, BookOpen, Zap, Shield, LogOut, User, History, Trash2, Sun, Moon } from "lucide-react";
import FileUpload from "../components/FileUpload";
import ChatWindow from "../components/ChatWindow";
import { getUserSessions, deleteUserSession } from "../api/client";
import { useTheme } from "../context/ThemeContext";

const LANGUAGE_PREFERENCE_KEY = "bhashabot_preferred_language";
const LANGUAGE_OPTIONS = [
  { value: "Auto Detect", label: "Auto Detect 🌐" },
  { value: "English", label: "English 🇬🇧" },
  { value: "Hindi", label: "Hindi 🇮🇳" },
  { value: "Odia", label: "Odia 🇮🇳" },
  { value: "Hinglish", label: "Hinglish 🔀" },
  { value: "Odilish", label: "Odilish 🔀" },
];

const TONE_PREFERENCE_KEY = "bhashabot_response_tone";
const TONE_OPTIONS = ["Professional", "Friendly", "Simple"];

const FeatureChip = ({ icon: Icon, text }) => (
  <div className="flex items-center gap-2 text-xs text-slate-500">
    <Icon size={12} className="text-brand-400 flex-shrink-0" />
    <span>{text}</span>
  </div>
);

const Home = ({ username, email, onLogout }) => {
  const { theme, toggleTheme } = useTheme();
  const [session, setSession] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [historyError, setHistoryError] = useState(null);
  const [preferredLanguage, setPreferredLanguage] = useState(() => {
    try {
      return localStorage.getItem(LANGUAGE_PREFERENCE_KEY) || "Auto Detect";
    } catch {
      return "Auto Detect";
    }
  });
  const [responseTone, setResponseTone] = useState(() => {
    try {
      return localStorage.getItem(TONE_PREFERENCE_KEY) || "Friendly";
    } catch {
      return "Friendly";
    }
  });



  // Fetch all sessions belonging to the user
  const fetchSessions = useCallback(async (selectNewest = false) => {
    setLoadingHistory(true);
    setHistoryError(null);
    try {
      const list = await getUserSessions();
      setSessions(list);
      
      // Auto-select the newest upload if requested and available
      if (selectNewest && list.length > 0) {
        const newest = list[0];
        setSession({
          sessionId: newest.session_id,
          filename: newest.filename,
          chunksStored: newest.chunks_stored,
          documentVersion: newest.document_version
        });
      }
    } catch (err) {
      console.error("Failed to load document history:", err);
      setHistoryError(err.message || "Failed to load history");
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    setSession(null);
    fetchSessions(false);
  }, [fetchSessions]);

  useEffect(() => {
    try {
      localStorage.setItem(LANGUAGE_PREFERENCE_KEY, preferredLanguage);
    } catch {
      // no-op
    }
  }, [preferredLanguage]);

  useEffect(() => {
    try {
      localStorage.setItem(TONE_PREFERENCE_KEY, responseTone);
    } catch {
      // no-op
    }
  }, [responseTone]);

  const handleUploadSuccess = (uploadResult) => {
    setSession({
      sessionId: uploadResult.sessionId,
      filename: uploadResult.filename,
      chunksStored: uploadResult.chunksStored,
      documentVersion: uploadResult.documentVersion
    });
    // Refresh history without overriding the explicitly selected session.
    fetchSessions(false);
  };

  const handleDeleteSession = async (sessionId) => {
    if (!window.confirm("Are you sure you want to delete this document index from your history?")) {
      return;
    }
    try {
      await deleteUserSession(sessionId);
      // If we deleted the active session, clear active session state
      if (session?.sessionId === sessionId) {
        setSession(null);
      }
      fetchSessions(false);
    } catch (err) {
      alert(`Error deleting document: ${err.message}`);
    }
  };

  const userInitial = username ? username.trim().charAt(0).toUpperCase() : "?";

  return (
    <div className="h-full bg-surface-900 flex flex-col" style={{ background: "var(--gradient-surface)" }}>
      {/* Navbar */}
      <nav className="glass px-6 py-3 flex items-center justify-between flex-shrink-0" role="navigation" aria-label="Main navigation">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center shadow-lg">
            <Globe size={16} className="text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold gradient-text leading-none">BhashaBot</h1>
            <p className="text-xs text-slate-600 leading-none mt-0.5">Multilingual PDF AI</p>
          </div>
        </div>

        {/* User profile & Logout */}
        <div className="flex items-center gap-4">
          {/* Theme Toggle Button */}
          <button
            id="theme-toggle-btn"
            onClick={toggleTheme}
            className="p-1.5 rounded-lg bg-surface-500/10 border border-surface-500/20 text-slate-500 hover:text-brand-400 hover:bg-surface-500/20 transition-all outline-none cursor-pointer flex items-center justify-center"
            title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            {theme === "dark" ? <Sun size={14} /> : <Moon size={14} />}
          </button>

          <div className="flex items-center gap-2" title={email}>
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-brand-400 to-indigo-600 flex items-center justify-center shadow text-xs font-semibold text-white border border-white/10 select-none">
              {userInitial}
            </div>
            <span className="hidden sm:block text-xs font-medium text-slate-300">
              {username}
            </span>
          </div>
          
          <button
            id="nav-logout-btn"
            onClick={onLogout}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 py-1.5 px-3 rounded-lg transition-all outline-none cursor-pointer"
            title="Log Out"
          >
            <LogOut size={13} />
            <span className="hidden xs:inline">Log Out</span>
          </button>
        </div>
      </nav>

      {/* Main Panel */}
      <main className="flex-1 flex overflow-hidden">
        <aside className="w-80 lg:w-[22rem] flex-shrink-0 flex flex-col overflow-y-auto" aria-label="Upload and session panel">
          <div className="p-6 flex flex-col gap-6 flex-1 min-h-0">
            {/* Upload Area */}
            <section className="flex-shrink-0">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-5 h-5 rounded-md bg-brand-600/20 flex items-center justify-center">
                  <BookOpen size={12} className="text-brand-400" />
                </div>
                <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Document</h2>
              </div>
              <FileUpload onUploadSuccess={handleUploadSuccess} currentFile={session?.filename} />
              <div className="mt-3">
                <label htmlFor="language-preference" className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
                  Response Language
                </label>
                <select
                  id="language-preference"
                  value={preferredLanguage}
                  onChange={(e) => setPreferredLanguage(e.target.value)}
                  className="w-full rounded-lg bg-surface-900/50 border border-surface-500/40 py-2 px-2.5 text-xs text-slate-300 outline-none focus:border-brand-500/60 focus:ring-1 focus:ring-brand-500/30"
                >
                  {LANGUAGE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              <div className="mt-3">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">🎭 RESPONSE TONE</h3>
                <div className="grid grid-cols-3 gap-1.5">
                  {TONE_OPTIONS.map((tone) => {
                    const isActive = responseTone === tone;
                    return (
                      <button
                        key={tone}
                        type="button"
                        onClick={() => setResponseTone(tone)}
                        className={`px-2 py-1.5 rounded-lg text-[11px] font-medium border transition-all ${
                          isActive
                            ? "bg-brand-500/20 border-brand-500/50 text-brand-300"
                            : "bg-surface-900/40 border-surface-500/40 text-slate-400 hover:text-slate-200 hover:border-surface-500/70"
                        }`}
                      >
                        {tone}
                      </button>
                    );
                  })}
                </div>
              </div>
            </section>

            {/* Historical Sessions List */}
            <section className="flex flex-col flex-shrink-0">
              <div className="flex items-center justify-between mb-3 px-1">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-md bg-brand-600/20 flex items-center justify-center">
                    <History size={13} className="text-brand-400" />
                  </div>
                  <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">History</h2>
                </div>
                {loadingHistory && (
                  <div className="w-3.5 h-3.5 border border-slate-500/30 border-t-brand-500 rounded-full animate-spin" />
                )}
              </div>
              
              <div className="space-y-2 max-h-64 overflow-y-auto pr-1 custom-scrollbar">
                {historyError ? (
                  <div className="text-center py-6 px-4 border border-red-500/20 rounded-xl bg-red-500/5">
                    <p className="text-[11px] text-red-400 mb-2">Failed to load history</p>
                    <p className="text-[10px] text-slate-600">{historyError}</p>
                    <button
                      onClick={() => fetchSessions(false)}
                      className="mt-3 text-[11px] px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 transition-all"
                    >
                      Retry
                    </button>
                  </div>
                ) : sessions.length === 0 && !loadingHistory ? (
                  <div className="text-center py-6 px-4 border border-dashed border-surface-500/20 rounded-xl">
                    <p className="text-[11px] text-slate-600">No documents indexed yet.</p>
                  </div>
                ) : loadingHistory && sessions.length === 0 ? (
                  <div className="text-center py-8 px-4">
                    <div className="w-6 h-6 border-2 border-slate-500/30 border-t-brand-500 rounded-full animate-spin mx-auto mb-2" />
                    <p className="text-[11px] text-slate-600">Loading your documents...</p>
                  </div>
                ) : (
                  sessions.map((s) => {
                    const isActive = session?.sessionId === s.session_id;
                    return (
                      <div
                        key={s.session_id}
                        className={`flex items-center justify-between gap-2 p-3.5 rounded-xl border transition-all cursor-pointer select-none group ${
                          isActive
                            ? "glass-light border-brand-500 bg-brand-500/5 shadow-brand-500/5 shadow-md"
                            : "border-surface-500/30 hover:border-surface-500/80 bg-surface-900/20 hover:bg-surface-700/20"
                        }`}
                        onClick={() => setSession({
                          sessionId: s.session_id,
                          filename: s.filename,
                          chunksStored: s.chunks_stored,
                          documentVersion: s.document_version
                        })}
                      >
                        <div className="flex items-center gap-2 min-w-0 flex-1">
                          <BookOpen size={14} className={isActive ? "text-brand-400" : "text-slate-500"} />
                          <div className="min-w-0 flex-1">
                            <p className={`text-sm font-medium truncate ${isActive ? "text-brand-300" : "text-slate-300"}`} title={s.filename}>
                              {s.filename}
                            </p>
                            <div className="flex items-center gap-1.5 mt-1 text-[10px] text-slate-500">
                              <span className="font-mono">{s.chunks_stored} chunks</span>
                              {s.document_version > 1 && (
                                <span className="rounded-full bg-amber-500/10 px-1.5 py-0.5 text-amber-400 border border-amber-500/20">
                                  Version {s.document_version} · Reprocessed
                                </span>
                              )}
                            </div>
                            <p className="text-[10px] text-slate-600 mt-1">
                              {new Date(s.created_at.replace(" ", "T")).toLocaleString()}
                            </p>
                          </div>
                        </div>
                        <button
                          type="button"
                          className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-red-500/20 hover:text-red-400 text-slate-500 transition-all duration-200 outline-none border-0 cursor-pointer"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteSession(s.session_id);
                          }}
                          title="Delete document index"
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    );
                  })
                )}
              </div>
            </section>

            <section className="flex-shrink-0">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Capabilities</h3>
              <div className="space-y-2.5">
                <FeatureChip icon={Globe} text="50+ languages with E5-small embeddings" />
                <FeatureChip icon={Zap} text="Groq LLaMA-3 for fast answers" />
                <FeatureChip icon={Shield} text="ChromaDB for local vector storage" />
                <FeatureChip icon={ChevronRight} text="Source citations with relevance scores" />
                <FeatureChip icon={BookOpen} text="IndicTrans2 ready for Indian languages" />
              </div>
            </section>
          </div>
        </aside>

        {/* Chat Section */}
        <section className="flex-1 flex flex-col overflow-hidden" aria-label="Chat interface">
          <div className="px-5 py-3 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-sm font-medium text-slate-300">
                {session
                  ? `Chatting about: ${session.filename}${session.documentVersion > 1 ? ` (Version ${session.documentVersion})` : ""}`
                  : "BhashaBot Chat"}
              </span>
            </div>
            {session && <span className="text-xs text-slate-600">{session.chunksStored} chunks indexed</span>}
          </div>
          <div className="flex-1 flex flex-col overflow-hidden">
            <ChatWindow
              sessionId={session?.sessionId || null}
              filename={session?.filename || null}
              preferredLanguage={preferredLanguage}
              tone={responseTone}
            />
          </div>
        </section>
      </main>
    </div>
  );
};

export default Home;
