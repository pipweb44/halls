from django.urls import path
from . import views

app_name = 'hall_booking'

urlpatterns = [
    path('', views.home, name='home'),
    path('halls/', views.halls_list, name='halls_list'),
    path('hall/<int:hall_id>/', views.hall_detail, name='hall_detail'),
    path('hall/<int:hall_id>/book/', views.booking_form, name='booking_form'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/check-availability/', views.check_availability, name='check_availability'),
    
    # مسارات الإدارة - بعد dashboard
    path('dashboard/halls/', views.admin_halls_list, name='admin_halls_list'),
    path('dashboard/halls/create/', views.admin_hall_create, name='admin_hall_create'),
    path('dashboard/halls/<int:hall_id>/edit/', views.admin_hall_edit, name='admin_hall_edit'),
    path('dashboard/halls/<int:hall_id>/delete/', views.admin_hall_delete, name='admin_hall_delete'),
    
    path('dashboard/bookings/', views.admin_bookings_list, name='admin_bookings_list'),
    path('dashboard/bookings/<int:booking_id>/', views.admin_booking_detail, name='admin_booking_detail'),
    path('dashboard/bookings/<int:booking_id>/delete/', views.admin_booking_delete, name='admin_booking_delete'),
    
    path('dashboard/contacts/', views.admin_contacts_list, name='admin_contacts_list'),
    path('dashboard/contacts/<int:contact_id>/', views.admin_contact_detail, name='admin_contact_detail'),
    path('dashboard/contacts/<int:contact_id>/delete/', views.admin_contact_delete, name='admin_contact_delete'),
    
    path('dashboard/reports/', views.admin_reports, name='admin_reports'),
    
    path('dashboard/users/', views.admin_users_list, name='admin_users_list'),
    path('dashboard/users/create/', views.admin_user_create, name='admin_user_create'),
    path('dashboard/users/<int:user_id>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('dashboard/users/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),
    path('dashboard/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    
    # مسارات نظام المصادقة متعدد الخطوات
    path('auth/', views.auth_welcome, name='auth_welcome'),
    
    # مسارات تسجيل الدخول
    path('auth/login/step1/', views.auth_login_step1, name='auth_login_step1'),
    path('auth/login/step2/', views.auth_login_step2, name='auth_login_step2'),
    
    # مسارات تسجيل الحساب الجديد
    path('auth/register/step1/', views.auth_register_step1, name='auth_register_step1'),
    path('auth/register/step2/', views.auth_register_step2, name='auth_register_step2'),
    path('auth/register/step3/', views.auth_register_step3, name='auth_register_step3'),
    
    # مسارات أخرى
    path('auth/forgot-password/', views.auth_forgot_password, name='auth_forgot_password'),
    path('auth/logout/', views.auth_logout, name='auth_logout'),
    path('auth/profile/', views.auth_profile, name='auth_profile'),
    path('auth/change-password/', views.auth_change_password, name='auth_change_password'),
    
    # روابط اختصار لسهولة الوصول
    path('login/', views.auth_login_step1, name='login'),
    path('register/', views.auth_register_step1, name='register'),
    path('signup/', views.auth_register_step1, name='signup'),
    path('signin/', views.auth_login_step1, name='signin'),
    path('forgot-password/', views.auth_forgot_password, name='forgot_password'),
    path('profile/', views.auth_profile, name='profile'),
    path('change-password/', views.auth_change_password, name='change_password'),
    path('logout/', views.auth_logout, name='logout'),
] 