# multiplayer_elo
elo rankings for multiplayer game leagues (e.g. carcasonne, settlers of catan)

## run

### using docker

You need to have [docker](ihttps://www.docker.com/) and
[docker-compose](https://docs.docker.com/compose/install/) installed on your machine.

Run

```
$ docker-compose up
```

This builds the images for the API and the UI, runs the containers and you should be good to go.
The database is mounted as a volume, and should persist on the host under
<path-to-multiplayer-epo>/db/elo.db

### without docker

As we have two different apps in this repository we have to set up two different
virtual environments, in this case [conda](https://conda.io/miniconda.html) environments.

Install the api requirements:

```
$ cd <path-to-multiplayer_elo>/api  
$ conda create --name elo_api python=2  
$ source activate elo_api  
$ pip install -r requirements.txt  
```

Start the api:

```
(elo_api)[api]$ gunicorn -b 127.0.0.1:8000 "app:create()"
```

Install the UI requirements:

```
$ cd <path-to-multiplayer_elo>/ui  
$ conda create --name elo_web python=3  
$ source activate elo_ui  
$ pip install -r requirements.txt
```

Now start the ui.

```
(elo_ui)[ui]$ gunicorn -b 127.0.0.1:5000 "app:create_app()"
```

## access

The UI will be available under http://127.0.0.1:5000

Look at the code in api.app for a documentation of the endpoints.

Further thoughts are accessible [here](http:127.0.1:5000/readme) once the UI
is up and running.
