from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import EmailOTP, Feedback, QueryLog

@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'is_verified', 'created_at')
    list_filter = ('is_verified',)
    search_fields = ('user__username', 'otp')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('name', 'email', 'message')

@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'language', 'created_at')
    list_filter = ('language', 'created_at')
    search_fields = ('user__username', 'question', 'response')

# Admin Site Customization
admin.site.site_header = _("Campus Guide Administration")
admin.site.site_title = _("Campus Guide Admin Portal")
admin.site.index_title = _("Welcome to Campus Guide Admin")