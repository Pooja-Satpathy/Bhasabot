// src/App.jsx
import React, { useState, useEffect } from "react";
import Home from "./pages/Home";
import Auth from "./components/Auth";
import { logoutUser, checkCurrentUser } from "./api/client";
import { ThemeProvider } from "./context/ThemeContext";
import "./index.css";

function AppContent() {
  const [token, setToken] = useState(null);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    const restoreSession = async () => {
      const savedToken = sessionStorage.getItem("bhashabot_token");
      const savedUsername = sessionStorage.getItem("bhashabot_username");
      const savedEmail = sessionStorage.getItem("bhashabot_email");

      if (!savedToken || !savedUsername || !savedEmail) {
        setCheckingAuth(false);
        return;
      }

      try {
        const profile = await checkCurrentUser();
        setToken(savedToken);
        setUsername(profile.username || savedUsername);
        setEmail(profile.email || savedEmail);
      } catch (err) {
        logoutUser();
        setToken(null);
        setUsername("");
        setEmail("");
      } finally {
        setCheckingAuth(false);
      }
    };

    restoreSession();
  }, []);

  const handleAuthSuccess = (uname, uemail, authToken) => {
    setToken(authToken);
    setUsername(uname);
    setEmail(uemail);
  };

  const handleLogout = () => {
    logoutUser();
    setToken(null);
    setUsername("");
    setEmail("");
  };

  if (checkingAuth) {
    return (
      <div 
        className="h-screen w-screen flex items-center justify-center text-slate-300 font-medium text-sm select-none"
        style={{ background: "var(--gradient-surface)" }}
      >
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-brand-500/30 border-t-brand-500 rounded-full animate-spin" />
          <span>Verifying credentials...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen overflow-hidden">
      {token ? (
        <Home key={token} username={username} email={email} onLogout={handleLogout} />
      ) : (
        <Auth onAuthSuccess={handleAuthSuccess} />
      )}
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;
