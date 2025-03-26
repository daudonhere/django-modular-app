from django.db.models.signals import post_migrate
from django.dispatch import receiver
from configs.models import Role  

@receiver(post_migrate)
def create_default_roles(sender, **kwargs):
    if sender.name == "configs":
        default_roles = ["user", "manager", "administrator"]
        for role in default_roles:
            Role.objects.get_or_create(rolename=role)
        print("default roles has been added !")