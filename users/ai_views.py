from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


def consult_page(request):
    return render(request, 'consult.html')


@csrf_exempt
def consult_ai(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    # Placeholder endpoint for chatbot integration.
    # Actual AI implementation should be added by the teammate responsible for the chatbot.
    return JsonResponse({
        'error': 'AI chatbot integration not implemented yet',
        'status': 'pending',
    }, status=501)
