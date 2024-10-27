echo "render_build.sh running"

# exit on error
set -o errexit
echo "no errors"

# install python dependencies
pip install -r ../requirements.txt
echo "python dependencies installed"

# collect static files
python throwin/manage.py collectstatic --noinput
echo "static files collected"

# migrate
python throwin/manage.py migrate
echo "db migrated"
