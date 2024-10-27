# exit on error
set -o errexit

# install python dependencies
pip install -r requirements.txt

# collect static files
python manage.py collectstatic --noinput

# migrate
python manage.py migrate
