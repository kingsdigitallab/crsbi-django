"""Defines custom signals and signal receivers."""

from django.conf import settings
from django.core.mail import send_mail
from django.dispatch import receiver, Signal

import sculpture.models


site_change = Signal(providing_args=['site'])


@receiver(site_change, dispatch_uid='site_status_change',
          sender=sculpture.models.Site)
def site_change_callback (sender, **kwargs):
    site = kwargs['site']
    previous_status = sculpture.models.Site.objects.get(pk=site.pk).status
    new_status = site.status
    if previous_status != new_status:
        email_addresses = []
        for author in site.authors.all():
            try:
                email = author.user_profile.user.email
                if email:
                    email_addresses.append(email)
            except:
                pass
        if email_addresses:
            body = '''Your CRSBI site report for "%s" has had its status changed from "%s" to "%s".''' % (site.get_title(), previous_status.name, new_status.name)
            send_mail('CRSBI site report status change', body,
                      settings.DEFAULT_FROM_EMAIL, email_addresses)
