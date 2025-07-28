## 🔧 Initial Setup Instructions

After cloning the repo and setting up venv, `.env` and DB:

then do this sequentially
```bash
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py setup_default_roles
python manage.py createsuperuser
python manage.py assign_superadmin_role
```
check `accounts/management/commands`

`python manage.py assign_superadmin_role`, 
this command will assign all user into superuser. because when a new user created, null role assign and that's why superuser act as a simple user which has only "view dashboard" permission.

so after creating a superuser run that file and it will assign user with superuser role. then in future `never` run it again.

## if reCaptcha is not showing checkbox in frontend then, go to google cloud console and create a new project
```bash
https://console.cloud.google.com/projectcreate?previousPage=%2Fwelcome%3Finv%3D1%26invt%3DAb32fA%26organizationId%3D0%26project%3Dwoven-respect-467206-i6&organizationId=0&inv=1&invt=Ab32fA
```

then go to this website and register a new site 
```bash
https://www.google.com/recaptcha/admin/create
```

Then fill this information

- Lable: give any name
- reCaptcha type: choose v2, i am not a robot
- Domains: `localhost`, press enter and then add another domain: `127.0.0.1`
- Google Cloud Platform: Choose your project


then copy site key into public key and secret key into private key in `.env` file.

## .env file
```bash
SECRET_KEY=
DJANGO_SETTINGS_MODULE=school_project.settings.dev

DB_NAME=school_management_updated
DB_USER=
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

ALLOWED_HOSTS=localhost,127.0.0.1

RECAPTCHA_PUBLIC_KEY=
RECAPTCHA_PRIVATE_KEY=
```
## requirements.txt file
I created this file using,
```bash
pip freeze > requirements.txt
```