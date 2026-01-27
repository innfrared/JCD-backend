#!/bin/bash
# Setup script for Jasmine Backend

echo "Setting up Jasmine Backend..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

pip install --upgrade pip

pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate

echo ""
echo "Setup complete!"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To create a superuser, run:"
echo "  python manage.py createsuperuser"
echo ""
echo "To start the development server, run:"
echo "  python manage.py runserver"

