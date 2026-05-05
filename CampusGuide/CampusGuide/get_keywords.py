import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CampusGuide.settings')
django.setup()

from main_app.models import QueryLog
from django.db.models import Count

keyword_counts = QueryLog.objects.values('question').annotate(count=Count('id')).order_by('-count')[:20]
for item in keyword_counts:
    print(f"{item['question']}: {item['count']}")
