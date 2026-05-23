import json
import os
from pathlib import Path
from dotenv import load_dotenv
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
import requests
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def home(request):
    return render(request, 'index.html')


@csrf_exempt  # needed because JS fetch doesn't send Django's csrf token
def signup(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')

        if User.objects.filter(username=email).exists():
            return JsonResponse({'error': 'User already exists'}, status=400)

        user = User.objects.create_user(
            username=email, email=email, password=password)
        user.first_name = name

        is_lawyer = (role == 'lawyer')
        if is_lawyer:
            user.is_staff = True

        user.save()

        redirect_url = reverse(
            'lawyer_dashboard') if is_lawyer else reverse('dashboard')

        return JsonResponse({
            'message': 'Registration successful',
            'email': email,
            'is_lawyer': is_lawyer,
            'redirect_url': redirect_url,
        })

    return render(request, 'signup.html', {
        'google_client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    })


@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
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

    return render(request, 'login.html', {
        'google_client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    })


@csrf_exempt
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'message': 'Logged out successfully'})

    return JsonResponse({'error': 'Invalid method'}, status=405)


@csrf_exempt
def google_oauth(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        token = data.get('token')

        if not token:
            return JsonResponse({'error': 'No token provided'}, status=400)

        CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
        if not CLIENT_ID:
            return JsonResponse({'error': 'Google OAuth not configured'}, status=500)

        idinfo = id_token.verify_oauth2_token(
            token, google_requests.Request(), CLIENT_ID
        )

        email = idinfo.get('email')
        name = idinfo.get('name', '')
        picture = idinfo.get('picture', '')

        if not email:
            return JsonResponse({'error': 'Email not provided'}, status=400)

        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                'email': email,
                'first_name': name.split()[0] if name else 'User',
                'last_name': name.split()[1] if len(name.split()) > 1 else '',
            },
        )

        login(request, user)

        return JsonResponse({
            'message': 'Login successful',
            'email': email,
            'name': name,
            'picture': picture,
            'is_new_user': created,
        })

    except ValueError:
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
