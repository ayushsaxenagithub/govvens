#!/bin/bash
set -e

echo "Installing requirements..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Deployment tasks completed. Restart your web server (e.g., Gunicorn or uWSGI) to apply changes."
