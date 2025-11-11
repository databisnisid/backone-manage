# BackOne Manage - Virtual Network

## Installation
	virtualenv venv -p python3
	source venv/bin/activate
	pip install -r requirements.txt
	python manage.py migrate
	python manage createsuperuser

## Running
	- Modify .env -> Copy from env.example
	- source /venv/bin/activate
	- ./start.ds (use screen to run as daemon)

## Settings
	- Login as superuser
	- Create Controllter
	- Create Features
	- Create Organizations
	- Create user with Organizations
	
## MQTT
	- Running MQTT workers

