"""
RAG Chain Service - Retrieval-Augmented Generation pipeline
Retrieves relevant chunks from ChromaDB and generates answers using Groq API (LLaMA model).
"""

import os
import re
from typing import Dict, Any, List, Optional
from groq import Groq

from services.vector_store import retrieve_chunks
from services.translator import (
    translate_to_english,
    translate_from_english,
    safe_chat_completion,
    normalize_odish_output,
)

# Configure Groq client with the API key from environment variables
# The key is loaded from .env file via python-dotenv in main.py
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq client (will be None if no key is set)
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Use LLaMA 3.3 70B via Groq for fast, high-quality multilingual responses
# Fallback option: "llama-3.1-8b-instant" (faster, smaller)
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Base system prompt for multilingual document assistance.
SYSTEM_PROMPT_BASE = """You are BhashaBot, an intelligent multilingual document assistant.
You help users understand PDF documents by answering questions, translating, or summarizing based on the provided context.

Instructions:
- Answer questions based on the provided context chunks.
- If the required facts to answer the question are not present in the context, clearly state that you don't have enough information.
- Always respond in English. Do not attempt to respond in Hindi, Tamil, French, or any other language. Your English response will be translated to the user's native language by a downstream translator.
- Cite which part of the document supports your answer when possible (e.g., "[Chunk 1]").
- Do not make up facts or information not present in the context.
"""

TONE_INSTRUCTIONS = {
    "Professional": "Use a formal, structured, concise, and technical writing style. Avoid casual language and emojis.",
    "Friendly": "Use a warm, encouraging, conversational style. Address the user naturally using 'you' where appropriate.",
    "Simple": "Use short sentences and simple words. Explain jargon in plain language and use analogies when helpful for beginners.",
}


def normalize_tone(tone: Optional[str]) -> str:
    if not tone:
        return "Friendly"
    normalized = tone.strip().lower()
    if normalized == "professional":
        return "Professional"
    if normalized == "simple":
        return "Simple"
    return "Friendly"


def build_system_prompt(tone: Optional[str]) -> str:
    selected_tone = normalize_tone(tone)
    tone_instruction = TONE_INSTRUCTIONS[selected_tone]
    return f"{SYSTEM_PROMPT_BASE}\nTone requirement: {tone_instruction}"


def build_prompt(query: str, context_chunks: List[str]) -> str:
    """
    Build the user prompt by combining context chunks and the user query.

    Args:
        query: The user's question (translated to English)
        context_chunks: List of relevant text chunks from the PDF

    Returns:
        Formatted prompt string ready for the Groq API
    """
    # Format each context chunk with a numbered label
    context_text = "\n\n---\n\n".join(
        [f"[Chunk {i + 1}]:\n{chunk}" for i, chunk in enumerate(context_chunks)]
    )

    # Build the full prompt with context and query
    prompt = f"""CONTEXT FROM DOCUMENT:
{context_text}

USER QUESTION: {query}

Please answer the question in English based on the context provided above.
Instructions for output:
1. Provide a comprehensive, accurate answer to the user question using ONLY the provided context.
2. Respond strictly in English. Do not write in any other language.
3. Do not include any translation or language metadata in your output."""

    return prompt


def is_hybrid_language(lang: str) -> bool:
    """
    Check if a language is a hybrid/code-mixed language (typically ends with 'glish' or 'lish' but is not English).
    """
    lang_lower = lang.lower()
    if lang_lower == "english":
        return False
    return lang_lower.endswith("glish") or lang_lower.endswith("lish")


def translate_query_to_english(query: str, detected_language: str) -> str:
    """
    Translate query to English. Uses Groq LLaMA for hybrid/code-mixed languages, and IndicTrans2 for other languages.
    """
    if is_hybrid_language(detected_language):
        if not groq_client:
            return query
        try:
            print(f"Translating hybrid query ({detected_language}) to English via Groq...")
            chat_completion = safe_chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a precise translator. Translate the following {detected_language} (base Indian language mixed with English and written in Latin/Roman script) query into clean, standard English. Respond ONLY with the translated English text, without any introduction, quotes, explanations, or extra text."
                    },
                    {"role": "user", "content": query},
                ],
                model=GROQ_MODEL,
                temperature=0.1,
                max_tokens=256,
            )
            translation = chat_completion.choices[0].message.content.strip()
            if translation.startswith('"') and translation.endswith('"'):
                translation = translation[1:-1].strip()
            return translation
        except Exception as e:
            print(f"Error translating hybrid query {detected_language} to English via Groq: {e}")
            return query
    else:
        return translate_to_english(query, detected_language)


