# Sherlock Home

Local-first AI agent for personal finance analysis.

## Goals

- Keep financial data local
- Import and normalize bank and credit card statements
- Categorize transactions
- Detect spending patterns and recurring expenses
- Analyze cash flow
- Provide local AI-assisted financial insights
- Avoid sending financial data to third-party AI services

## Planned stack

- Debian on WSL2
- NVIDIA CUDA
- Ollama
- Qwen
- Python
- FastAPI
- PostgreSQL
- Streamlit

## Security principles

- No real financial data committed to Git
- No secrets committed to Git
- Local LLM inference
- Local database
- Explicit tool-based calculations instead of LLM arithmetic
