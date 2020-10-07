# st-remy-django

## clone project
```
git clone --recursive https://github.com/Umbokc/st-remy-django
cd st-remy-django
```

## Setup frontend

Before compile, in `frontend/public/index.html` change the `SERVER_BASE` configuration to your backend url.

Then install dependencies:
```
cd frontend
npm install
```

#### Run frontend
```
npm run serve
```

## Setup backend

Create a virtual environment to install dependencies in and activate it:

```
python3.7 -m venv venv
source venv/bin/activate
```

Then install the dependencies:

```
pip install -r requirements.txt
```

Add secret key to SECRET_KEY in `st_remy/settings.py`

Create tables:
```
python manage.py migrate
```

Collect static:
```
python manage.py collectstatic
```

Run server:

```
python manage.py runserver
```
