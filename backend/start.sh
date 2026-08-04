#!/bin/bash
# BhashaBot Backend Startup Script
# Run this instead of uvicorn directly to ensure HuggingFace models
# download to D drive and NOT C drive.

echo "🚀 Starting BhashaBot backend..."

# Activate the virtual environment
source venv/Scripts/activate

# Force HuggingFace to use D drive for model storage
export HF_HOME="D:/bhashabot/backend/hf_cache"
export TRANSFORMERS_CACHE="D:/bhashabot/backend/hf_cache"
export SENTENCE_TRANSFORMERS_HOME="D:/bhashabot/backend/hf_cache"

echo "✅ HF_HOME set to: $HF_HOME"
echo "✅ Starting uvicorn on http://localhost:8000 ..."

# Start the FastAPI server
uvicorn main:app --reload
