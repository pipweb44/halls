from django.urls import path
from . import views

app_name = 'hall_booking'

urlpatterns = [
    path('', views.home, name='home'),
    path('', views.home, name='index'),  # Alias for admin theme compatibility
    path('halls/', views.halls_list, name='halls_list'),
    path('hall/<int:hall_id>/', views.hall_detail, name='hall_detail'),
    path('hall/<int:hall_id>/book/', views.booking_form, name='booking_form'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('api/check-availability/', views.check_availability, name='check_availability'),
    path('api/get-cities/', views.get_cities_by_governorate, name='get_cities_by_governorate'),
    

    # مسارات مديري القاعات
    path('hall-manager/', views.hall_manager_dashboard, name='hall_manager_dashboard'),
    path('hall-manager/bookings/', views.hall_manager_bookings, name='hall_manager_bookings'),
    path('hall-manager/bookings/<int:booking_id>/', views.hall_manager_booking_detail, name='hall_manager_booking_detail'),
    path('hall-manager/schedule/', views.hall_manager_schedule, name='hall_manager_schedule'),

    # مسارات الحجز الجديد بـ 6 خطوات
    path('booking/<int:hall_id>/step1/', views.booking_step1_date, name='booking_step1_date'),
    path('booking/<int:hall_id>/step2/', views.booking_step2_time, name='booking_step2_time'),
    path('booking/<int:hall_id>/step3/', views.booking_step3_services, name='booking_step3_services'),
    path('booking/<int:hall_id>/step4/', views.booking_step4_meals, name='booking_step4_meals'),
    path('booking/<int:hall_id>/step5/', views.booking_step5_info, name='booking_step5_info'),
    path('booking/<int:hall_id>/step6/', views.booking_step6_review, name='booking_step6_review'),
    path('booking/<int:hall_id>/confirm/', views.confirm_booking, name='confirm_booking'),
    path('booking/success/<uuid:booking_id>/', views.booking_success, name='booking_success'),
    
    # مسارات إدارة القاعات
    path('manager/dashboard/', views.hall_manager_dashboard, name='hall_manager_dashboard'),
    path('manager/hall/<int:hall_id>/', views.hall_management, name='hall_management'),
    path('manager/hall/<int:hall_id>/schedule/', views.hall_schedule_management, name='hall_schedule_management'),
    path('manager/hall/<int:hall_id>/block-time/', views.block_time_slot, name='block_time_slot'),
    path('manager/hall/<int:hall_id>/reports/', views.hall_reports, name='hall_reports'),
    
    # مسارات إدارة الخدمات والوجبات والصور
    path('manager/hall/<int:hall_id>/service/', views.manage_hall_service, name='manage_hall_service'),
    path('manager/hall/<int:hall_id>/meal/', views.manage_hall_meal, name='manage_hall_meal'),
    path('manager/hall/<int:hall_id>/image/', views.manage_hall_image, name='manage_hall_image'),
    path('manager/hall/<int:hall_id>/booking/<int:booking_id>/status/', views.manage_booking_status, name='manage_booking_status'),
    path('booking/<int:booking_id>/details/', views.booking_details_modal, name='booking_details_modal'),

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
    
    # مسارات البروفيل الشخصي
    path('my-profile/', views.user_profile, name='user_profile'),
    path('my-bookings/', views.user_bookings, name='user_bookings'),
    path('my-bookings/<uuid:booking_id>/', views.booking_detail_user, name='booking_detail_user'),
    path('my-bookings/<uuid:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),

    # مسارات الإشعارات
    path('notifications/', views.user_notifications, name='user_notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/unread-count/', views.get_unread_notifications_count, name='unread_notifications_count'),

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