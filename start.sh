#!/bin/bash
# Activate the venv created by poetry or pip
source .venv/bin/activate
python -m uv run python backend/app.py
