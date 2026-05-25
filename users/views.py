from django.shortcuts import render, redirect
from django.urls import reverse

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
import requests
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


# Create your views here.


def home(request):
    return render(request, 'index.html')


@csrf_exempt  # needed because JS fetch doesn't send Django's csrf token
def signup(request):
    if request.method == 'POST':
        data = json.loads(request.body)  # reads the JSON sent by frontend

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')

        # check if user already exists
        if User.objects.filter(username=email).exists():
            return JsonResponse({'error': 'User already exists'}, status=400)

        # create the user
        user = User.objects.create_user(
            username=email, email=email, password=password)
        user.first_name = name

        # if frontend sent a role and it's 'lawyer', mark user as staff
        is_lawyer = (role == 'lawyer')
        if is_lawyer:
            user.is_staff = True

        user.save()

        # tell frontend whether to redirect to lawyer dashboard
        redirect_url = reverse(
            'lawyer_dashboard') if is_lawyer else reverse('dashboard')

        return JsonResponse({
            'message': 'Registration successful',
            'email': email,
            'is_lawyer': is_lawyer,
            'redirect_url': redirect_url,
        })

    # GET request - just show the page
    return render(request, 'signup.html', {
        'google_client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    })


@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        email = data.get('email')
        password = data.get('password')

        try:
            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)

                # if user was created as a lawyer earlier, send redirect instruction
                is_lawyer = bool(user.is_staff)
                redirect_url = reverse(
                    'lawyer_dashboard') if is_lawyer else reverse('dashboard')

                return JsonResponse({
                    'message': 'Login successful',
                    'email': email,
                    'is_lawyer': is_lawyer,
                    'redirect_url': redirect_url,
                })
            else:
                return JsonResponse({'error': 'Invalid email or password'}, status=401)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    # GET request - just show the page
    return render(request, 'login.html', {
        'google_client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    })


@csrf_exempt
def logout_view(request):
    if request.method == 'POST':
        logout(request)  # destroys the session
        return JsonResponse({'message': 'Logged out successfully'})

    return JsonResponse({'error': 'Invalid method'}, status=405)


@csrf_exempt
def google_oauth(request):
    """Handle Google OAuth login/signup"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        token = data.get('token')

        if not token:
            return JsonResponse({'error': 'No token provided'}, status=400)

        # Verify the token with Google
        CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
        if not CLIENT_ID:
            return JsonResponse(
                {'error': 'Google OAuth not configured'}, status=500
            )

        idinfo = id_token.verify_oauth2_token(
            token, google_requests.Request(), CLIENT_ID
        )

        # Extract user info from token
        email = idinfo.get('email')
        name = idinfo.get('name', '')
        picture = idinfo.get('picture', '')

        if not email:
            return JsonResponse({'error': 'Email not provided'}, status=400)

        # Create or get user
        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                'email': email,
                'first_name': name.split()[0] if name else 'User',
                'last_name': name.split()[1] if len(name.split()) > 1 else '',
            },
        )

        # Log the user in
        login(request, user)

        return JsonResponse({
            'message': 'Login successful',
            'email': email,
            'name': name,
            'picture': picture,
            'is_new_user': created,
        })

    except ValueError as e:
        # Invalid token
        return JsonResponse({'error': 'Invalid token'}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    return render(request, 'dashboard.html', {
        'name': request.user.first_name,
        'email': request.user.email,
    })


def lawyer_dashboard_page(request):
    return render(request, 'lawyer-dashboard.html')


def consult_page(request):
    return render(request, 'consult.html')


def lawyers(request):
    return render(request, 'lawyers.html')


def appointments(request):
    return render(request, 'appointments.html')


def book_appointment(request):
    return render(request, 'book.html')


def meeting(request):
    return render(request, 'meeting.html')


@csrf_exempt
def consult_ai(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        body = json.loads(request.body)
        message = body.get("message", "").strip()

        if not message:
            return JsonResponse({"error": "No message provided"}, status=400)

        # Call your Flask AI service
        flask_response = requests.post(
            "http://localhost:5001/ask",
            json={"question": message},
            timeout=30
        )

        ai_data = flask_response.json()
        answer = ai_data.get(
            "answer", "Sorry, I could not process your request.")

        return JsonResponse({
            "reply": answer,
            "area": detect_legal_area(message),
            "recommended": [],
            "aiPowered": True
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def detect_legal_area(message):
    message = message.lower()
    if any(w in message for w in ["landlord", "rent", "deposit", "tenant"]):
        return "Property / Tenancy Law"
    elif any(w in message for w in ["fired", "job", "salary", "employer", "worker"]):
        return "Labor Law"
    elif any(w in message for w in ["divorce", "marriage", "wife", "husband", "child"]):
        return "Family Law"
    elif any(w in message for w in ["police", "arrest", "crime", "fir", "case"]):
        return "Criminal Law"
    elif any(w in message for w in ["company", "business", "contract", "agreement"]):
        return "Business / Contract Law"
    elif any(w in message for w in ["consumer", "product", "refund", "cheated"]):
        return "Consumer Protection Law"
    else:
        return "General Legal Query"
