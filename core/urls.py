"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from hall_booking.admin import admin_site
from hall_booking import views

urlpatterns = [
    # مسارات الإحصائيات في الإدارة - يجب أن تكون قبل admin/
    path('admin/statistics/', views.admin_statistics_view, name='admin_statistics'),
    path('admin/statistics/api/bookings-chart/', views.admin_bookings_chart_api, name='admin_bookings_chart_api'),
    path('admin/statistics/api/revenue-chart/', views.admin_revenue_chart_api, name='admin_revenue_chart_api'),
    path('admin/statistics/api/halls-chart/', views.admin_halls_chart_api, name='admin_halls_chart_api'),
    
    path('admin/', admin.site.urls),  # لوحة الإدارة الافتراضية
    path('admin-site/', admin_site.urls),  # لوحة الإدارة المخصصة إذا أردت الاحتفاظ بها
    
    path('', include('hall_booking.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