HYBRID_DESCRIPTIONS = {
    "Hinglish": "Hindi language mixed with English and written in the Latin/Roman script",
    "Odilish": "Odia/Oriya language mixed with English and written in the Latin/Roman script. Use natural Odia pronouns and grammar (for example: 'mu', 'mora', 'tame', 'karuchi', 'karantu', 'bujhi', 'kintu', 'bisayare'). Avoid Hindi words and Hindi sentence shapes such as 'hai', 'aur', 'samajh', 'mujhe', 'tum', 'karna', 'par', 'sahi'.",
}

SUPPORTED_LANGUAGES = {"English", "Hindi", "Odia", "Hinglish", "Odilish"}
# Stores only explicit in-chat override choices (not auto-detect/sidebar defaults)
session_language: Dict[str, str] = {}


def normalize_preferred_language(preferred_language: Optional[str]) -> Optional[str]:
    """Normalize sidebar language preference to supported canonical names."""
    if not preferred_language:
        return None
    raw = preferred_language.strip().lower()
    if raw in {"auto detect", "auto", "autodetect"}:
        return None
    if raw in {"english", "eng"}:
        return "English"
    if raw in {"hindi", "hin"}:
        return "Hindi"
    if raw in {"odia", "oriya", "or"}:
        return "Odia"
    if raw in {"hinglish"}:
        return "Hinglish"
    if raw in {"odilish", "odlish", "odish", "orlish"}:
        return "Odilish"
    return None


def detect_language_override_intent(query: str) -> Optional[str]:
    """Detect in-message language override intent from common phrases."""
    q = query.lower()

    override_patterns = [
        ("English", [
            r"\breply in english\b", r"\banswer in english\b", r"\brespond in english\b",
            r"\benglish re de\b", r"\benglish re dia\b", r"\benglish re kaha\b", r"\benglish re kuha\b", r"\benglish mein bolo\b",
        ]),
        ("Hindi", [
            r"\breply in hindi\b", r"\banswer in hindi\b", r"\brespond in hindi\b",
            r"\bhindi mein bolo\b", r"\bab hindi re kaha\b", r"\bhindi re de\b", r"\bhindi re dia\b", r"\bhindi re kuha\b",
        ]),
        ("Odia", [
            r"\breply in odia\b", r"\banswer in odia\b", r"\brespond in odia\b",
            r"\bodia re de\b", r"\bodia re dia\b", r"\bodia re kaha\b", r"\bodia re kuha\b",
            r"\bodia re .*\b(de|dia|kaha|kuha)\b",
        ]),
        ("Hinglish", [
            r"\breply in hinglish\b", r"\banswer in hinglish\b", r"\brespond in hinglish\b",
            r"\bhinglish mein bolo\b",
        ]),
        ("Odilish", [
            r"\breply in odilish\b", r"\banswer in odilish\b", r"\brespond in odilish\b",
            r"\bodilish re de\b", r"\bodilish re dia\b", r"\bodilish re kaha\b", r"\bodilish re kuha\b",
            r"\bodish re de\b", r"\bodish re dia\b", r"\bodlish re de\b", r"\bodlish re dia\b",
            r"\bodilish re .*\b(de|dia|kaha|kuha)\b",
        ]),
    ]

    for language, patterns in override_patterns:
        if any(re.search(p, q) for p in patterns):
            return language

    return None


def resolve_response_language(
    session_id: str,
    query: str,
    detected_language: str,
    preferred_language: Optional[str],
) -> str:
    """Priority: mid-chat override > sidebar preference > auto-detect."""
    override_lang = detect_language_override_intent(query)
    if override_lang:
        # Persist explicit mid-chat override for subsequent messages in this session.
        session_language[session_id] = override_lang
        return override_lang

    # If user explicitly changed language mid-chat earlier, keep honoring it.
    if session_id in session_language:
        return session_language[session_id]

    preferred = normalize_preferred_language(preferred_language)
    if preferred:
        return preferred

    if detected_language in SUPPORTED_LANGUAGES:
        return detected_language

    return "English"


