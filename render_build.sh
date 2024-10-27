echo "render_build.sh running"

# exit on error
set -o errexit

# install python dependencies
pip install -r requirements.txt

# collect static files
python throwin/manage.py collectstatic --noinput

# migrate
python throwin/manage.py migrate
