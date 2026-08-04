"""
Translator Service - Language detection and translation utilities
Uses langdetect for language identification.
Includes a placeholder interface for IndicTrans2 integration.
"""



# langdetect is a port of Google's language-detection library
# Supports 55+ languages including major Indian languages
from langdetect import detect, DetectorFactory, LangDetectException
import os
import re
from typing import Optional
from groq import Groq

# Set a fixed seed for reproducible language detection results
# (langdetect uses randomness internally by default)
DetectorFactory.seed = 42

# Configure Groq client for LLM-based language detection
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

def get_gemini_api_key() -> Optional[str]:
    """
    Dynamically loads and returns the GEMINI_API_KEY from environment/dotenv.
    Uses override=True to ensure any recent edits to .env are picked up.
    """
    try:
        from dotenv import load_dotenv
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dotenv_path = os.path.join(backend_dir, ".env")
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path=dotenv_path, override=True)
        else:
            load_dotenv(override=True)
    except Exception as e:
        print(f"Warning: Failed to reload .env dynamically: {e}")
    return os.getenv("GEMINI_API_KEY")


def call_gemini_fallback(messages: list, temperature: float = 0.3, max_tokens: int = 1024):
    """
    Calls the Google Gemini API (gemini-1.5-flash) via direct REST requests as a fallback when Groq fails.
    This avoids any dependency on the 'google-generativeai' package.
    """
    gemini_key = get_gemini_api_key()
    if not gemini_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables.")
    
    # Format system prompt, history and query into a single text prompt for Gemini
    prompt_parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            prompt_parts.append(f"System Instructions:\n{content}\n")
        elif role == "user":
            prompt_parts.append(f"User:\n{content}\n")
        elif role in ["assistant", "bot"]:
            prompt_parts.append(f"BhashaBot:\n{content}\n")
            
    prompt_parts.append("BhashaBot:")
    full_prompt = "\n".join(prompt_parts)
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": full_prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }
    
    print("[Gemini Fallback] Sending query to gemini-1.5-flash via REST API...")
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    # Extract the generated text
    try:
        generated_text = data['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError) as err:
        print(f"Error parsing Gemini REST API response: {data}")
        raise ValueError(f"Failed to parse Gemini response: {err}")
        
    class MockChoiceMessage:
        def __init__(self, content):
            self.content = content
            
    class MockChoice:
        def __init__(self, content):
            self.message = MockChoiceMessage(content)
            
    class MockChatCompletion:
        def __init__(self, content):
            self.choices = [MockChoice(content)]
            
    return MockChatCompletion(generated_text)


def safe_chat_completion(messages: list, model: str = None, temperature: float = 0.3, max_tokens: int = 1024):
    """
    Calls the Groq chat completion API. If a 429 Rate Limit error occurs,
    automatically falls back to a lighter model (llama-3.1-8b-instant).
    If that also fails (or if Groq is not configured), falls back to Gemini if available.
    """
    from typing import Any
    
    gemini_key = get_gemini_api_key()
    if not groq_client:
        if gemini_key:
            print("[Groq Fallback] Groq client not initialized. Trying Gemini fallback directly...")
            try:
                return call_gemini_fallback(messages, temperature, max_tokens)
            except Exception as gemini_err:
                print(f"[Gemini Fallback] Gemini fallback failed: {gemini_err}")
        raise ValueError("Groq client is not initialized and Gemini fallback is not available.")
    
    current_model = model or GROQ_MODEL
    fallback_model = "llama-3.1-8b-instant"
    
    try:
        return groq_client.chat.completions.create(
            messages=messages,
            model=current_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:
        error_str = str(e).lower()
        is_rate_limit = "429" in error_str or "rate_limit" in error_str or "rate limit" in error_str
        
        if is_rate_limit and current_model != fallback_model:
            print(f"[Groq Fallback] Rate limit hit for '{current_model}'. Retrying with '{fallback_model}'...")
            try:
                return groq_client.chat.completions.create(
                    messages=messages,
                    model=fallback_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as fallback_err:
                print(f"[Groq Fallback] Fallback request failed: {fallback_err}")
                # Fall back to Gemini if available
                if gemini_key:
                    print("[Groq Fallback] Both Groq models failed. Trying Gemini fallback...")
                    try:
                        return call_gemini_fallback(messages, temperature, max_tokens)
                    except Exception as gemini_err:
                        print(f"[Gemini Fallback] Gemini fallback also failed: {gemini_err}")
                raise e
        else:
            # Fall back to Gemini if available
            if gemini_key:
                print("[Groq Fallback] Groq call failed. Trying Gemini fallback...")
                try:
                    return call_gemini_fallback(messages, temperature, max_tokens)
                except Exception as gemini_err:
                    print(f"[Gemini Fallback] Gemini fallback also failed: {gemini_err}")
            raise e


# Mapping of langdetect language codes to human-readable names
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "or": "Odia",
}

SUPPORTED_LANGUAGES = {"English", "Hindi", "Odia", "Hinglish", "Odilish"}

# Common hybrid/code-mixed words (transliterated into Latin characters)
HYBRID_INDICATORS = {
    # Hindi/Hinglish
    "kya", "hai", "ko", "se", "ek", "jo", "aur", "ki", "ka", "ke", "hota", "hoga", "bhai",
    "yaar", "plz", "please", "karo", "karna", "karke", "krte", "raha", "rahe", "rhi",
    "samjh", "samajh", "na", "nahi", "nhi", "tha", "thi", "the", "bhi", "toh", "to", "ab",
    "pe", "par", "liye", "chahiye", "kaise", "kab", "kuch", "aisa", "waisa", "hum", "tum",
    "aap", "mera", "meri", "mere", "apna", "apne", "apni", "kar", "kr", "ne", "ho", "hu",
    "hoon", "hain", "kardo", "batao", "bata", "likho", "likh", "bolo", "bol", "samjha",
    "samjhao", "dijiye", "do", "karne", "sakte", "sakta", "sakti", "kam", "jyada",
    "sahi", "galat", "hona", "chal", "chalo", "gaya", "gayi", "gaye", "aa", "aao", "aaya",
    "aayi", "aaye", "de", "kuch", "sab", "koi", "hi", "he",
    # Tamil/Tanglish
    "inniku", "naan", "nee", "nalla", "iruku", "panna", "mudiyuma", "teriyum", "varam",
    "enga", "solla", "kelu", "vanga", "ponga", "pannunga", "da", "di", "ma", "pa", "irukein",
    # Bengali/Benglish
    "amra", "tumi", "ami", "kore", "dao", "koro", "korbo", "hobe", "hoyeche", "bhalo",
    "khabar", "ta", "ekta", "kotha", "kichu", "parbo", "ashbe",
    # Odia/Odilish
    "dikhantu", "lekha", "achi", "kana", "mate", "tame", "ame", "karantu", "heba", "kala",
    "kemiti", "kou", "seita", "kahantu", "dekhantu", "bujheiparibu", "bujheiparibe", "bujhantu",
    "bujhi", "bujhau", "heuchi", "hela", "helani", "karuchi", "karibe", "kahuchi", "kaha",
    "nahin", "kie", "sange", "sahita", "paribu", "paribe", "odia", "oriya", "odish", "odlish",
    "seithi", "achi", "bujhi", "karantu", "karuchi", "helani", "kahantu", "dekhantu"
}

ODISH_MARKERS = {
    "achi", "seithi", "mate", "tame", "ame", "bujhi", "bujhau", "bujheiparibu", "bujheiparibe",
    "karuchi", "karucha", "karantu", "karibe", "helani", "hela", "heuchi", "dekhantu", "kahantu", "kahuchi",
    "kena", "kemiti", "sange", "sahita", "paribu", "paribe", "odia", "oriya", "odish", "odlish"
}

BENGALI_MARKERS = {
    "ami", "tumi", "amra", "kore", "koro", "kotha", "bhalo", "kichu", "khabar", "ekta", "parbo", "ashbe",
    "boli", "bolchi", "bolo", "bhalo", "bhasha"
}


def get_native_script_language(text: str) -> Optional[str]:
    """
    Identifies if a text contains native Indian scripts and returns the language name.
    Avoids network calls by checking Unicode ranges.
    """
    ranges = {
        "Hindi": (0x0900, 0x097F),
        "Bengali": (0x0980, 0x09FF),
        "Punjabi": (0x0A00, 0x0A7F),
        "Gujarati": (0x0A80, 0x0AFF),
        "Odia": (0x0B00, 0x0B7F),
        "Tamil": (0x0B80, 0x0BFF),
        "Telugu": (0x0C00, 0x0C7F),
        "Kannada": (0x0C80, 0x0CFF),
        "Malayalam": (0x0D00, 0x0D7F),
    }
    counts = {lang: 0 for lang in ranges}
    for char in text:
        cp = ord(char)
        for lang, (start, end) in ranges.items():
            if start <= cp <= end:
                counts[lang] += 1
                break
    max_lang = max(counts, key=counts.get)
    if counts[max_lang] > 0:
        return max_lang
    return None


def is_hybrid_text(text: str) -> bool:
    """
    Determine if text is likely a code-mixed / hybrid language written in Latin script.
    """
    text_lower = text.lower().strip()

    # Check if user explicitly references a hybrid language or translation
    hybrid_keywords = [
        "hinglish", "tanglish", "benglish", "odlish", "odish", "orlish", "teluglish", "kanglish", "marathlish",
        "translate to", "explain in", "answer in", "reply in", "write in", "speak in", "respond in",
        "odia", "oriya", "hindi", "tamil", "telugu", "kannada", "bengali", "marathi", "gujarati", "punjabi"
    ]
    if any(kw in text_lower for kw in hybrid_keywords):
        return True

    # Tokenize words to search in the vocabulary
    words = re.findall(r"\b[a-z]+\b", text_lower)
    if not words:
        return False

    # Strong Odia/Odilish signals should be recognized even in very short phrases.
    if any(word in ODISH_MARKERS for word in words):
        return True

    # Allow suffix-based Odish-style patterns such as -uchi, -antu, -ichi, -ibe, -ibu.
    odish_suffix_hits = [word for word in words if re.search(r"(?:uchi|antu|ichi|ibe|ibu|ani)$", word)]
    if odish_suffix_hits:
        return True

    # Check for presence of hybrid indicator words.
    # For short code-mixed queries we should not require multiple indicators.
    hybrid_count = sum(1 for w in words if w in HYBRID_INDICATORS)
    if hybrid_count >= 1 and len(words) <= 8:
        return True

    return False


def detect_language_llm(text: str) -> str:
    """
    Use Groq LLaMA to detect the language of a text, specifically recognizing hybrid/code-mixed languages.
    """
    if not groq_client:
        return "English"
    try:
        print(f"[Language Detector] Querying Groq LLaMA to identify language for: '{text}'")
        chat_completion = safe_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a language detection expert. Analyze the given text and determine its language.\n"
                        "Instructions:\n"
                        "- The only supported outputs are English, Hindi, Odia, Hinglish, and Odilish.\n"
                        "- If the user explicitly requests one of these languages, detect the requested target language.\n"
                        "- Use 'Hinglish' for Hindi + English code-switched Latin text.\n"
                        "- Use 'Odilish' for Odia + English code-switched Latin text.\n"
                        "- Return 'English' for every unsupported or uncertain language.\n"
                        "- Respond with ONLY one supported language name, without punctuation or explanation."
                    )
                },
                {"role": "user", "content": text},
            ],
            model=GROQ_MODEL,
            temperature=0.1,
            max_tokens=64,
        )
        detected = chat_completion.choices[0].message.content.strip()
        # Clean quotes or punctuation from model response
        detected = re.sub(r"[^\w\-]", "", detected)
        
        # Standardize common language name variations
        std_name = detected.strip().lower()
        if std_name in ["odish", "odlish", "orlish", "odilish"]:
            return "Odilish"
        if std_name == "oriya":
            return "Odia"

        for name in SUPPORTED_LANGUAGES:
            if name.lower() == std_name:
                return name
        return "English"
    except Exception as e:
        print(f"Error in LLM-based language detection: {e}")
        return "English"


