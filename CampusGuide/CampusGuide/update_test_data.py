import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CampusGuide.settings')
django.setup()

from main_app.models import QueryLog

logs = list(QueryLog.objects.all())
for i, log in enumerate(logs):
    if i % 3 == 1:
        log.language = 'hi'
        log.save()
    elif i % 3 == 2:
        log.language = 'gu'
        log.save()

print(f"Successfully updated {len(logs)} records.")
