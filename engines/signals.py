from django.apps import apps
from django.conf import settings
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from engines.models import Module

EXCLUDED_APPS = {
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'drf_spectacular',
    'configs',
    'engines',
}

@receiver(post_migrate)
def detect_and_save_modules(sender, **kwargs):
    if sender.name != "engines":
        return 

    installed_apps = set(settings.INSTALLED_APPS) - EXCLUDED_APPS
    existing_modules = set(Module.objects.values_list('name', flat=True))

    new_modules = installed_apps - existing_modules
    modules_to_create = [Module(name=app, installed=False, version="0.1") for app in new_modules]

    if modules_to_create:
        Module.objects.bulk_create(modules_to_create)
        print(f"Added {len(modules_to_create)} new modules to the database.")