def detect_language(text: str) -> str:
    """
    Detect the language of the given text.
    Uses direct script identification for native Indian scripts.
    Uses Groq LLaMA for hybrid/code-mixed language detection if indicators are found.
    Falls back to langdetect for standard foreign and European languages.

    Args:
        text: Input text string (query or document excerpt)

    Returns:
        One of: "English", "Hindi", "Odia", "Hinglish", or "Odilish".
    """
    trimmed = text.strip()
    if not trimmed:
        return "English"

    # 1. Check for native script languages first (instant check)
    native_lang = get_native_script_language(trimmed)
    if native_lang:
        return native_lang if native_lang in SUPPORTED_LANGUAGES else "English"

    words = re.findall(r"\b[a-z]+\b", trimmed.lower())

    if "mu" in words and ("kuhe" in words or "kahuchi" in words):
        return "Odilish"

    if "tame" in words and ("karucha" in words or "karuchi" in words or "bhal" in words):
        return "Odilish"

    # 3. Check for hybrid/code-mixed text (Latin script representing Indian language)
    if is_hybrid_text(trimmed):
        if any(word in ODISH_MARKERS for word in words):
            return "Odilish"
        if any(re.search(r"(?:uchi|antu|ichi|ibe|ibu|ani)$", word) for word in words):
            return "Odilish"
        return detect_language_llm(trimmed)

    # 4. Fallback to standard langdetect
    try:
        # langdetect needs a minimal length to work reliably, but short Indian hybrid phrases
        # should still be handled by the LLM detector instead of being forced to English.
        if len(trimmed) < 10:
            if any(word in ODISH_MARKERS for word in words):
                return "Odilish"
            if any(re.search(r"(?:uchi|antu|ichi|ibe|ibu|ani)$", word) for word in words):
                return "Odilish"
            return detect_language_llm(trimmed)

        lang_code = detect(trimmed)

        # If langdetect maps it to something other than 'en', check if it might be an unhandled hybrid text
        # (Since code-mixed texts are often misclassified by langdetect as other random languages)
        if lang_code != "en" and lang_code in ["ro", "it", "es", "so", "et", "sw", "tl", "id"]:
            return detect_language_llm(trimmed)

        return LANGUAGE_NAMES.get(lang_code, "English")

    except LangDetectException:
        # If detection fails, check if we can run LLM detection or default to English
        if len(trimmed) > 0:
            return detect_language_llm(trimmed)
        return "English"


