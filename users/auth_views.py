import json
import os
from pathlib import Path
from dotenv import load_dotenv
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import login, logout

try:
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token
except ImportError:
    google_requests = None
    id_token = None

from .supabase_client import get_supabase_client
from .db_storage import add_user, add_lawyer, set_current_user, clear_current_user

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def home(request):
    return render(request, 'index.html')


def _load_json(data):
    try:
        return json.loads(data)
    except Exception:
        return {}


def _get_user_role(user, requested_role=None):
    if requested_role and requested_role == 'lawyer':
        return 'lawyer' if user.is_staff else 'user'
    return 'lawyer' if user.is_staff else 'user'


def _create_or_update_local_user(email, name, password, role):
    user, created = User.objects.get_or_create(
        username=email,
        defaults={'email': email, 'first_name': name or ''},
    )
    if password:
        user.set_password(password)
    user.first_name = name or user.first_name
    user.is_staff = (role == 'lawyer')
    user.save()
    return user


@csrf_exempt  # needed because JS fetch doesn't send Django's csrf token
def signup(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            role = data.get('role', 'user')
            phone = data.get('phone', '').strip()
            license_number = data.get('licenseNumber', '').strip()
            district = data.get('district', '').strip()
            specialization = data.get('specialization', '').strip()
            legal_area = data.get('legalArea', '').strip()
            experience_years = data.get('experienceYears', '').strip()
            availability = data.get('availability', '').strip()
            languages = data.get('languages', '').strip()
            bio = data.get('bio', '').strip()
            consultation_fee = data.get('consultationFee', '').strip()
            profile_picture = data.get('profilePictureName', '')
            supporting_documents = data.get('supportingDocuments', [])

            if not name or not email or not password:
                return JsonResponse({'error': 'Name, email, and password are required.'}, status=400)

            if User.objects.filter(username=email).exists():
                return JsonResponse({'error': 'User already exists.'}, status=400)

            try:
                supabase = get_supabase_client()
            except RuntimeError:
                # Supabase not configured — fall back to local-only registration
                supabase = None

            if supabase is None:
                auth_response = None
            else:
                auth_response = supabase.auth.sign_up({
                    'email': email,
                    'password': password,
                })

            # Normalize error object similar to login
            error_obj = None
            if getattr(auth_response, 'error', None):
                error_obj = auth_response.error
            elif isinstance(auth_response, dict):
                error_obj = auth_response.get('error')

            if error_obj:
                raw_message = None
                if hasattr(error_obj, 'message'):
                    raw_message = error_obj.message
                elif isinstance(error_obj, dict):
                    raw_message = error_obj.get('message')
                else:
                    raw_message = str(error_obj)

                if raw_message:
                    raw_message = raw_message.strip().lower()

                if raw_message and 'password' in raw_message:
                    friendly_message = 'Password does not meet requirements.'
                elif raw_message and ('email' in raw_message or 'already' in raw_message or 'user' in raw_message):
                    friendly_message = 'Email is invalid or already registered.'
                else:
                    friendly_message = raw_message.title() if raw_message else 'Registration failed.'

                return JsonResponse({'error': friendly_message}, status=400)

            token = None
            if getattr(auth_response, 'session', None) is not None:
                token = getattr(auth_response.session, 'access_token', None)
                if token is None and hasattr(auth_response.session, 'get'):
                    token = auth_response.session.get('access_token')

            # extract supabase user id if available
            supabase_user_id = None
            try:
                if auth_response:
                    if hasattr(auth_response, 'user') and auth_response.user:
                        u = auth_response.user
                        supabase_user_id = getattr(u, 'id', None) or (isinstance(u, dict) and u.get('id'))
                    elif isinstance(auth_response, dict):
                        data = auth_response.get('data') or {}
                        u = data.get('user') or auth_response.get('user')
                        if isinstance(u, dict):
                            supabase_user_id = u.get('id')
            except Exception:
                supabase_user_id = None

            local_user = _create_or_update_local_user(email, name, password, role)
            login(request, local_user)

            add_user({'name': name, 'email': email, 'role': role, 'phone': phone})

            if role == 'lawyer':
                add_lawyer({
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'district': district,
                    'license_number': license_number,
                    'specialization': specialization,
                    'legal_area': legal_area,
                    'experience_years': experience_years,
                    'availability': availability,
                    'languages': languages,
                    'bio': bio,
                    'fee_npr': consultation_fee,
                    'profile_picture': profile_picture,
                    'supporting_documents': supporting_documents,
                    'status': 'pending',
                })

            set_current_user({
                'name': name,
                'email': email,
                'role': role,
                'token': token,
            })

            redirect_url = reverse('lawyer_dashboard') if role == 'lawyer' else reverse('dashboard')

            # log supabase response for debugging
            try:
                with open('/tmp/supabase_response.log', 'a') as f:
                    f.write(f"SIGNUP: supabase_present={bool(supabase)} user_id={supabase_user_id}\n")
            except Exception:
                pass

            return JsonResponse({
                'message': 'Registration successful',
                'email': email,
                'name': name,
                'role': role,
                'token': token,
                'redirect_url': redirect_url,
                'synced_to_supabase': bool(supabase and auth_response),
                'supabase_user_id': supabase_user_id,
            })
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            try:
                with open('/tmp/signup_error.log', 'w') as f:
                    f.write(tb)
            except Exception:
                pass
            print('Signup error:', e)
            return JsonResponse({'error': 'Registration failed. Please check your input and try again.'}, status=500)

    return render(request, 'signup.html', {
        'google_client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    })


@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        requested_role = data.get('role', 'user')

        if not email or not password:
            return JsonResponse({'error': 'Email and password are required.'}, status=400)

        try:
            supabase = get_supabase_client()
        except RuntimeError:
            supabase = None

        if supabase is None:
            # Fallback to local Django auth
            user = User.objects.filter(username=email).first()
            if user is None:
                return JsonResponse({'error': 'Incorrect email.'}, status=401)
            if not user.check_password(password):
                return JsonResponse({'error': 'Incorrect password.'}, status=401)
            # local auth successful — continue to login below
            auth_response = None
        else:
            auth_response = supabase.auth.sign_in_with_password({
                'email': email,
                'password': password,
            })

        error_obj = None
        if getattr(auth_response, 'error', None):
            error_obj = auth_response.error
        elif isinstance(auth_response, dict):
            error_obj = auth_response.get('error')

        if error_obj:
            raw_message = None
            if hasattr(error_obj, 'message'):
                raw_message = error_obj.message
            elif isinstance(error_obj, dict):
                raw_message = error_obj.get('message')
            else:
                raw_message = str(error_obj)

            if raw_message:
                raw_message = raw_message.strip().lower()

            if raw_message and 'password' in raw_message:
                friendly_message = 'Incorrect password.'
            elif raw_message and ('email' in raw_message or 'user' in raw_message or 'not found' in raw_message):
                friendly_message = 'Incorrect email.'
            else:
                friendly_message = raw_message.title() if raw_message else 'Invalid email or password.'

            return JsonResponse({'error': friendly_message}, status=401)

        session = getattr(auth_response, 'session', None) if auth_response is not None else None
        token = None
        if session is not None:
            token = getattr(session, 'access_token', None)
            if token is None and hasattr(session, 'get'):
                token = session.get('access_token')

        # extract supabase user id from login response
        supabase_user_id = None
        try:
            if auth_response:
                if hasattr(auth_response, 'user') and auth_response.user:
                    u = auth_response.user
                    supabase_user_id = getattr(u, 'id', None) or (isinstance(u, dict) and u.get('id'))
                elif isinstance(auth_response, dict):
                    data = auth_response.get('data') or {}
                    u = data.get('user') or auth_response.get('user')
                    if isinstance(u, dict):
                        supabase_user_id = u.get('id')
        except Exception:
            supabase_user_id = None

        user = User.objects.filter(username=email).first()
        if user is None:
            user = _create_or_update_local_user(email, email.split('@')[0], password, requested_role)

        role = 'lawyer' if user.is_staff else 'user'
        if requested_role and role != requested_role:
            return JsonResponse({'error': f'This account is registered as "{role}". Please login with the correct role.'}, status=403)

        login(request, user)
        set_current_user({
            'name': user.first_name,
            'email': email,
            'role': role,
            'token': token,
        })

        redirect_url = reverse('lawyer_dashboard') if role == 'lawyer' else reverse('dashboard')
        try:
            with open('/tmp/supabase_response.log', 'a') as f:
                f.write(f"LOGIN: supabase_present={bool(supabase)} user_id={supabase_user_id}\n")
        except Exception:
            pass

        return JsonResponse({
            'message': 'Login successful',
            'email': email,
            'name': user.first_name,
            'role': role,
            'token': token,
            'redirect_url': redirect_url,
            'synced_to_supabase': bool(supabase and auth_response),
            'supabase_user_id': supabase_user_id,
        })

    return render(request, 'login.html', {
        'google_client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    })


@csrf_exempt
def logout_view(request):
    if request.method == 'POST':
        clear_current_user()
        logout(request)
        return JsonResponse({'message': 'Logged out successfully'})

    return JsonResponse({'error': 'Invalid method'}, status=405)


@csrf_exempt
def google_oauth(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if google_requests is None or id_token is None:
        return JsonResponse({'error': 'Google OAuth support is not available on this server.'}, status=500)

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
        set_current_user({
            'name': user.first_name,
            'email': email,
            'role': 'lawyer' if user.is_staff else 'user',
            'token': token,
        })

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
