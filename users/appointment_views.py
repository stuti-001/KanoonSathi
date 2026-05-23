from django.shortcuts import render


def appointments(request):
    return render(request, 'appointments.html')


def book_appointment(request):
    return render(request, 'book.html')


def meeting(request):
    return render(request, 'meeting.html')
