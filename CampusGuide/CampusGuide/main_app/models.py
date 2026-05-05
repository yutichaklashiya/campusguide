from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


# ================= OTP MODEL =================

class EmailOTP(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"))

    otp = models.CharField(max_length=6, verbose_name=_("OTP"))

    is_verified = models.BooleanField(default=False, verbose_name=_("Is Verified"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Email OTP")
        verbose_name_plural = _("Email OTPs")

    def __str__(self):
        return f"{self.user.username} OTP"



# ================= FEEDBACK MODEL =================

class Feedback(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("User"))

    name = models.CharField(max_length=100, verbose_name=_("Name"))

    email = models.EmailField(verbose_name=_("Email"))

    rating = models.IntegerField(default=0, verbose_name=_("Rating"))

    message = models.TextField(verbose_name=_("Message"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Feedback")
        verbose_name_plural = _("Feedbacks")

    def __str__(self):
        return f"{self.name} - {self.rating}⭐"

    # 🔹 Check positive feedback
    def is_positive(self):
        return self.rating >= 4



# ================= USER QUERY MODEL =================

class QueryLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("User"))
    question = models.TextField(verbose_name=_("Question"))
    response = models.TextField(blank=True, null=True, verbose_name=_("Response"))
    language = models.CharField(max_length=10, verbose_name=_("Language"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Query Log")
        verbose_name_plural = _("Query Logs")

    def __str__(self):
        return self.question