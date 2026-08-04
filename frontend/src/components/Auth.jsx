// src/components/Auth.jsx
import React, { useState } from "react";
import { Globe, Mail, Lock, User, ArrowRight, Loader2, CheckCircle2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { loginUser, signupUser } from "../api/client";

const Auth = ({ onAuthSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  const validateEmail = (val) => {
    return /\S+@\S+\.\S+/.test(val);
  };

  const validateUsername = (val) => {
    return /^[a-zA-Z0-9_]+$/.test(val);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMsg("");

    const cleanUsername = username.trim();
    const cleanEmail = email.trim().toLowerCase();

    // Sign Up Validations
    if (!isLogin) {
      if (cleanUsername.length < 3) {
        setError("Username must be at least 3 characters long.");
        return;
      }
      if (!validateUsername(cleanUsername)) {
        setError("Username can only contain letters, numbers, and underscores.");
        return;
      }
      if (!validateEmail(cleanEmail)) {
        setError("Please enter a valid email address.");
        return;
      }
    } else {
      // Login validation (can be username or email)
      if (cleanUsername.length < 3) {
        setError("Username/Email must be at least 3 characters long.");
        return;
      }
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    if (!isLogin && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      if (isLogin) {
        const data = await loginUser(cleanUsername, password);
        onAuthSuccess(data.username, data.email, data.access_token);
      } else {
        await signupUser(cleanUsername, cleanEmail, password, confirmPassword);
        setSuccessMsg("Account created successfully! Switching to Login...");
        
        // Wait and then switch back to login screen, prefilling username
        setTimeout(() => {
          setIsLogin(true);
          setPassword("");
          setConfirmPassword("");
          setSuccessMsg("");
          setLoading(false);
        }, 2000);
      }
    } catch (err) {
      setError(err.message || "Authentication failed. Please try again.");
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError("");
    setSuccessMsg("");
    setUsername("");
    setEmail("");
    setPassword("");
    setConfirmPassword("");
  };

  return (
    <div 
      className="w-full h-full flex items-center justify-center p-4 relative overflow-hidden select-none"
      style={{ background: "var(--gradient-surface)" }}
    >
      {/* Decorative Background Glows */}
      <div className="absolute top-1/4 left-1/4 w-80 h-80 rounded-full bg-brand-500/10 blur-[100px] pointer-events-none" />
      <div className="absolute bottom-1/3 right-1/4 w-96 h-96 rounded-full bg-purple-500/10 blur-[120px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md glass rounded-2xl p-8 relative z-10 shadow-2xl border border-surface-500/40"
      >
        {/* App Logo/Header */}
        <div className="flex flex-col items-center text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center shadow-lg shadow-brand-500/20 mb-4">
            <Globe size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold gradient-text leading-none">BhashaBot</h1>
          <p className="text-xs text-slate-500 mt-1.5 leading-none">Multilingual PDF Question Answering</p>
        </div>

        {/* Title */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-slate-200">
            {isLogin ? "Welcome back" : "Create an account"}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {isLogin ? "Sign in to access your saved documents" : "Join BhashaBot and start analyzing documents"}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Username Field (Login or Sign Up) */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              {isLogin ? "Username or Email" : "Username"}
            </label>
            <div className="relative flex items-center">
              <User size={16} className="absolute left-3 text-slate-600" />
              <input
                id="username-input"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder={isLogin ? "Enter username or email" : "Enter a unique username"}
                required
                disabled={loading}
                className="w-full bg-surface-900/50 border border-surface-500/40 rounded-xl py-3 pl-10 pr-4 text-sm text-slate-200 placeholder-slate-700 focus:outline-none focus:border-brand-500/60 focus:ring-1 focus:ring-brand-500/30 transition-all"
              />
            </div>
          </div>

          {/* Email Field (Sign Up only) */}
          {!isLogin && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="overflow-hidden"
            >
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Email Address
              </label>
              <div className="relative flex items-center">
                <Mail size={16} className="absolute left-3 text-slate-600" />
                <input
                  id="email-input"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required={!isLogin}
                  disabled={loading}
                  className="w-full bg-surface-900/50 border border-surface-500/40 rounded-xl py-3 pl-10 pr-4 text-sm text-slate-200 placeholder-slate-700 focus:outline-none focus:border-brand-500/60 focus:ring-1 focus:ring-brand-500/30 transition-all"
                />
              </div>
            </motion.div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Password
            </label>
            <div className="relative flex items-center">
              <Lock size={16} className="absolute left-3 text-slate-600" />
              <input
                id="password-input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                disabled={loading}
                className="w-full bg-surface-900/50 border border-surface-500/40 rounded-xl py-3 pl-10 pr-4 text-sm text-slate-200 placeholder-slate-700 focus:outline-none focus:border-brand-500/60 focus:ring-1 focus:ring-brand-500/30 transition-all"
              />
            </div>
          </div>

          {/* Confirm Password Field for Sign Up */}
          {!isLogin && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="overflow-hidden"
            >
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Confirm Password
              </label>
              <div className="relative flex items-center">
                <Lock size={16} className="absolute left-3 text-slate-600" />
                <input
                  id="confirm-password-input"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  required={!isLogin}
                  disabled={loading}
                  className="w-full bg-surface-900/50 border border-surface-500/40 rounded-xl py-3 pl-10 pr-4 text-sm text-slate-200 placeholder-slate-700 focus:outline-none focus:border-brand-500/60 focus:ring-1 focus:ring-brand-500/30 transition-all"
                />
              </div>
            </motion.div>
          )}

          {/* Messages */}
          <AnimatePresence mode="wait">
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg p-3"
              >
                {error}
              </motion.div>
            )}
            {successMsg && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3 flex items-center gap-2"
              >
                <CheckCircle2 size={14} />
                <span>{successMsg}</span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Submit Button */}
          <button
            id="auth-submit-btn"
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-brand-500 to-purple-600 hover:from-brand-600 hover:to-purple-700 text-white rounded-xl py-3 text-sm font-semibold flex items-center justify-center gap-2 transition-all hover:shadow-lg hover:shadow-brand-500/20 hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 disabled:scale-100 disabled:pointer-events-none cursor-pointer mt-6"
          >
            {loading && !successMsg ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <>
                <span>{isLogin ? "Sign In" : "Sign Up"}</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        {/* Toggle Mode */}
        <div className="mt-8 border-t border-surface-500/20 pt-6 text-center">
          <p className="text-xs text-slate-500">
            {isLogin ? "Don't have an account?" : "Already have an account?"}{" "}
            <button
              id="auth-toggle-mode-btn"
              type="button"
              onClick={toggleMode}
              disabled={loading}
              className="text-brand-400 hover:text-brand-300 font-semibold hover:underline bg-transparent border-0 cursor-pointer ml-1 outline-none"
            >
              {isLogin ? "Sign up now" : "Sign in now"}
            </button>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default Auth;
