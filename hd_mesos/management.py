from django.contrib.auth.hashers import make_password
from django.db.models.signals import post_migrate
from .models import Users

def init_db(sender, **kwargs):
    if not Users.objects.exists():
        Users.objects.create(username='admin',nickname='admin',password=make_password('admin'),role=0)

post_migrate.connect(init_db)