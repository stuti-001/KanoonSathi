from django.shortcuts import render


def lawyers(request):
    return render(request, 'lawyers.html')
