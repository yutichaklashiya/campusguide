import random
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required
from django.db.models.functions import TruncDate
from django.utils.translation import gettext as _

from .models import EmailOTP, Feedback, QueryLog
from .utils import translate_to_english, translate_back
from .chatbot_utils import get_response
import json


# ================= SIGNUP =================
def signup(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        full_name = request.POST.get("full_name", "").strip()

        if User.objects.filter(username=username).exists():
            return render(request,"main_app/signup.html",{"error":"Username already exists"})

        if User.objects.filter(email=email).exists():
            return render(request,"main_app/signup.html",{"error":"Email already registered"})

        if password != confirm_password:
            return render(request,"main_app/signup.html",{"error":"Passwords do not match"})

        first_name = ""
        last_name = ""
        if full_name:
            parts = full_name.split()
            first_name = parts[0]
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=False
        )

        otp = str(random.randint(100000,999999))
        EmailOTP.objects.create(user=user,otp=otp)

        send_mail(
            "CampusGuide OTP Verification",
            f"Your OTP is {otp}",
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False
        )

        request.session["user_id"] = user.id

        return redirect("verify_otp")

    return render(request,"main_app/signup.html")


# ================= VERIFY OTP =================
def verify_otp(request):

    user_id = request.session.get("user_id")

    if not user_id:
        return redirect("signup")

    user = User.objects.get(id=user_id)

    if request.method == "POST":

        entered_otp = request.POST.get("otp")

        try:
            otp_obj = EmailOTP.objects.get(user=user)

            if otp_obj.otp == entered_otp:

                user.is_active = True
                user.save()

                otp_obj.delete()
                del request.session["user_id"]

                return redirect("login")

            else:
                return render(request,"main_app/verifyotp.html",{"error":"Invalid OTP"})

        except EmailOTP.DoesNotExist:
            return render(request,"main_app/verifyotp.html",{"error":"OTP expired"})

    return render(request,"main_app/verifyotp.html")


# ================= RESEND OTP =================

def resend_otp(request):

    user_id = request.session.get("user_id")

    if not user_id:
        return redirect("signup")

    user = User.objects.get(id=user_id)

    EmailOTP.objects.filter(user=user).delete()

    otp = str(random.randint(100000,999999))

    EmailOTP.objects.create(user=user, otp=otp)

    send_mail(
        "CampusGuide OTP Verification",
        f"Your NEW OTP is {otp}",
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False
    )

    return redirect("verify_otp")


# ================= LOGIN =================

def login_view(request):

    message = ""
    next_url = request.GET.get('next', '')
    if next_url == '/chat/' or next_url.endswith('/chat/'):
        message = "Please login or sign up to chat with the Campus Guide."

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request,username=username,password=password)

        if user:
            login(request,user)
            return redirect(request.POST.get('next') or next_url or "home")

        return render(request,"main_app/login.html",{"error":"Invalid credentials","message":message, "next": next_url})

    return render(request,"main_app/login.html",{"message":message, "next": next_url})


def logout_view(request):
    logout(request)
    return redirect('home')


# ================= ADMIN LOGIN =================
def admin_login(request):

    error = ""

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            error = "Invalid admin credentials"

    return render(request, "main_app/admin_login.html", {"error": error})


# ================= PASSWORD RESET =================

def custom_reset_confirm(request, uidb64, token):

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except:
        return redirect("login")

    if not default_token_generator.check_token(user, token):
        return redirect("login")

    error = ""

    if request.method == "POST":

        p1 = request.POST.get("new_password1")
        p2 = request.POST.get("new_password2")

        if p1 != p2:
            error = "Passwords do not match"

        else:
            user.set_password(p1)
            user.save()
            return redirect("login")

    return render(request,"main_app/reset_confirm.html",{"error":error})


# ================= USER PAGES =================
def home(request):
    return render(request,"main_app/home.html")

def contact(request):
    return render(request,"main_app/contact.html")

@login_required(login_url='login')
def chat(request):
    return render(request,"main_app/chat.html")

def about(request):
    return render(request,"main_app/aboutclg.html")

def history(request):
    return render(request,"main_app/history.html")

