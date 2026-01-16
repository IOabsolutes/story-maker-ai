#!/bin/bash
# scripts/init_ollama.sh
# Initializes Ollama by pulling the required model

set -e

OLLAMA_HOST="${OLLAMA_HOST:-http://ollama:11434}"
MODEL="${OLLAMA_MODEL:-llama3}"

echo "Waiting for Ollama service..."
until curl -s "${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; do
    sleep 2
done

echo "Ollama service is ready!"
echo "Pulling model: ${MODEL}..."

# Pull the model using streaming endpoint
curl -X POST "${OLLAMA_HOST}/api/pull" -d "{\"name\": \"${MODEL}\"}"

echo ""
echo "Model ${MODEL} is ready!"
