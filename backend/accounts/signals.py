from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, UserActivity
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=CustomUser)
def create_user_log(sender, instance, created, **kwargs):
    """Create user activity log on user creation"""
    if created:
        try:
            UserActivity.objects.create(
                user=instance,
                activity_type='create',
                description=f'User account created: {instance.username}',
                ip_address='127.0.0.1'
            )
            logger.info(f"User created: {instance.username}")
        except Exception as e:
            logger.error(f"Failed to create user activity log: {str(e)}")