def academic(request):
    return render(request,"main_app/acadamicdepartment.html")

def achievements(request):
    return render(request,"main_app/achievements.html")


# ================= FEEDBACK =================
def feedback(request):

    if request.method == "POST":

        rating = request.POST.get("rating")
        message = request.POST.get("message")

        Feedback.objects.create(
            rating=rating,
            message=message
        )

        return redirect("home")

    return render(request,"main_app/feedback.html")


# ================= ADMIN DASHBOARD =================
@login_required
def admin_dashboard(request):

    if not request.user.is_staff:
        return redirect("login")
     
    total_queries = QueryLog.objects.count()
    total_users = User.objects.count()

    total_feedback = Feedback.objects.count()
    positive_feedback = Feedback.objects.filter(rating__gte=4).count()

    positive_percentage = round((positive_feedback / total_feedback) * 100, 1) if total_feedback > 0 else 0
    avg_rating = Feedback.objects.aggregate(Avg('rating'))['rating__avg'] or 0

    recent_queries = QueryLog.objects.all().order_by('-created_at')[:5]

    lang_data = QueryLog.objects.values('language').annotate(count=Count('id'))
    allowed_langs = {"en": "English", "gu": "Gujarati", "hi": "Hindi"}
    lang_totals = {"en": 0, "gu": 0, "hi": 0}
    for row in lang_data:
        raw_lang = str(row.get("language", "")).strip().lower()
        lang_code = raw_lang.split("-")[0] if raw_lang else ""
        if lang_code in lang_totals:
            lang_totals[lang_code] += int(row.get("count", 0))
    languages = [allowed_langs["en"], allowed_langs["gu"], allowed_langs["hi"]]
    language_counts = [lang_totals["en"], lang_totals["gu"], lang_totals["hi"]]

    keyword_data = (
        QueryLog.objects
        .values('question')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    keywords = [x['question'][:20] + "..." if len(x['question']) > 20 else x['question'] for x in keyword_data]
    keyword_counts = [x['count'] for x in keyword_data]

    context = {
        "total_queries": total_queries,
        "total_users": total_users,
        "positive_percentage": positive_percentage,
        "avg_rating": round(avg_rating,1),

        "recent_queries": recent_queries,

        "languages": json.dumps(languages),
        "language_counts": json.dumps(language_counts),

        "keywords": json.dumps(keywords),
        "keyword_counts": json.dumps(keyword_counts)
    }

    return render(request,"main_app/admin_dashboard.html",context)


# ================= ADMIN REVIEW =================
@login_required
def admin_review(request):
    if not request.user.is_staff:
        return redirect("login")

    feedbacks = Feedback.objects.all().order_by('-created_at') if hasattr(Feedback, 'created_at') else Feedback.objects.all()
    # Let's check the Feedback model fields first to be safe, but usually we have created_at
    
    total_feedback = feedbacks.count()
    avg_rating = feedbacks.aggregate(avg=Avg('rating'))['avg'] or 0

    positive = feedbacks.filter(rating__gte=4).count()
    negative = feedbacks.filter(rating__lt=4).count()

    positive_percent = round((positive/total_feedback)*100) if total_feedback > 0 else 0
    negative_percent = round((negative/total_feedback)*100) if total_feedback > 0 else 0

    context = {
        "avg_rating": round(avg_rating, 1),
        "total_feedback": total_feedback,
        "positive_percent": positive_percent,
        "negative_percent": negative_percent,
        "recent_reviews": feedbacks[:10] # Showing more reviews
    }

    return render(request, "main_app/admin_review.html", context)


# ================= LANGUAGE ANALYTICS =================
@login_required
def admin_languse(request):
    if not request.user.is_staff:
        return redirect("login")

    lang_data = QueryLog.objects.values('language').annotate(count=Count('id'))
    allowed_langs = {"en": "English", "gu": "Gujarati", "hi": "Hindi"}
    lang_totals = {"en": 0, "gu": 0, "hi": 0}
    for row in lang_data:
        raw_lang = str(row.get("language", "")).strip().lower()
        lang_code = raw_lang.split("-")[0] if raw_lang else ""
        if lang_code in lang_totals:
            lang_totals[lang_code] += int(row.get("count", 0))

    languages = [allowed_langs["en"], allowed_langs["gu"], allowed_langs["hi"]]
    counts = [lang_totals["en"], lang_totals["gu"], lang_totals["hi"]]

    # Categorization Logic (On-the-fly)
    category_counts = {
        "Admission": QueryLog.objects.filter(question__icontains="admission").count(),
        "Fees": QueryLog.objects.filter(question__icontains="fee").count() + QueryLog.objects.filter(question__icontains="fess").count(),
        "Hostel": QueryLog.objects.filter(question__icontains="hostel").count(),
        "Placement": QueryLog.objects.filter(question__icontains="placement").count(),
        "Courses": QueryLog.objects.filter(question__icontains="course").count(),
    }

    categories = list(category_counts.keys())
    cat_counts = list(category_counts.values())

    recent_queries = QueryLog.objects.all().order_by('-created_at')[:5]

    context = {
        "languages": json.dumps(languages),
        "counts": json.dumps(counts),
        "categories": json.dumps(categories),
        "cat_counts": json.dumps(cat_counts),
        "recent_queries": recent_queries
    }

    return render(request, "main_app/admin_languse.html", context)


# ================= USER QUERY LIST =================
@login_required
def admin_querylog(request):
    if not request.user.is_staff:
        return redirect("login")

    queries = QueryLog.objects.all().order_by('-created_at')

    return render(request,"main_app/admin_userquery.html",{
        "queries":queries
    })


# ================= SEARCH ANALYTICS =================
@login_required
def search_analytics(request):
    if not request.user.is_staff:
        return redirect("login")

    # 1. Top Keywords
    keyword_counts = QueryLog.objects.values('question').annotate(count=Count('id')).order_by('-count')[:10]
    top_keywords = [{"keyword": item['question'][:20] + "..." if len(item['question']) > 20 else item['question'], "count": item['count']} for item in keyword_counts]

    # 2. Category Data
    category_data = [
        {"category": _("Admission"), "count": QueryLog.objects.filter(question__icontains="admission").count()},
        {"category": _("Fees"), "count": QueryLog.objects.filter(question__icontains="fee").count() + QueryLog.objects.filter(question__icontains="fess").count()},
        {"category": _("Hostel"), "count": QueryLog.objects.filter(question__icontains="hostel").count()},
        {"category": _("Placement"), "count": QueryLog.objects.filter(question__icontains="placement").count()},
        {"category": _("Other"), "count": QueryLog.objects.exclude(question__icontains="admission").exclude(question__icontains="fee").exclude(question__icontains="hostel").exclude(question__icontains="placement").count()},
    ]

    # 3. Date Trend (Last 7 Days) - Real-time based on database
    from django.utils import timezone
    from datetime import timedelta
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    date_trend = (
        QueryLog.objects
        .filter(created_at__gte=seven_days_ago)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    
    # Format dates for chart labels and find the busiest day
    date_data = []
    max_count = -1
    top_search_date = "None"
    
    for item in date_trend:
        formatted_date = item['date'].strftime('%d %b')
        count = item['count']
        date_data.append({
            "date": formatted_date,
            "count": count
        })
        if count > max_count:
            max_count = count
            top_search_date = formatted_date

    # 4. Campus Life Trend (Specific keywords) - Real-time and identifying top topic
    campus_topics = [
        {"topic": _("Admission"), "count": QueryLog.objects.filter(question__icontains="admission").count()},
        {"topic": _("Placement"), "count": QueryLog.objects.filter(question__icontains="placement").count()},
        {"topic": _("Fees"), "count": QueryLog.objects.filter(question__icontains="fee").count() + QueryLog.objects.filter(question__icontains="fess").count()},
        {"topic": _("Hostel"), "count": QueryLog.objects.filter(question__icontains="hostel").count()},
        {"topic": _("Library"), "count": QueryLog.objects.filter(question__icontains="library").count()},
        {"topic": _("Canteen"), "count": QueryLog.objects.filter(question__icontains="canteen").count() + QueryLog.objects.filter(question__icontains="food").count()},
        {"topic": _("Events"), "count": QueryLog.objects.filter(question__icontains="event").count()},
        {"topic": _("Sports"), "count": QueryLog.objects.filter(question__icontains="sport").count()},
    ]
    
    # Sort to find the most searched for the badge, but KEEP original list for chart labels consistency
    sorted_topics = sorted(campus_topics, key=lambda x: x['count'], reverse=True)
    
    # Get top topic name for the template
    top_campus_topic = sorted_topics[0]['topic'] if sorted_topics and sorted_topics[0]['count'] > 0 else "None"

    context = {
        "top_keywords": top_keywords,
        "category_data": category_data,
        "date_data": json.dumps(date_data),
        "campus_life_data": campus_topics, # Use unsorted for stable chart labels
        "top_campus_topic": top_campus_topic,
        "top_search_date": top_search_date
    }

    return render(request, "main_app/search_analytics.html", context)


# ================= CHATBOT =================
@login_required(login_url='login')
def chatbot(request):

    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({"response": _("Please login first to use the chatbot.")}, status=403)

        question = request.POST.get("message")
        
        if not question:
            return JsonResponse({"response": _("Please enter a valid question.")})

        try:
            # 🔥 TRANSLATION (REFINED)
            # Use Django's current language instead of guessing from a single name
            current_lang = request.LANGUAGE_CODE.split('-')[0] # 'en', 'gu', etc.
            
            if current_lang != "en":
                # Translate from user's language to English for processing
                english_question, _ = translate_to_english(question)
            else:
                english_question = question

            # Safe user
            user = request.user if request.user.is_authenticated else None

            # 🔥 MAIN CHANGE (Now using English-translated question AND original for proper names)
            answer = get_response(english_question, question)

            # Translate back to the user's language if it's not English
            if current_lang != "en":
                answer = translate_back(answer, current_lang)

             # Save in database
            QueryLog.objects.create(
                user=user,
                question=question,
                response=answer,
                language=current_lang # Save actual language
            )

            return JsonResponse({
                "response": answer
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"response": f"Error: {str(e)}"})

    return JsonResponse({"response": "Invalid request"})


# ================= CHAT HISTORY API =================
@login_required(login_url='login')
def chat_history_api(request):
    """Return the logged-in user's past Q&A pairs as JSON for the history sidebar."""
    logs = (
        QueryLog.objects
        .filter(user=request.user)
        .order_by('-created_at')[:50]
        .values('question', 'response', 'created_at')
    )
    data = []
    for entry in logs:
        data.append({
            'q': entry['question'],
            'a': entry['response'] or '',
            'ts': int(entry['created_at'].timestamp() * 1000)  # JS-compatible ms
        })
    return JsonResponse({'history': data})


# ================= CONTACT =================
def contact(request):
    success = request.GET.get("success") == "1"
    error = ""
    name_value = ""
    message_value = ""

    if request.method == "POST":
        name_value = (request.POST.get("name") or "").strip()
        message_value = (request.POST.get("message") or "").strip()

        if not request.user.is_authenticated:
            error = _("Please login to send a message.")
            return render(request, "main_app/contact.html", {"success": success, "error": error, "name_value": name_value, "message_value": message_value})

        if not name_value or not message_value:
            error = _("Please enter both name and message.")
            return render(request, "main_app/contact.html", {"success": success, "error": error, "name_value": name_value, "message_value": message_value})

        # 🔥 EMAIL SEND
        try:
            send_mail(
                subject="New Contact Message",
                message=f"From: {name_value}\n\nMessage:\n{message_value}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
            return redirect(request.path + "?success=1")
        except Exception as e:
            print("❌ Email Error:", e)
            error = _("Unable to send message right now. Please try again later.")

    return render(request, "main_app/contact.html", {"success": success, "error": error, "name_value": name_value, "message_value": message_value})


# ================= SET LANGUAGE =================
def set_language(request):
    if request.method == "POST":
        lang = request.POST.get("language")
        request.session['language'] = lang
    return redirect(request.META.get('HTTP_REFERER'))