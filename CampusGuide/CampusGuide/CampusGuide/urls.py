from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

from django.shortcuts import redirect

# ✅ Language switch URL
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('', lambda request: redirect('/en/')), # Redirect root to home
    path('login/', lambda request: redirect('/en/login/')), # Redirect bare login to en login
]

# ✅ Main URLs with language support
urlpatterns += i18n_patterns(

    path('admin/', admin.site.urls),

    # Main App URLs
    path('', include('main_app.urls')),
)

# ✅ Static files
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)