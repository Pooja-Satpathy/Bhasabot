// src/components/LangBadge.jsx
import React from "react";

const LANG_FLAGS = {
  English: "🇬🇧", Hindi: "🇮🇳", Tamil: "🇮🇳", Telugu: "🇮🇳",
  Kannada: "🇮🇳", Malayalam: "🇮🇳", Bengali: "🇮🇳", Gujarati: "🇮🇳",
  Marathi: "🇮🇳", Punjabi: "🇮🇳", Urdu: "🇵🇰", Odia: "🇮🇳",
  Assamese: "🇮🇳", French: "🇫🇷", German: "🇩🇪", Spanish: "🇪🇸",
  Portuguese: "🇧🇷", Arabic: "🇸🇦", Japanese: "🇯🇵", Chinese: "🇨🇳",
};

const INDIAN_LANGUAGES = new Set([
  "Hindi", "Tamil", "Telugu", "Kannada", "Malayalam",
  "Bengali", "Gujarati", "Marathi", "Punjabi", "Odia", "Assamese", "Urdu",
]);

const LangBadge = ({ language, size = "sm" }) => {
  if (!language) return null;
  const isIndian = INDIAN_LANGUAGES.has(language);
  const flag = LANG_FLAGS[language] || "🌐";
  const sizeClasses = { xs: "text-xs px-1.5 py-0.5", sm: "text-xs px-2 py-1" };
  const colorClasses = isIndian
    ? "bg-orange-500/15 text-orange-300 border border-orange-500/30"
    : "bg-brand-600/15 text-brand-300 border border-brand-500/30";

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-medium ${sizeClasses[size]} ${colorClasses} transition-all duration-200`}
      title={`Detected language: ${language}`}
      aria-label={`Language detected: ${language}`}
    >
      <span role="img" aria-hidden="true">{flag}</span>
      <span>{language}</span>
    </span>
  );
};

export default LangBadge;
