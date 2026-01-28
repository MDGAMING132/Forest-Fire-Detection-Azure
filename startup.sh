#!/bin/bash
# Azure App Service startup script for Forest Fire Detection

echo "Starting Forest Fire Detection Backend..."
gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers 2 backend.app:app
