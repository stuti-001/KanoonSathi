from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('lawyer-dashboard/', views.lawyer_dashboard_page, name='lawyer_dashboard'),
    path('consult/', views.consult_page, name='consult'),
    path('lawyers/', views.lawyers, name='lawyers'),
    path('appointments/', views.appointments, name='appointments'),
    path('book/', views.book_appointment, name='book'),
    path('meeting/', views.meeting, name='meeting'),
    path('logout/', views.logout_view, name='logout'),

    path("api/consult", views.consult_ai, name="consult_ai"),
    path("api/auth/google", views.google_oauth, name="google_oauth"),
]
