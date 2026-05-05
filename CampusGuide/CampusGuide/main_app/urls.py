from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import contact

urlpatterns = [

    # HOME
    path('', views.home, name='home'),
    path('home/', views.home, name='home_page'),

    # AUTH
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),

    # ADMIN
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/languse/', views.admin_languse, name='admin_languse'),
    path('admin-dashboard/review/', views.admin_review, name='admin_review'),
    path('admin-dashboard/userquery/', views.admin_querylog, name='admin_userquery'),
    path('admin-dashboard/search-analytics/', views.search_analytics, name='search_analytics'),

    # PASSWORD RESET
    path(
        'reset-password/',
        auth_views.PasswordResetView.as_view(
            template_name="main_app/reset_password.html",
            email_template_name="main_app/reset_email.html",
            subject_template_name="main_app/reset_subject.txt",
            html_email_template_name="main_app/reset_email_html.html"
        ),
        name='password_reset'
    ),

    path(
        'reset-password/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name="main_app/reset_done.html"
        ),
        name='password_reset_done'
    ),

    path(
        'reset/<uidb64>/<token>/',
        views.custom_reset_confirm,
        name='password_reset_confirm'
    ),

    path(
        'reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name="main_app/reset_complete.html"
        ),
        name='password_reset_complete'
    ),

    # USER PAGES
    path('history/', views.history, name='history'),
    path('feedback/', views.feedback, name='feedback'),
    path('contact/', views.contact, name='contact'),
    path('chat/', views.chat, name='chat'),
    path('set-language/', views.set_language, name='set_language'),
    path('about/', views.about, name='about'),
    path('academic/', views.academic, name='academic'),
    path('achievements/', views.achievements, name='achievements'),

    # CHATBOT
    path('chatbot/', views.chatbot, name='chatbot'),
    path('chat-history/', views.chat_history_api, name='chat_history_api'),

]