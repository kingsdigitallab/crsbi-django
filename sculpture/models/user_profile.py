from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save


class UserProfile (models.Model):

    user = models.OneToOneField(User)

    class Meta:
        app_label = 'sculpture'
        ordering = ['user__first_name', 'user__last_name', 'user__username']

    def __str__ (self):
        user = self.user
        return '%s %s (%s)' % (user.first_name, user.last_name, user.username)

    @property
    def is_editor (self):
        """Returns True if the user is a member of the Editors group."""
        if self.user.groups.filter(name='Editors'):
            return True
        return False


# Create a UserProfile whenever a new User is created.
def create_user_profile (sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User,
                  dispatch_uid='sculpture.models.user_profile')
