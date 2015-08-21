
# Running the example application

Install git, pip and virtualenv, then follow these steps to download and run
the example application in this directory:

```bash
$ git clone git://github.com/brilliantorg/django-components.git
$ cd django-components/example
$ virtualenv venv
$ . venv/bin/activate
$ pip install -r requirements.txt
```

Next create the database tables and an admin user.

On Django 1.6 and below:

```bash
$ python manage.py syncdb --migrate
```

On Django 1.7 and above:

```bash
$ python manage.py migrate
$ python manage.py createsuperuser
```

Now run the Django development server:

```bash
$ python manage.py runserver
```

The examples are now available at http://127.0.0.1:8000.
