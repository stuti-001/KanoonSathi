import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .db_storage import add_appointment, get_all_lawyers, get_appointments_by_email


def appointments(request):
    return render(request, 'appointments.html')


def book_appointment(request):
    return render(request, 'book.html')


def meeting(request):
    return render(request, 'meeting.html')


@csrf_exempt
def api_appointments(request):
    if request.method == 'GET':
        email = None
        if request.user.is_authenticated:
            email = request.user.username
        else:
            email = request.GET.get('email', '').strip().lower()

        if not email:
            return JsonResponse({'error': 'Email is required to fetch appointments.'}, status=401)

        appointments = get_appointments_by_email(email)
        return JsonResponse(appointments, safe=False)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON.'}, status=400)

        required_fields = ['userName', 'email',
                           'phone', 'lawyerId', 'date', 'time']
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return JsonResponse({'error': f'Missing fields: {", ".join(missing)}'}, status=400)

        lawyer_id = data.get('lawyerId')
        lawyers = get_all_lawyers()
        lawyer = next((l for l in lawyers if str(
            l.get('id')) == str(lawyer_id)), None)
        if not lawyer:
            return JsonResponse({'error': 'Selected lawyer not found.'}, status=400)

        appointment = add_appointment({
            'userName': data['userName'],
            'email': data['email'].strip().lower(),
            'phone': data['phone'],
            'lawyerId': lawyer.get('id'),
            'lawyerName': lawyer.get('name'),
            'lawyerArea': lawyer.get('legal_area') or lawyer.get('specialization') or '',
            'district': lawyer.get('district', ''),
            'date': data['date'],
            'time': data['time'],
            'mode': data.get('mode', 'Online'),
            'issueSummary': data.get('issueSummary', ''),
            'chatSummary': data.get('chatSummary', ''),
        })
        return JsonResponse(appointment, status=201)

    return JsonResponse({'error': 'Method not allowed.'}, status=405)


def api_lawyers(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)
    return JsonResponse(get_all_lawyers(), safe=False)
