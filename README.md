# canopydash

## Running the django project locally

Use the following command to run the project locally

```
python manage.py runserver
```

## Installing dependencies

Create the virtual environment in that directory (make sure it is called venv otherwise it will be tracked by github)

```
python3 -m venv venv
```

Activate the virtual environment

```
source venv/bin/activate
```

Install the necessary dependencies

```
pip install -r requirements.txt
```

To deactivate the virtual environment use

```
deactivate
```

## Project Structure

```text
canopydash/
├── manage.py
├── requirements.txt
├── docker-compose.yml
├── .dockerignore
├── .gitignore
├── .env

├── docker/                         # infra config
│   ├── django/                     # Django app container
│   │   └── Dockerfile
│   ├── celery/                     # Celery worker
│   │   └── Dockerfile
│   ├── nginx/                      # Serves HLS/static
│   │   └── nginx.conf
│   └── redis/                      # Redis config (if customized)

├── canopydash/                     # Django project settings
│   ├── __init__.py
│   ├── settings.py                 # Project-wide config
│   ├── urls.py                     # Mounts app routes
│   ├── celery.py                   # Celery init and config
│   └── wsgi.py                     # WSGI entrypoint

├── live/                           # Handles all camera/video logic
│   ├── __init__.py
│   ├── views.py                    # Frontend (HTML) views
│   ├── api.py                      # API endpoints (clip, frame)
│   ├── tasks.py                    # Celery tasks (FFmpeg background jobs)
│   ├── urls.py                     # Routes for views + API
│   ├── models.py
│   ├── utils.py                    # Shared functions: file locators, ffmpeg helpers
│   ├── templates/
│   │   ├── live.html               # Live stream display
│   │   └── video_list.html         # Browse/download video segments
│   └── static/
│       └── live/
│           └── js/
│               └── player.js       # Handles stream switching / frontend logic

├── metrics/                        # Handles ML output + plant data
│   ├── __init__.py
│   ├── views.py                    # Frontend dashboard (charts)
│   ├── api.py                      # POST endpoints from inference Jetson
│   ├── models.py                   # PlantMetric, Plant, TimeSeriesPoint
│   ├── urls.py                     # Routes for views + API
│   ├── templates/
│   │   └── metrics/
│   │       └── dashboard.html      # Metric visualization
│   └── static/
│       └── metrics/
│           └── js/
│               └── dashboard.js    # Chart.js, AJAX updates
```