def translate_answer_to_hybrid(answer: str, target_lang: str) -> str:
    """
    Translate an English response to supported Hinglish or Odilish using Groq LLaMA or Gemini.
    """
    from services.translator import get_gemini_api_key
    if not groq_client and not get_gemini_api_key():
        return answer
    try:
        print(f"Translating answer back to hybrid language {target_lang}...")
        desc = HYBRID_DESCRIPTIONS.get(
            target_lang, 
            f"{target_lang} (the base Indian language mixed with English and written in the Latin/Roman alphabet)"
        )
        chat_completion = safe_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a precise translator. Translate the following English text into {target_lang} "
                        f"which is {desc}, using English words where appropriate for technical terms (e.g. 'hypothesis', 'statement', 'researcher', 'theory', 'document', 'chunk'). "
                        f"Important: for Odilish, keep it strictly Odia + English. Use natural Odia pronouns and sentence flow: 'mu', 'mora', 'tame', 'karuchi', 'karantu', 'bujhi', 'kintu', 'bisayare', 'thik', 'ache'. "
                        f"Do NOT introduce Hindi words or Hindi sentence shapes such as 'hai', 'aur', 'uska', 'samajh', 'mujhe', 'tum', 'kya', 'karna', 'par', 'sahi'. "
                        f"If a word is naturally English for research or technical content, use that English word and keep the surrounding grammar Odia. "
                        f"Ensure the translation reads naturally like standard conversational {target_lang}. "
                        f"Respond ONLY with the translated text, without any introduction, quotes, explanations, or extra text."
                    )
                },
                {"role": "user", "content": answer},
            ],
            model=GROQ_MODEL,
            temperature=0.3,
            max_tokens=1024,
        )
        translated = chat_completion.choices[0].message.content.strip()
        if target_lang == "Odilish":
            translated = normalize_odish_output(translated)
        return translated
    except Exception as e:
        print(f"Error translating answer to hybrid language {target_lang}: {e}")
        return answer


def run_rag_chain(
    query: str,
    session_id: str,
    detected_language: str,
    history: Optional[List[Dict[str, str]]] = None,
    preferred_language: Optional[str] = None,
    tone: Optional[str] = "Friendly",
) -> Dict[str, Any]:
    """
    Execute the full RAG pipeline:
    1. Retrieve top-5 relevant chunks from ChromaDB
    2. Build a context-enriched prompt
    3. Call Groq API (LLaMA) for answer generation
    4. Return answer with source metadata

    Args:
        query: The user's question string
        session_id: The session ID to scope the ChromaDB search
        detected_language: Detected language of the query (for prompt construction)
        history: Optional conversation history list of dicts

    Returns:
        Dict with keys: 'answer' (str), 'sources' (list of source metadata dicts)
    """
    
    response_language = resolve_response_language(
        session_id=session_id,
        query=query,
        detected_language=detected_language,
        preferred_language=preferred_language,
    )

    # Translate non-English query to English for better search accuracy
    search_query = query
    if detected_language != "English":
        print(f"Translating query from {detected_language} to English...")
        search_query = translate_query_to_english(query, detected_language)
        print(f"Translated Search Query: {search_query}")

    # Step 1: Retrieve the most relevant chunks from ChromaDB using the translated English query
    retrieved = retrieve_chunks(session_id=session_id, query=search_query)

    if not retrieved:
        return {
            "answer": "I couldn't find any relevant information in the uploaded document. Please make sure a PDF has been uploaded for this session.",
            "sources": [],
        }

    # Extract just the text from retrieved results for the prompt
    context_chunks = [r["text"] for r in retrieved]

    # Build source attribution list for the response
    sources = [
        {
            "filename": r["metadata"].get("filename", "Unknown"),
            "chunk_index": r["metadata"].get("chunk_index", 0),
            "relevance_score": round(max(0.0, min(1.0, 1 - r["distance"])), 4),  # Clamp to [0, 1]
        }
        for r in retrieved
    ]

    # Step 2: Build the user prompt with context (using the translated English search_query)
    prompt = build_prompt(search_query, context_chunks)

    # Step 3: Call Groq API (LLaMA model)
    try:
        if not groq_client:
            return {
                "answer": "Groq API is not configured. Please set the GROQ_API_KEY in your .env file.",
                "sources": sources,
            }

        # Build list of messages for Groq completion, including tone-aware system prompt and chat history
        messages = [{"role": "system", "content": build_system_prompt(tone)}]
        if history:
            for h in history:
                role = "assistant" if h.get("role") == "bot" else h.get("role", "user")
                messages.append({"role": role, "content": h.get("content", "")})
        messages.append({"role": "user", "content": prompt})

        # Use the Groq chat completions API with system + history + user messages
        chat_completion = safe_chat_completion(
            messages=messages,
            model=GROQ_MODEL,
            temperature=0.3,       # Lower temperature for factual Q&A
            max_tokens=1024,
        )

        answer = chat_completion.choices[0].message.content

        # Translate answer according to resolved response language preference/override
        if is_hybrid_language(response_language):
            print(f"Translating answer back to hybrid language {response_language} via Groq...")
            translated_answer = translate_answer_to_hybrid(answer, response_language)
            answer = f"{translated_answer}\n\n*(Translated to {response_language})*"
        elif response_language != "English":
            print(f"Translating answer back to {response_language} via AI4Bharat IndicTrans2...")
            translated_answer = translate_from_english(answer, response_language)
            answer = f"{translated_answer}\n\n*(Translated via AI4Bharat/IndicTrans2)*"

    except Exception as e:
        # Handle API errors gracefully
        answer = f"Error generating response: {str(e)}. Please check your GROQ_API_KEY."

    return {
        "answer": answer,
        "sources": sources,
    }