import os
import requests

# HuggingFace API Token for calling AI4Bharat's IndicTrans2 models
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

# Official AI4Bharat IndicTrans2 model endpoints on HuggingFace
MODEL_INDIC_TO_EN = "https://api-inference.huggingface.co/models/ai4bharat/indictrans2-indic-en-1B"
MODEL_EN_TO_INDIC = "https://api-inference.huggingface.co/models/ai4bharat/indictrans2-en-indic-1B"

# Mappings for AI4Bharat IndicTrans2 language codes
INDIC_LANG_TOKENS = {
    "English": "eng_Latn",
    "Hindi": "hin_Deva",
    "Odia": "ory_Orya",
}

def query_hf_api(api_url: str, text: str) -> str:
    """
    Helper function to call the HuggingFace Inference API for Seq2Seq translation.
    """
    if not HF_API_TOKEN:
        print("Warning: HF_API_TOKEN missing. Returning original text.")
        return text

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": text}
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        # The HF Seq2Seq API typically returns: [{'translation_text': '...'}] or [{'generated_text': '...'}]
        if isinstance(data, list) and len(data) > 0:
            if 'generated_text' in data[0]:
                return data[0]['generated_text']
            elif 'translation_text' in data[0]:
                return data[0]['translation_text']
                
        print(f"Unexpected HF API response: {data}")
        return text
        
    except Exception as e:
        print(f"HuggingFace API Error: {e}")
        # HF API sometimes returns 503 if the model is loading (Cold start)
        return text

ODISH_STYLE_REPLACEMENTS = {
    "aur": "aru",
    "au": "aru",
    "uska": "tanka",
    "mujhe": "mu",
    "mujhko": "mu",
    "tum": "tame",
    "tumhe": "tameku",
    "samajh": "bujhi",
    "samjh": "bujhi",
    "karna": "kariba",
    "karne": "karibaku",
    "kya": "ki",
    "hai": "achi",
    "hota": "heba",
    "hoga": "heba",
    "bhi": "o",
    "toh": "tebe",
    "par": "kintu",
    "pura": "purna",
    "koi": "kebe",
    "sahi": "thik",
    "galat": "bhul",
    "apko": "tameku",
    "aap": "tame",
    "mera": "mora",
    "meri": "mora",
    "mere": "mora",
    "apna": "apana",
    "apne": "apana",
    "apni": "apana",
    "nahi": "nahi",
    "nhi": "nahi",
    "jemane": "jemiti",
    "pucho": "pacharantu",
    "question pucho": "question pacharantu",
    "about": "bisayare",
    "parib": "pariba",
}


def normalize_odish_output(text: str) -> str:
    """
    Clean translated Odish replies so they stay in Odia + English style instead of drifting into Hindi.
    """
    normalized = text

    # Normalize the most common accidental Hindi/Odish grammar drifts first.
    normalized = re.sub(r"\bquestion\s+pucho\b", "question pacharantu", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bjemane\b", "jemiti", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bparib\b", "pariba", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\blekha\s+about\b", "lekha bisayare", normalized, flags=re.IGNORECASE)

    for src, dst in ODISH_STYLE_REPLACEMENTS.items():
        normalized = re.sub(rf"\b{src}\b", dst, normalized, flags=re.IGNORECASE)

    return normalized


def translate_via_groq(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translates text between any two languages using LLaMA via Groq or Gemini as a fallback/upgrade.
    Used for global languages, hybrid languages, and as a fallback for Indian languages.
    """
    gemini_key = get_gemini_api_key()
    # If Gemini is available, use it for translating low-resource Indian languages (where LLaMA 8B performs poorly)
    is_indic = target_lang in ["Odia", "Tamil", "Telugu", "Kannada", "Malayalam", "Gujarati", "Marathi", "Punjabi", "Assamese", "Bengali"]
    
    if gemini_key and (is_indic or not groq_client):
        try:
            print(f"[Gemini Translator] Translating from {source_lang} to {target_lang}...")
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"You are a professional, precise translator. Translate the following text from {source_lang} to {target_lang}.\n"
                        f"Instructions:\n"
                        f"- Retain formatting, code blocks, Markdown elements, inline code, numbers, and technical terminology exactly as they are in the source.\n"
                        f"- Translate the actual prose content accurately. For Indian languages, write in the native script (e.g. Odia script for Odia, Tamil script for Tamil, etc.).\n"
                        f"- Respond ONLY with the translated text. Do not add quotes, introductory statements, translation explanations, or any other extra text."
                    )
                },
                {"role": "user", "content": text}
            ]
            res = call_gemini_fallback(messages, temperature=0.2, max_tokens=1024)
            translation = res.choices[0].message.content.strip()
            if translation.startswith('"') and translation.endswith('"'):
                translation = translation[1:-1].strip()
            elif translation.startswith("`") and translation.endswith("`"):
                translation = translation[1:-1].strip()
            return translation
        except Exception as e:
            print(f"Gemini translation failed, falling back to Groq: {e}")

    if not groq_client:
        print("Warning: Groq client is not initialized for translation fallback.")
        return text
    try:
        print(f"[Groq Translator] Translating from {source_lang} to {target_lang}...")
        chat_completion = safe_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a professional, precise translator. Translate the following text from {source_lang} to {target_lang}.\n"
                        f"Instructions:\n"
                        f"- Retain formatting, code blocks, Markdown elements, inline code, numbers, and technical terminology exactly as they are in the source.\n"
                        f"- Translate the actual prose content accurately.\n"
                        f"- Respond ONLY with the translated text. Do not add quotes, introductory statements, translation explanations, or any other extra text."
                    )
                },
                {"role": "user", "content": text},
            ],
            model=GROQ_MODEL,
            temperature=0.2,
            max_tokens=1024,
        )
        translation = chat_completion.choices[0].message.content.strip()
        # Clean potential wrapped quotes
        if translation.startswith('"') and translation.endswith('"'):
            translation = translation[1:-1].strip()
        elif translation.startswith("`") and translation.endswith("`"):
            translation = translation[1:-1].strip()
        return translation
    except Exception as e:
        print(f"Error in Groq translation from {source_lang} to {target_lang}: {e}")
        return text

def translate_to_english(text: str, source_lang_name: str) -> str:
    """
    Translate text from a language to English using AI4Bharat's IndicTrans2 via HuggingFace
    for Indian languages, and falling back to Groq LLaMA for global or when HF fails.
    """
    if source_lang_name == "English":
        return text

    # Check if this is a supported Indian language for IndicTrans2
    src_token = INDIC_LANG_TOKENS.get(source_lang_name)
    
    if src_token and HF_API_TOKEN:
        # Format for IndicTrans2: __source_token__ __target_token__ sentence
        formatted_text = f"__{src_token}__ __eng_Latn__ {text}"
        try:
            translation = query_hf_api(MODEL_INDIC_TO_EN, formatted_text)
            if translation and translation != formatted_text:
                # Clean up any residual language prefix the model might output
                clean_prefixes = [
                    f"__{src_token.lower()}__ __eng_latn__:",
                    f"__eng_latn__:",
                    f"{src_token.lower()} eng_latn:",
                    f"eng_latn:"
                ]
                for prefix in clean_prefixes:
                    if translation.lower().startswith(prefix):
                        translation = translation[len(prefix):].strip()
                return translation
        except Exception as e:
            print(f"IndicTrans2 translation failed: {e}. Falling back to Groq...")
            
    # Fallback/Default translation for global or failed Indian translations
    return translate_via_groq(text, source_lang_name, "English")

def translate_from_english(text: str, target_lang_name: str) -> str:
    """
    Translate text from English to a target language using AI4Bharat's IndicTrans2 via HuggingFace
    for Indian languages, and falling back to Groq LLaMA for global or when HF fails.
    """
    if target_lang_name == "English":
        return text

    # Check if this is a supported Indian language for IndicTrans2
    tgt_token = INDIC_LANG_TOKENS.get(target_lang_name)
    
    if tgt_token and HF_API_TOKEN:
        # Format input: __eng_Latn__ __target_token__ sentence
        formatted_text = f"__eng_Latn__ __{tgt_token}__ {text}"
        try:
            translation = query_hf_api(MODEL_EN_TO_INDIC, formatted_text)
            if translation and translation != formatted_text:
                # Clean up any residual language prefix the model might output
                clean_prefixes = [
                    f"__eng_latn__ __{tgt_token.lower()}__:", 
                    f"__{tgt_token.lower()}__:", 
                    f"eng_latn {tgt_token.lower()}:", 
                    f"{tgt_token.lower()}:"
                ]
                for prefix in clean_prefixes:
                    if translation.lower().startswith(prefix):
                        translation = translation[len(prefix):].strip()
                return translation
        except Exception as e:
            print(f"IndicTrans2 translation failed: {e}. Falling back to Groq...")

    # Fallback/Default translation for global or failed Indian translations
    return translate_via_groq(text, "English", target_lang_name)
