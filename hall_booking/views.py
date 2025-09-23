from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from datetime import datetime, timedelta
from .models import (Hall, Booking, Category, Governorate, City, HallService, 
                    HallMeal, BookingService, BookingMeal, HallManager, HallImage, 
                    Contact, Notification)
from .forms import BookingForm, ContactForm, HallForm
from django.contrib.auth.models import User
import calendar
import json
from django.core.paginator import Paginator
from django.contrib.auth import update_session_auth_hash, authenticate, login, logout
from collections import defaultdict

def is_admin(user):
    return user.is_staff

def is_hall_manager(user):
    """تحقق من كون المستخدم مدير قاعة"""
    return HallManager.objects.filter(user=user, is_active=True).exists()

def get_user_managed_hall(user):
    """الحصول على القاعة التي يديرها المستخدم"""
    try:
        manager = HallManager.objects.get(user=user, is_active=True)
        return manager.hall
    except HallManager.DoesNotExist:
        return None

def home(request):
    """الصفحة الرئيسية"""
    categories = Category.objects.all()
    featured_halls = Hall.objects.filter(status='available').prefetch_related('images')[:6]
    recent_bookings = Booking.objects.filter(status='approved').order_by('-created_at')[:3]
    
    context = {
        'categories': categories,
        'featured_halls': featured_halls,
        'recent_bookings': recent_bookings,
    }
    return render(request, 'hall_booking/home.html', context)

def halls_list(request):
    """قائمة القاعات"""
    category_id = request.GET.get('category')
    governorate_id = request.GET.get('governorate')
    city_id = request.GET.get('city')
    search_query = request.GET.get('search')
    capacity = request.GET.get('capacity')

    halls = Hall.objects.filter(status='available').select_related('category', 'governorate', 'city').prefetch_related('images')

    if category_id:
        halls = halls.filter(category_id=category_id)

    if governorate_id:
        halls = halls.filter(governorate_id=governorate_id)
        # إذا تم اختيار مدينة، تأكد أنها تنتمي للمحافظة المختارة
        if city_id:
            halls = halls.filter(city_id=city_id, city__governorate_id=governorate_id)
    elif city_id:
        # إذا تم اختيار مدينة بدون محافظة، تجاهل المدينة
        city_id = None

    if capacity:
        if capacity == '1-50':
            halls = halls.filter(capacity__gte=1, capacity__lte=50)
        elif capacity == '51-100':
            halls = halls.filter(capacity__gte=51, capacity__lte=100)
        elif capacity == '101-200':
            halls = halls.filter(capacity__gte=101, capacity__lte=200)
        elif capacity == '201+':
            halls = halls.filter(capacity__gte=201)

    if search_query:
        halls = halls.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(governorate__name__icontains=search_query) |
            Q(city__name__icontains=search_query) |
            Q(address__icontains=search_query)
        )

    categories = Category.objects.all()
    governorates = Governorate.objects.all().order_by('name')

    # المدن تظهر فقط إذا تم اختيار محافظة
    cities = []
    if governorate_id:
        cities = City.objects.filter(governorate_id=governorate_id).order_by('name')

    context = {
        'halls': halls,
        'categories': categories,
        'governorates': governorates,
        'cities': cities,
        'selected_category': category_id,
        'selected_governorate': governorate_id,
        'selected_city': city_id,
        'selected_capacity': capacity,
        'search_query': search_query,
    }
    return render(request, 'hall_booking/halls_list.html', context)

def get_cities_by_governorate(request):
    """الحصول على المدن حسب المحافظة (AJAX)"""
    governorate_id = request.GET.get('governorate_id')
    cities = []

    if governorate_id:
        cities_queryset = City.objects.filter(governorate_id=governorate_id).order_by('name')
        cities = [{'id': city.id, 'name': city.name} for city in cities_queryset]

    return JsonResponse({'cities': cities})

def hall_detail(request, hall_id):
    """تفاصيل القاعة"""
    hall = get_object_or_404(Hall, id=hall_id, status='available')

    # الحصول على الخدمات والوجبات والصور المتاحة للقاعة
    hall_services = hall.hall_services.filter(is_available=True).order_by('name')
    hall_meals = hall.hall_meals.filter(is_available=True).order_by('meal_type', 'name')
    hall_images = hall.images.all().order_by('order', '-uploaded_at')

    # القاعات المشابهة (نفس الفئة أو نفس المحافظة)
    similar_halls = Hall.objects.filter(
        status='available'
    ).exclude(
        id=hall.id
    ).filter(
        Q(category=hall.category) | Q(governorate=hall.governorate)
    ).select_related('category', 'governorate', 'city').prefetch_related('images')[:6]

    # التحقق من التواريخ المتاحة
    if request.method == 'POST':
        date = request.POST.get('date')
        if date:
            selected_date = datetime.strptime(date, '%Y-%m-%d').date()
            # الحصول على الحجوزات في هذا التاريخ
            bookings = Booking.objects.filter(
                hall=hall,
                start_datetime__date=selected_date,
                status__in=['approved', 'pending']
            )
            context = {
                'hall': hall,
                'hall_services': hall_services,
                'hall_meals': hall_meals,
                'hall_images': hall_images,
                'selected_date': selected_date,
                'bookings': bookings,
                'similar_halls': similar_halls,
            }
        else:
            context = {
                'hall': hall,
                'hall_services': hall_services,
                'hall_meals': hall_meals,
                'hall_images': hall_images,
                'similar_halls': similar_halls,
            }
    else:
        context = {
            'hall': hall,
            'hall_services': hall_services,
            'hall_meals': hall_meals,
            'hall_images': hall_images,
            'similar_halls': similar_halls,
        }

    return render(request, 'hall_booking/hall_detail.html', context)

def booking_form(request, hall_id):
    """نموذج الحجز"""
    hall = get_object_or_404(Hall, id=hall_id)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.hall = hall
            # اربط الحجز بالمستخدم المسجل دوماً لضمان ظهوره في الملف الشخصي
            if request.user.is_authenticated:
                booking.user = request.user
                # إذا كان البريد في الحجز فارغاً ولدى المستخدم بريد، استخدم بريد المستخدم
                if not booking.customer_email and request.user.email:
                    booking.customer_email = request.user.email
                # إذا لم يملأ الاسم، استخدم اسم المستخدم/الاسم الكامل
                if not booking.customer_name:
                    full_name = (request.user.get_full_name() or '').strip()
                    booking.customer_name = full_name or request.user.username
            booking.total_price = booking.calculate_total_price()
            booking.save()
            
            messages.success(request, 'تم إرسال طلب الحجز بنجاح! سنتواصل معك قريباً.')
            return redirect('hall_booking:hall_detail', hall_id=hall_id)
    else:
        # تهيئة الحقول باسم وبريد المستخدم لتجربة أفضل
        initial = {}
        if request.user.is_authenticated:
            if request.user.email:
                initial['customer_email'] = request.user.email
            full_name = (request.user.get_full_name() or '').strip()
            if full_name:
                initial['customer_name'] = full_name
        form = BookingForm(initial=initial)
    
    context = {
        'form': form,
        'hall': hall,
    }
    return render(request, 'hall_booking/booking_form.html', context)

def contact(request):
    """صفحة التواصل"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إرسال رسالتك بنجاح! سنتواصل معك قريباً.')
            return redirect('hall_booking:contact')
    else:
        form = ContactForm()
    
    context = {
        'form': form,
    }
    return render(request, 'hall_booking/contact.html', context)

def about(request):
    """صفحة من نحن"""
    return render(request, 'hall_booking/about.html')

@csrf_exempt
def check_availability(request):
    """التحقق من توفر القاعة"""
    if request.method == 'POST':
        data = json.loads(request.body)
        hall_id = data.get('hall_id')
        start_datetime = data.get('start_datetime')
        end_datetime = data.get('end_datetime')
        
        try:
            hall = Hall.objects.get(id=hall_id)
            start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
            
            # التحقق من وجود حجوزات متداخلة
            conflicting_bookings = Booking.objects.filter(
                hall=hall,
                status__in=['approved', 'pending'],
                start_datetime__lt=end_dt,
                end_datetime__gt=start_dt
            )
            
            is_available = not conflicting_bookings.exists()
            
            return JsonResponse({
                'available': is_available,
                'message': 'القاعة متاحة' if is_available else 'القاعة غير متاحة في هذا الوقت'
            })
        except Exception as e:
            return JsonResponse({
                'available': False,
                'message': 'حدث خطأ في التحقق من التوفر'
            })
    
    return JsonResponse({'error': 'طريقة طلب غير صحيحة'})

def admin_bookings_calendar(request):
    """Return JSON data for calendar events"""
    if not request.user.is_staff:
        return JsonResponse([], safe=False)
    
    try:
        start_date = request.GET.get('start')
        end_date = request.GET.get('end')
        
        # Convert string dates to datetime objects
        start = timezone.datetime.fromisoformat(start_date) if start_date else None
        end = timezone.datetime.fromisoformat(end_date) if end_date else None
        
        # Build the query
        query = Q()
        if start:
            query &= Q(start_datetime__gte=start)
        if end:
            query &= Q(end_datetime__lte=end)
            
        # Get the bookings
        bookings = Booking.objects.filter(query).select_related('hall', 'user')
        
        # Format events for FullCalendar
        events = []
        for booking in bookings:
            event = {
                'id': booking.id,
                'title': f"{booking.hall.name} - {booking.customer_name or 'Guest'}",
                'start': booking.start_datetime.isoformat(),
                'end': booking.end_datetime.isoformat(),
                'url': reverse('hall_booking:admin_booking_detail', args=[booking.id]),
                'color': '#1cc88a' if booking.status == 'confirmed' else 
                        '#f6c23e' if booking.status == 'pending' else '#e74a3b',
                'textColor': '#fff',
                'borderColor': '#fff',
                'extendedProps': {
                    'status': booking.status,
                    'customer': booking.customer_name,
                    'hall': booking.hall.name
                }
            }
            events.append(event)
            
        return JsonResponse(events, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)



# إدارة القاعات
@login_required
@user_passes_test(is_admin)
def admin_halls_list(request):
    """قائمة إدارة القاعات"""
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    
    halls = Hall.objects.all()
    
    if search_query:
        halls = halls.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if category_filter:
        halls = halls.filter(category_id=category_filter)
    
    if status_filter:
        halls = halls.filter(status=status_filter)
    
    categories = Category.objects.all()
    
    context = {
        'halls': halls,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
    }
    return render(request, 'admin_dashbourd/halls_list.html', context)

@login_required
@user_passes_test(is_admin)
def admin_hall_create(request):
    """إنشاء قاعة جديدة"""
    if request.method == 'POST':
        form = HallForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إنشاء القاعة بنجاح!')
            return redirect('hall_booking:admin_halls_list')
    else:
        form = HallForm()
    
    context = {
        'form': form,
        'title': 'إنشاء قاعة جديدة'
    }
    
    return render(request, 'admin_dashbourd/hall_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_hall_edit(request, hall_id):
    """تعديل قاعة"""
    hall = get_object_or_404(Hall, id=hall_id)
    
    if request.method == 'POST':
        form = HallForm(request.POST, request.FILES, instance=hall)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث القاعة بنجاح!')
            return redirect('hall_booking:admin_halls_list')
    else:
        form = HallForm(instance=hall)
    
    context = {
        'form': form,
        'hall': hall,
        'title': 'تعديل القاعة'
    }
    return render(request, 'admin_dashbourd/hall_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_add_booking(request):
    """إضافة حجز جديد"""
    if not request.user.is_staff:
        return redirect('hall_booking:home')
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.created_by = request.user
            booking.save()
            messages.success(request, 'تم إضافة الحجز بنجاح')
            return redirect('hall_booking:admin_booking_detail', booking_id=booking.id)
    else:
        form = BookingForm()
    
    return render(request, 'admin_dashbourd/booking_form.html', {
        'form': form,
        'title': 'إضافة حجز جديد'
    })

@login_required
@user_passes_test(is_admin)
def admin_booking_detail(request, booking_id):
    """تفاصيل الحجز"""
    if not request.user.is_staff:
        return redirect('hall_booking:home')
        
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث حالة الحجز بنجاح')
            return redirect('hall_booking:admin_booking_detail', booking_id=booking.id)
    else:
        form = BookingForm(instance=booking)
    
    return render(request, 'admin_dashbourd/booking_detail.html', {
        'booking': booking,
        'form': form
    })

@login_required
@user_passes_test(is_admin)
def admin_hall_delete(request, hall_id):
    """حذف قاعة"""
    hall = get_object_or_404(Hall, id=hall_id)
    
    if request.method == 'POST':
        hall.delete()
        messages.success(request, 'تم حذف القاعة بنجاح!')
        return redirect('hall_booking:admin_halls_list')
    
    context = {
        'hall': hall
    }
    return render(request, 'admin_dashbourd/hall_confirm_delete.html', context)

# إدارة الحجوزات
@login_required
@user_passes_test(is_admin)
def admin_bookings_list(request):
    """صفحة إدارة الحجوزات"""
    bookings = Booking.objects.all().order_by('-created_at')
    
    # البحث والفلترة
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    hall_filter = request.GET.get('hall', '')
    
    if search_query:
        bookings = bookings.filter(
            Q(event_title__icontains=search_query) |
            Q(customer_name__icontains=search_query) |
            Q(customer_phone__icontains=search_query)
        )
    
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    if hall_filter:
        bookings = bookings.filter(hall_id=hall_filter)
    
    halls = Hall.objects.all()
    
    context = {
        'bookings': bookings,
        'halls': halls,
        'search_query': search_query,
        'status_filter': status_filter,
        'hall_filter': hall_filter,
    }
    # إضافة إحصائيات للصفحة
    pending_count = bookings.filter(status='pending').count()
    approved_count = bookings.filter(status='approved').count()
    completed_count = bookings.filter(status='completed').count()

    context.update({
        'pending_count': pending_count,
        'approved_count': approved_count,
        'completed_count': completed_count,
    })

    return render(request, 'admin_dashbourd/bookings_list.html', context)

@login_required
@user_passes_test(is_admin)
def admin_booking_detail(request, booking_id):
    """تفاصيل الحجز"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['pending', 'approved', 'completed', 'cancelled']:
            booking.status = new_status
            booking.save()
            messages.success(request, 'تم تحديث حالة الحجز بنجاح')
            return redirect('hall_booking:admin_bookings_list')
    
    context = {
        'booking': booking,
    }
    return render(request, 'hall_booking/admin/booking_detail.html', context)

@login_required
@user_passes_test(is_admin)
def admin_booking_delete(request, booking_id):
    """حذف الحجز"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.method == 'POST':
        booking.delete()
        messages.success(request, 'تم حذف الحجز بنجاح')
        return redirect('hall_booking:admin_bookings_list')
    
    context = {
        'booking': booking,
    }
    return render(request, 'hall_booking/admin/booking_confirm_delete.html', context)

# إدارة رسائل التواصل
@login_required
@user_passes_test(is_admin)
def admin_contacts_list(request):
    """صفحة إدارة رسائل التواصل"""
    contacts = Contact.objects.all().order_by('-created_at')
    
    # البحث
    search_query = request.GET.get('search', '')
    if search_query:
        contacts = contacts.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(message__icontains=search_query)
        )
    
    context = {
        'contacts': contacts,
        'search_query': search_query,
    }
    return render(request, 'admin_dashbourd/contacts_list.html', context)

@login_required
@user_passes_test(is_admin)
def admin_contact_detail(request, contact_id):
    """تفاصيل الرسالة"""
    contact = get_object_or_404(Contact, id=contact_id)
    
    if request.method == 'POST':
        contact.is_read = True
        contact.save()
        messages.success(request, 'تم تحديث حالة الرسالة')
        return redirect('hall_booking:admin_contacts_list')
    
    context = {
        'contact': contact,
    }
    return render(request, 'hall_booking/admin/contact_detail.html', context)

@login_required
@user_passes_test(is_admin)
def admin_contact_delete(request, contact_id):
    """حذف الرسالة"""
    contact = get_object_or_404(Contact, id=contact_id)
    
    if request.method == 'POST':
        contact.delete()
        messages.success(request, 'تم حذف الرسالة بنجاح')
        return redirect('hall_booking:admin_contacts_list')
    
    context = {
        'contact': contact,
    }
    return render(request, 'hall_booking/admin/contact_confirm_delete.html', context)

# التقارير
@login_required
@user_passes_test(is_admin)
def admin_reports(request):
    """صفحة التقارير والإحصائيات"""
    # إحصائيات عامة
    total_halls = Hall.objects.count()
    total_bookings = Booking.objects.count()
    total_contacts = Contact.objects.count()
    
    # إحصائيات الحجوزات
    pending_bookings = Booking.objects.filter(status='pending').count()
    approved_bookings = Booking.objects.filter(status='approved').count()
    completed_bookings = Booking.objects.filter(status='completed').count()
    cancelled_bookings = Booking.objects.filter(status='cancelled').count()
    
    # إحصائيات القاعات
    available_halls = Hall.objects.filter(status='available').count()
    maintenance_halls = Hall.objects.filter(status='maintenance').count()
    booked_halls = Hall.objects.filter(status='booked').count()
    
    # إحصائيات الرسائل
    unread_contacts = Contact.objects.filter(is_read=False).count()
    read_contacts = Contact.objects.filter(is_read=True).count()
    
    # الحجوزات حسب الشهر
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    monthly_bookings = []
    for i in range(6):
        month = current_month - i
        year = current_year
        if month <= 0:
            month += 12
            year -= 1
        
        count = Booking.objects.filter(
            created_at__year=year,
            created_at__month=month
        ).count()
        
        month_name = {
            1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
            5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
            9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
        }[month]
        
        monthly_bookings.append({
            'month': month_name,
            'count': count
        })
    
    monthly_bookings.reverse()
    
    # القاعات الأكثر حجزاً
    popular_halls = Hall.objects.annotate(
        booking_count=Count('booking')
    ).order_by('-booking_count')[:5]
    
    context = {
        'total_halls': total_halls,
        'total_bookings': total_bookings,
        'total_contacts': total_contacts,
        'pending_bookings': pending_bookings,
        'approved_bookings': approved_bookings,
        'completed_bookings': completed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'available_halls': available_halls,
        'maintenance_halls': maintenance_halls,
        'booked_halls': booked_halls,
        'unread_contacts': unread_contacts,
        'read_contacts': read_contacts,
        'monthly_bookings': monthly_bookings,
        'popular_halls': popular_halls,
    }
    return render(request, 'hall_booking/admin/reports.html', context) 

# Authentication Views
def auth_welcome(request):
    """صفحة الترحيب بنظام المصادقة"""
    return render(request, 'hall_booking/auth/welcome.html')

def auth_login_step1(request):
    """الخطوة الأولى: إدخال البريد الإلكتروني أو اسم المستخدم"""
    if request.method == 'POST':
        login_identifier = request.POST.get('login_identifier')
        if login_identifier:
            request.session['auth_login_identifier'] = login_identifier
            return redirect('hall_booking:auth_login_step2')
        else:
            messages.error(request, 'يرجى إدخال البريد الإلكتروني أو اسم المستخدم')
    return render(request, 'hall_booking/auth/login_step1.html')


def auth_login_step2(request):
    """الخطوة الثانية: إدخال كلمة المرور"""
    login_identifier = request.session.get('auth_login_identifier')
    if not login_identifier:
        return redirect('hall_booking:auth_login_step1')
    if request.method == 'POST':
        password = request.POST.get('password')
        if password:
            # محاولة المصادقة بالبريد الإلكتروني أو اسم المستخدم
            from django.contrib.auth.models import User
            user = None
            # أولاً: جرب كاسم مستخدم
            user_obj = User.objects.filter(username=login_identifier).first()
            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)
            # إذا لم يوجد كاسم مستخدم، جرب كإيميل
            if not user:
                user_obj = User.objects.filter(email=login_identifier).first()
                if user_obj:
                    user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                login(request, user)
                if 'auth_login_identifier' in request.session:
                    del request.session['auth_login_identifier']
                messages.success(request, f'مرحباً {user.get_full_name() or user.username}!')
                # توجيه المسؤولين إلى لوحة الإدارة
                if user.is_staff:
                    return redirect('/admin/')
                else:
                    return redirect('hall_booking:home')
            else:
                messages.error(request, 'اسم المستخدم أو البريد الإلكتروني أو كلمة المرور غير صحيحة')
        else:
            messages.error(request, 'يرجى إدخال كلمة المرور')
    return render(request, 'hall_booking/auth/login_step2.html', {'login_identifier': login_identifier})


def auth_register_step1(request):
    """الخطوة الأولى: إدخال البيانات الأساسية مع اسم مستخدم اختياري"""
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        if first_name and last_name and email:
            request.session['auth_data'] = {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'username': username or ''
            }
            return redirect('hall_booking:auth_register_step2')
        else:
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة')
    return render(request, 'hall_booking/auth/register_step1.html')

def auth_register_step2(request):
    """الخطوة الثانية: إدخال كلمة المرور"""
    auth_data = request.session.get('auth_data')
    if not auth_data:
        return redirect('hall_booking:auth_register_step1')
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 and password2:
            if password1 == password2:
                if len(password1) >= 8:
                    # تحديد اسم المستخدم
                    from django.contrib.auth.models import User
                    username = auth_data.get('username') or auth_data['email']
                    # تحقق من عدم تكرار اسم المستخدم
                    if User.objects.filter(username=username).exists():
                        messages.error(request, 'اسم المستخدم مستخدم بالفعل، يرجى اختيار اسم آخر أو تركه فارغًا')
                        return render(request, 'hall_booking/auth/register_step2.html')
                    # تحقق من عدم تكرار البريد الإلكتروني
                    if User.objects.filter(email=auth_data['email']).exists():
                        messages.error(request, 'البريد الإلكتروني مستخدم بالفعل')
                        return render(request, 'hall_booking/auth/register_step2.html')
                    # إنشاء المستخدم
                    try:
                        user = User.objects.create_user(
                            username=username,
                            email=auth_data['email'],
                            password=password1,
                            first_name=auth_data['first_name'],
                            last_name=auth_data['last_name']
                        )
                        login(request, user)
                        if 'auth_data' in request.session:
                            del request.session['auth_data']
                        messages.success(request, 'تم إنشاء الحساب بنجاح!')
                        # توجيه المسؤولين إلى لوحة الإدارة
                        if user.is_staff:
                            return redirect('/admin/')
                        else:
                            return redirect('hall_booking:home')
                    except Exception as e:
                        messages.error(request, 'حدث خطأ أثناء إنشاء الحساب')
                else:
                    messages.error(request, 'كلمة المرور يجب أن تكون 8 أحرف على الأقل')
            else:
                messages.error(request, 'كلمات المرور غير متطابقة')
        else:
            messages.error(request, 'يرجى إدخال كلمة المرور')
    return render(request, 'hall_booking/auth/register_step2.html')

def auth_register_step3(request):
    """الخطوة الثالثة: تأكيد الحساب"""
    auth_data = request.session.get('auth_data')
    if not auth_data:
        return redirect('hall_booking:auth_register_step1')
    
    if request.method == 'POST':
        # Here you can add email verification logic
        # For now, we'll just redirect to next step
        return redirect('hall_booking:auth_register_step2')
    
    return render(request, 'hall_booking/auth/register_step3.html')

def auth_forgot_password(request):
    """صفحة نسيان كلمة المرور"""
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Here you can add password reset logic
            messages.success(request, 'تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني')
            return redirect('hall_booking:auth_login_step1')
        else:
            messages.error(request, 'يرجى إدخال البريد الإلكتروني')
    
    return render(request, 'hall_booking/auth/forgot_password.html')

def auth_logout(request):
    """تسجيل الخروج"""
    logout(request)
    messages.success(request, 'تم تسجيل الخروج بنجاح')
    return redirect('hall_booking:home')

@login_required
def auth_profile(request):
    """صفحة الملف الشخصي"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        messages.success(request, 'تم تحديث الملف الشخصي بنجاح')
        return redirect('hall_booking:auth_profile')
    
    # جلب طلبات الحجز الخاصة بالمستخدم: أولاً بعلاقة المستخدم، ثم كباك أب عبر البريد
    user_bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    if not user_bookings.exists():
        user_email = request.user.email
        if user_email:
            user_bookings = Booking.objects.filter(customer_email=user_email).order_by('-created_at')
    context = {
        'bookings': user_bookings,
    }
    return render(request, 'hall_booking/auth/profile.html', context)

@login_required
def auth_change_password(request):
    """تغيير كلمة المرور"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if request.user.check_password(current_password):
            if new_password1 == new_password2:
                if len(new_password1) >= 8:
                    request.user.set_password(new_password1)
                    request.user.save()
                    messages.success(request, 'تم تغيير كلمة المرور بنجاح')
                    return redirect('hall_booking:auth_profile')
                else:
                    messages.error(request, 'كلمة المرور الجديدة يجب أن تكون 8 أحرف على الأقل')
            else:
                messages.error(request, 'كلمات المرور الجديدة غير متطابقة')
        else:
            messages.error(request, 'كلمة المرور الحالية غير صحيحة')
    
    return render(request, 'hall_booking/auth/change_password.html') 

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def admin_users_list(request):
    """قائمة إدارة المستخدمين"""
    search_query = request.GET.get('search', '')
    users = User.objects.all().order_by('-date_joined')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    paginator = Paginator(users, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # إحصائيات
    total_users = users.count()
    staff_count = users.filter(is_staff=True).count()
    active_count = users.filter(is_active=True).count()
    inactive_count = users.filter(is_active=False).count()
    context = {
        'users': page_obj,
        'search_query': search_query,
        'total_users': total_users,
        'staff_count': staff_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
    }
    return render(request, 'hall_booking/admin/users_list.html', context) 

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def admin_user_create(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'تم إنشاء المستخدم بنجاح!')
            return redirect('hall_booking:admin_users_list')
    else:
        form = UserCreationForm()
    return render(request, 'hall_booking/admin/user_form.html', {'form': form, 'create': True})

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def admin_user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث بيانات المستخدم بنجاح!')
            return redirect('hall_booking:admin_users_list')
    else:
        form = UserChangeForm(instance=user)
    return render(request, 'hall_booking/admin/user_form.html', {'form': form, 'edit': True, 'user_obj': user})

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def admin_user_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'تم حذف المستخدم بنجاح!')
        return redirect('hall_booking:admin_users_list')
    return render(request, 'hall_booking/admin/user_confirm_delete.html', {'user_obj': user}) 

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def admin_user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    # Fetch bookings linked to this user. Fallback to email-based match for legacy records.
    user_bookings = Booking.objects.filter(user=user).order_by('-created_at')
    if not user_bookings.exists() and user.email:
        user_bookings = Booking.objects.filter(customer_email=user.email).order_by('-created_at')
    return render(
        request,
        'hall_booking/admin/user_detail.html',
        {
            'user_obj': user,
            'bookings': user_bookings,
        },
    )

# ==================== Hall Manager Views ====================

@login_required
@user_passes_test(is_hall_manager)
def hall_manager_dashboard(request):
    """لوحة تحكم مدير القاعة"""
    managed_hall = get_user_managed_hall(request.user)
    if not managed_hall:
        messages.error(request, 'لا يمكنك الوصول لهذه الصفحة')
        return redirect('hall_booking:home')

    # إحصائيات القاعة
    total_bookings = Booking.objects.filter(hall=managed_hall).count()
    pending_bookings = Booking.objects.filter(hall=managed_hall, status='pending').count()
    approved_bookings = Booking.objects.filter(hall=managed_hall, status='approved').count()
    completed_bookings = Booking.objects.filter(hall=managed_hall, status='completed').count()
    cancelled_bookings = Booking.objects.filter(hall=managed_hall, status='cancelled').count()

    # إيرادات القاعة
    total_revenue = Booking.objects.filter(
        hall=managed_hall,
        status='completed'
    ).aggregate(total=Sum('total_price'))['total'] or 0

    # الحجوزات الأخيرة
    recent_bookings = Booking.objects.filter(
        hall=managed_hall
    ).order_by('-created_at')[:10]

    # الحجوزات القادمة
    upcoming_bookings = Booking.objects.filter(
        hall=managed_hall,
        status__in=['approved', 'pending'],
        start_datetime__gte=timezone.now()
    ).order_by('start_datetime')[:5]

    context = {
        'managed_hall': managed_hall,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'approved_bookings': approved_bookings,
        'completed_bookings': completed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'total_revenue': total_revenue,
        'recent_bookings': recent_bookings,
        'upcoming_bookings': upcoming_bookings,
    }
    return render(request, 'hall_booking/hall_manager/dashboard.html', context)

@login_required
@user_passes_test(is_hall_manager)
def hall_manager_bookings(request):
    """إدارة حجوزات القاعة"""
    managed_hall = get_user_managed_hall(request.user)
    if not managed_hall:
        messages.error(request, 'لا يمكنك الوصول لهذه الصفحة')
        return redirect('hall_booking:home')

    # فلترة الحجوزات
    bookings = Booking.objects.filter(hall=managed_hall).order_by('-created_at')

    # البحث والفلترة
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    if search_query:
        bookings = bookings.filter(
            Q(event_title__icontains=search_query) |
            Q(customer_name__icontains=search_query) |
            Q(customer_phone__icontains=search_query)
        )

    if status_filter:
        bookings = bookings.filter(status=status_filter)

    # التصفح
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    bookings = paginator.get_page(page_number)

    context = {
        'managed_hall': managed_hall,
        'bookings': bookings,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'hall_booking/hall_manager/bookings.html', context)

@login_required
@user_passes_test(is_hall_manager)
def hall_manager_booking_detail(request, booking_id):
    """تفاصيل الحجز لمدير القاعة"""
    managed_hall = get_user_managed_hall(request.user)
    if not managed_hall:
        messages.error(request, 'لا يمكنك الوصول لهذه الصفحة')
        return redirect('hall_booking:home')

    booking = get_object_or_404(Booking, id=booking_id, hall=managed_hall)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        admin_notes = request.POST.get('admin_notes', '')

        if new_status in ['pending', 'approved', 'completed', 'cancelled']:
            booking.status = new_status
            if admin_notes:
                booking.admin_notes = admin_notes
            booking.save()
            messages.success(request, 'تم تحديث حالة الحجز بنجاح')
            return redirect('hall_booking:hall_manager_bookings')

    context = {
        'managed_hall': managed_hall,
        'booking': booking,
    }
    return render(request, 'hall_booking/hall_manager/booking_detail.html', context)

@login_required
@user_passes_test(is_hall_manager)
def hall_manager_schedule(request):
    """جدول مواعيد القاعة"""
    managed_hall = get_user_managed_hall(request.user)
    if not managed_hall:
        messages.error(request, 'لا يمكنك الوصول لهذه الصفحة')
        return redirect('hall_booking:home')

    # الحصول على التاريخ المطلوب (افتراضياً الشهر الحالي)
    from datetime import datetime, timedelta
    import calendar

    year = int(request.GET.get('year', datetime.now().year))
    month = int(request.GET.get('month', datetime.now().month))

    # الحصول على أول وآخر يوم في الشهر
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)

    # الحصول على الحجوزات في هذا الشهر
    bookings = Booking.objects.filter(
        hall=managed_hall,
        start_datetime__date__gte=first_day.date(),
        start_datetime__date__lte=last_day.date()
    ).order_by('start_datetime')

    # تنظيم الحجوزات حسب التاريخ
    bookings_by_date = {}
    for booking in bookings:
        date_key = booking.start_datetime.date()
        if date_key not in bookings_by_date:
            bookings_by_date[date_key] = []
        bookings_by_date[date_key].append(booking)

    # إنشاء التقويم
    cal = calendar.monthcalendar(year, month)

    context = {
        'managed_hall': managed_hall,
        'bookings': bookings,
        'bookings_by_date': bookings_by_date,
        'calendar': cal,
        'current_year': year,
        'current_month': month,
        'month_name': calendar.month_name[month],
        'prev_month': month - 1 if month > 1 else 12,
        'prev_year': year if month > 1 else year - 1,
        'next_month': month + 1 if month < 12 else 1,
        'next_year': year if month < 12 else year + 1,
    }
    return render(request, 'hall_booking/hall_manager/schedule.html', context)

# ==================== Multi-Step Booking Views ====================

def booking_step1_date(request, hall_id):
    """الخطوة الأولى: اختيار التاريخ"""
    hall = get_object_or_404(Hall, id=hall_id)

    if request.method == 'POST':
        selected_date = request.POST.get('date')
        if selected_date:
            # حفظ التاريخ في الجلسة
            request.session['booking_data'] = {
                'hall_id': hall_id,
                'date': selected_date
            }
            return redirect('hall_booking:booking_step2_time', hall_id=hall_id)
        else:
            messages.error(request, 'يرجى اختيار تاريخ صحيح')

    # الحصول على التواريخ المحجوزة لإخفائها
    from datetime import datetime, timedelta
    today = datetime.now().date()

    # الحصول على التواريخ المحجوزة في الشهرين القادمين
    end_date = today + timedelta(days=60)
    booked_dates = Booking.objects.filter(
        hall=hall,
        start_datetime__date__gte=today,
        start_datetime__date__lte=end_date,
        status__in=['approved', 'pending']
    ).values_list('start_datetime__date', flat=True).distinct()

    # تحويل التواريخ إلى strings للاستخدام في JavaScript
    booked_dates_str = [date.strftime('%Y-%m-%d') for date in booked_dates]

    context = {
        'hall': hall,
        'booked_dates': booked_dates_str,
        'min_date': today.strftime('%Y-%m-%d'),
        'max_date': end_date.strftime('%Y-%m-%d'),
    }
    return render(request, 'hall_booking/booking/step1_date.html', context)

def booking_step2_time(request, hall_id):
    """الخطوة الثانية: اختيار الوقت"""
    hall = get_object_or_404(Hall, id=hall_id)

    # التحقق من وجود بيانات الخطوة الأولى
    booking_data = request.session.get('booking_data', {})
    if not booking_data.get('date') or booking_data.get('hall_id') != hall_id:
        messages.error(request, 'يرجى البدء من اختيار التاريخ')
        return redirect('hall_booking:booking_step1_date', hall_id=hall_id)

    selected_date = booking_data['date']

    if request.method == 'POST':
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        if start_time and end_time:
            # التحقق من صحة الأوقات
            from datetime import datetime, timedelta
            try:
                start_datetime = datetime.strptime(f"{selected_date} {start_time}", '%Y-%m-%d %H:%M')
                end_datetime = datetime.strptime(f"{selected_date} {end_time}", '%Y-%m-%d %H:%M')

                if end_datetime <= start_datetime:
                    messages.error(request, 'وقت النهاية يجب أن يكون بعد وقت البداية')
                else:
                    # التحقق من عدم تعارض الأوقات
                    conflicting_bookings = Booking.objects.filter(
                        hall=hall,
                        start_datetime__date=start_datetime.date(),
                        status__in=['approved', 'pending']
                    ).filter(
                        Q(start_datetime__lt=end_datetime) & Q(end_datetime__gt=start_datetime)
                    )

                    if conflicting_bookings.exists():
                        messages.error(request, 'هذا الوقت محجوز بالفعل، يرجى اختيار وقت آخر')
                    else:
                        # حساب السعر
                        duration_hours = (end_datetime - start_datetime).total_seconds() / 3600
                        total_price = float(hall.price_per_hour) * duration_hours

                        # حفظ بيانات الوقت في الجلسة
                        booking_data.update({
                            'start_time': start_time,
                            'end_time': end_time,
                            'start_datetime': start_datetime.isoformat(),
                            'end_datetime': end_datetime.isoformat(),
                            'duration_hours': duration_hours,
                            'total_price': total_price
                        })
                        request.session['booking_data'] = booking_data
                        return redirect('hall_booking:booking_step3_info', hall_id=hall_id)

            except ValueError:
                messages.error(request, 'تنسيق الوقت غير صحيح')
        else:
            messages.error(request, 'يرجى اختيار وقت البداية والنهاية')

    # الحصول على الأوقات المحجوزة في هذا التاريخ
    from datetime import datetime
    selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()

    booked_times = Booking.objects.filter(
        hall=hall,
        start_datetime__date=selected_date_obj,
        status__in=['approved', 'pending']
    ).values('start_datetime__time', 'end_datetime__time')

    # تحويل الأوقات المحجوزة إلى تنسيق يمكن استخدامه في JavaScript
    booked_slots = []
    for booking in booked_times:
        booked_slots.append({
            'start': booking['start_datetime__time'].strftime('%H:%M'),
            'end': booking['end_datetime__time'].strftime('%H:%M')
        })

    context = {
        'hall': hall,
        'selected_date': selected_date,
        'booked_slots': booked_slots,
    }
    return render(request, 'hall_booking/booking/step2_time.html', context)

def booking_step3_info(request, hall_id):
    """الخطوة الثالثة: معلومات التواصل والحدث"""
    hall = get_object_or_404(Hall, id=hall_id)

    # التحقق من وجود بيانات الخطوات السابقة
    booking_data = request.session.get('booking_data', {})
    if not all([booking_data.get('date'), booking_data.get('start_time'),
                booking_data.get('hall_id') == hall_id]):
        messages.error(request, 'يرجى إكمال الخطوات السابقة أولاً')
        return redirect('hall_booking:booking_step1_date', hall_id=hall_id)

    if request.method == 'POST':
        # جمع بيانات النموذج
        customer_name = request.POST.get('customer_name', '').strip()
        customer_email = request.POST.get('customer_email', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        event_title = request.POST.get('event_title', '').strip()
        event_description = request.POST.get('event_description', '').strip()
        attendees_count = request.POST.get('attendees_count', '').strip()

        # التحقق من صحة البيانات
        errors = []
        if not customer_name:
            errors.append('اسم العميل مطلوب')
        if not customer_email:
            errors.append('البريد الإلكتروني مطلوب')
        if not customer_phone:
            errors.append('رقم الهاتف مطلوب')
        if not event_title:
            errors.append('عنوان الحدث مطلوب')
        if not attendees_count or not attendees_count.isdigit():
            errors.append('عدد الحضور يجب أن يكون رقماً صحيحاً')
        elif int(attendees_count) > hall.capacity:
            errors.append(f'عدد الحضور لا يمكن أن يتجاوز سعة القاعة ({hall.capacity} شخص)')

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # حفظ بيانات التواصل في الجلسة
            booking_data.update({
                'customer_name': customer_name,
                'customer_email': customer_email,
                'customer_phone': customer_phone,
                'event_title': event_title,
                'event_description': event_description,
                'attendees_count': int(attendees_count)
            })
            request.session['booking_data'] = booking_data
            return redirect('hall_booking:booking_step4_review', hall_id=hall_id)

    # تعبئة البيانات المحفوظة مسبقاً
    initial_data = {}
    if request.user.is_authenticated:
        initial_data['customer_email'] = request.user.email or ''
        full_name = request.user.get_full_name()
        if full_name:
            initial_data['customer_name'] = full_name

    # إضافة البيانات المحفوظة في الجلسة
    for field in ['customer_name', 'customer_email', 'customer_phone',
                  'event_title', 'event_description', 'attendees_count']:
        if booking_data.get(field):
            initial_data[field] = booking_data[field]

    context = {
        'hall': hall,
        'booking_data': booking_data,
        'initial_data': initial_data,
    }
    return render(request, 'hall_booking/booking/step3_info.html', context)

def booking_step4_review(request, hall_id):
    """الخطوة الرابعة: مراجعة الحجز والإرسال"""
    hall = get_object_or_404(Hall, id=hall_id)

    # التحقق من وجود جميع بيانات الخطوات السابقة
    booking_data = request.session.get('booking_data', {})
    required_fields = ['date', 'start_time', 'end_time', 'customer_name',
                      'customer_email', 'customer_phone', 'event_title', 'attendees_count']

    if not all([booking_data.get(field) for field in required_fields]) or booking_data.get('hall_id') != hall_id:
        messages.error(request, 'يرجى إكمال جميع الخطوات السابقة')
        return redirect('hall_booking:booking_step1_date', hall_id=hall_id)

    if request.method == 'POST':
        # إنشاء الحجز
        from datetime import datetime

        try:
            start_datetime = datetime.fromisoformat(booking_data['start_datetime'])
            end_datetime = datetime.fromisoformat(booking_data['end_datetime'])

            # التحقق مرة أخيرة من عدم تعارض الأوقات
            conflicting_bookings = Booking.objects.filter(
                hall=hall,
                start_datetime__date=start_datetime.date(),
                status__in=['approved', 'pending']
            ).filter(
                Q(start_datetime__lt=end_datetime) & Q(end_datetime__gt=start_datetime)
            )

            if conflicting_bookings.exists():
                messages.error(request, 'عذراً، تم حجز هذا الوقت من قبل عميل آخر. يرجى اختيار وقت آخر.')
                return redirect('hall_booking:booking_step2_time', hall_id=hall_id)

            # إنشاء الحجز
            booking = Booking.objects.create(
                hall=hall,
                user=request.user if request.user.is_authenticated else None,
                customer_name=booking_data['customer_name'],
                customer_email=booking_data['customer_email'],
                customer_phone=booking_data['customer_phone'],
                event_title=booking_data['event_title'],
                event_description=booking_data.get('event_description', ''),
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                attendees_count=booking_data['attendees_count'],
                total_price=booking_data['total_price'],
                status='pending'
            )

            # مسح بيانات الجلسة
            if 'booking_data' in request.session:
                del request.session['booking_data']

            messages.success(request, f'تم إرسال طلب الحجز بنجاح! رقم الحجز: {booking.booking_id}')
            return redirect('hall_booking:booking_success', booking_id=booking.booking_id)

        except Exception as e:
            messages.error(request, 'حدث خطأ أثناء إنشاء الحجز. يرجى المحاولة مرة أخرى.')
            return redirect('hall_booking:booking_step1_date', hall_id=hall_id)

    # تحضير البيانات للعرض
    from datetime import datetime
    start_datetime = datetime.fromisoformat(booking_data['start_datetime'])
    end_datetime = datetime.fromisoformat(booking_data['end_datetime'])

    context = {
        'hall': hall,
        'booking_data': booking_data,
        'start_datetime': start_datetime,
        'end_datetime': end_datetime,
    }
    return render(request, 'hall_booking/booking/step4_review.html', context)

def booking_success(request, booking_id):
    """صفحة نجاح الحجز"""
    booking = get_object_or_404(Booking, booking_id=booking_id)

    context = {
        'booking': booking,
    }
    return render(request, 'hall_booking/booking/success.html', context)

@login_required
def user_profile(request):
    """صفحة البروفيل الشخصي للمستخدم"""
    user = request.user

    # جلب حجوزات المستخدم
    bookings = Booking.objects.filter(user=user).order_by('-created_at')

    # جلب الإشعارات
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    unread_notifications = notifications.filter(is_read=False)

    # إحصائيات الحجوزات
    total_bookings = bookings.count()
    pending_bookings = bookings.filter(status='pending').count()
    approved_bookings = bookings.filter(status='approved').count()
    completed_bookings = bookings.filter(status='completed').count()
    rejected_bookings = bookings.filter(status='rejected').count()
    cancelled_bookings = bookings.filter(status='cancelled').count()

    # تقسيم الحجوزات حسب الحالة
    bookings_by_status = {
        'pending': bookings.filter(status='pending'),
        'approved': bookings.filter(status='approved'),
        'completed': bookings.filter(status='completed'),
        'rejected': bookings.filter(status='rejected'),
        'cancelled': bookings.filter(status='cancelled'),
    }

    context = {
        'user': user,
        'bookings': bookings[:5],  # آخر 5 حجوزات
        'bookings_by_status': bookings_by_status,
        'notifications': notifications[:5],  # آخر 5 إشعارات
        'unread_notifications_count': unread_notifications.count(),
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'approved_bookings': approved_bookings,
        'completed_bookings': completed_bookings,
        'rejected_bookings': rejected_bookings,
        'cancelled_bookings': cancelled_bookings,
    }
    return render(request, 'hall_booking/profile/profile.html', context)

@login_required
def user_bookings(request):
    """صفحة جميع حجوزات المستخدم"""
    user = request.user
    status_filter = request.GET.get('status', 'all')

    # جلب الحجوزات
    bookings = Booking.objects.filter(user=user).order_by('-created_at')

    # تطبيق فلتر الحالة
    if status_filter != 'all':
        bookings = bookings.filter(status=status_filter)

    # تقسيم الصفحات
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_choices': Booking.STATUS_CHOICES,
    }
    return render(request, 'hall_booking/profile/bookings.html', context)

@login_required
def booking_detail_user(request, booking_id):
    """صفحة تفاصيل الحجز للمستخدم"""
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)

    context = {
        'booking': booking,
        'can_cancel': booking.status == 'pending',
    }
    return render(request, 'hall_booking/profile/booking_detail.html', context)

@login_required
def cancel_booking(request, booking_id):
    """إلغاء الحجز"""
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)

    if booking.status != 'pending':
        messages.error(request, 'لا يمكن إلغاء هذا الحجز.')
        return redirect('booking_detail_user', booking_id=booking_id)

    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, 'تم إلغاء الحجز بنجاح.')
        return redirect('user_profile')

    context = {
        'booking': booking,
    }
    return render(request, 'hall_booking/profile/cancel_booking.html', context)

@login_required
def edit_profile(request):
    """تعديل البروفيل الشخصي"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()

        messages.success(request, 'تم تحديث البروفيل بنجاح.')
        return redirect('user_profile')

    context = {
        'user': request.user,
    }
    return render(request, 'hall_booking/profile/edit_profile.html', context)

@login_required
def user_notifications(request):
    """صفحة الإشعارات"""
    user = request.user

    # جلب الإشعارات
    notifications = Notification.objects.filter(user=user).order_by('-created_at')

    # تقسيم الصفحات
    paginator = Paginator(notifications, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # تحديد الإشعارات كمقروءة عند عرضها
    unread_notifications = notifications.filter(is_read=False)
    unread_notifications.update(is_read=True)

    context = {
        'page_obj': page_obj,
        'total_notifications': notifications.count(),
    }
    return render(request, 'hall_booking/profile/notifications.html', context)

@login_required
def mark_notification_read(request, notification_id):
    """تحديد إشعار كمقروء"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    return redirect('user_notifications')

@login_required
def get_unread_notifications_count(request):
    """الحصول على عدد الإشعارات غير المقروءة"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})

# New Booking Wizard Views

def booking_step1_date(request, hall_id):
    """الخطوة الأولى: اختيار التاريخ"""
    hall = get_object_or_404(Hall, id=hall_id, status='available')
    
    context = {
        'hall': hall,
    }
    return render(request, 'hall_booking/booking/step1_date.html', context)

def booking_step2_time(request, hall_id):
    """الخطوة الثانية: اختيار الوقت"""
    hall = get_object_or_404(Hall, id=hall_id, status='available')
    
    # الحصول على التاريخ المحدد من الجلسة أو من الطلب
    selected_date = request.session.get('selected_date')
    if not selected_date and request.GET.get('date'):
        selected_date = request.GET.get('date')
    
    # الحصول على الحجوزات المتداخلة في هذا التاريخ
    booked_slots = []
    if selected_date:
        try:
            from datetime import datetime
            date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
            bookings = Booking.objects.filter(
                hall=hall,
                start_datetime__date=date_obj,
                status__in=['approved', 'pending']
            ).order_by('start_datetime')
            
            for booking in bookings:
                booked_slots.append({
                    'start': booking.start_datetime.strftime('%H:%M'),
                    'end': booking.end_datetime.strftime('%H:%M')
                })
        except ValueError:
            pass
    
    # توليد الأوقات المتاحة
    available_times = []
    for hour in range(8, 23):  # من 8 صباحاً إلى 11 مساءً
        for minute in [0, 30]:  # كل نصف ساعة
            time_str = f"{hour:02d}:{minute:02d}"
            available_times.append(time_str)
    
    context = {
        'hall': hall,
        'selected_date': selected_date,
        'booked_slots': booked_slots,
        'available_times': available_times,
    }
    return render(request, 'hall_booking/booking/step2_time.html', context)

def booking_step3_services(request, hall_id):
    """الخطوة الثالثة: اختيار الخدمات"""
    hall = get_object_or_404(Hall, id=hall_id, status='available')
    hall_services = hall.hall_services.filter(is_available=True).order_by('name')
    
    context = {
        'hall': hall,
        'hall_services': hall_services,
    }
    return render(request, 'hall_booking/booking/step3_services.html', context)

def booking_step4_meals(request, hall_id):
    """الخطوة الرابعة: اختيار الوجبات"""
    hall = get_object_or_404(Hall, id=hall_id, status='available')
    hall_meals = hall.hall_meals.filter(is_available=True).order_by('meal_type', 'name')
    
    context = {
        'hall': hall,
        'hall_meals': hall_meals,
    }
    return render(request, 'hall_booking/booking/step4_meals.html', context)

def booking_step5_info(request, hall_id):
    """الخطوة الخامسة: المعلومات الشخصية"""
    hall = get_object_or_404(Hall, id=hall_id, status='available')
    
    context = {
        'hall': hall,
    }
    return render(request, 'hall_booking/booking/step5_info.html', context)

def booking_step6_review(request, hall_id):
    """الخطوة السادسة: مراجعة وتأكيد الحجز"""
    hall = get_object_or_404(Hall, id=hall_id, status='available')
    hall_services = hall.hall_services.filter(is_available=True).order_by('name')
    hall_meals = hall.hall_meals.filter(is_available=True).order_by('meal_type', 'name')
    
    context = {
        'hall': hall,
        'hall_services': hall_services,
        'hall_meals': hall_meals,
    }
    return render(request, 'hall_booking/booking/step6_review.html', context)

@csrf_exempt
def confirm_booking(request, hall_id):
    """تأكيد الحجز وحفظه في قاعدة البيانات"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'طريقة طلب غير صحيحة'})
    
    try:
        hall = get_object_or_404(Hall, id=hall_id, status='available')
        data = json.loads(request.body)
        
        # استخراج البيانات
        booking_datetime = data.get('booking_datetime', {})
        customer_info = data.get('customer_info', {})
        selected_services = data.get('selected_services', [])
        selected_meals = data.get('selected_meals', [])
        
        # التحقق من صحة البيانات
        if not all([booking_datetime.get('date'), booking_datetime.get('start_time'), 
                   booking_datetime.get('end_time'), customer_info.get('customer_name'),
                   customer_info.get('customer_email'), customer_info.get('customer_phone')]):
            return JsonResponse({'success': False, 'message': 'بيانات غير مكتملة'})
        
        # تحويل التاريخ والوقت
        date_str = booking_datetime['date']
        start_time_str = booking_datetime['start_time']
        end_time_str = booking_datetime['end_time']
        
        start_datetime = datetime.strptime(f"{date_str} {start_time_str}", "%Y-%m-%d %H:%M")
        end_datetime = datetime.strptime(f"{date_str} {end_time_str}", "%Y-%m-%d %H:%M")
        
        # التحقق من عدم تداخل الحجوزات
        conflicting_bookings = Booking.objects.filter(
            hall=hall,
            status__in=['approved', 'pending'],
            start_datetime__lt=end_datetime,
            end_datetime__gt=start_datetime
        )
        
        if conflicting_bookings.exists():
            return JsonResponse({'success': False, 'message': 'القاعة محجوزة في هذا الوقت'})
        
        # حساب السعر الإجمالي
        duration_hours = (end_datetime - start_datetime).total_seconds() / 3600
        hall_cost = float(hall.price_per_hour) * duration_hours
        
        services_cost = 0
        for service_data in selected_services:
            try:
                service = HallService.objects.get(id=service_data['id'], hall=hall, is_available=True)
                services_cost += float(service.price) * service_data['quantity']
            except HallService.DoesNotExist:
                continue
        
        meals_cost = 0
        for meal_data in selected_meals:
            try:
                meal = HallMeal.objects.get(id=meal_data['id'], hall=hall, is_available=True)
                meals_cost += float(meal.price_per_person) * meal_data['quantity']
            except HallMeal.DoesNotExist:
                continue
        
        total_price = hall_cost + services_cost + meals_cost
        
        # إنشاء الحجز
        booking = Booking.objects.create(
            hall=hall,
            user=request.user if request.user.is_authenticated else None,
            customer_name=customer_info['customer_name'],
            customer_email=customer_info['customer_email'],
            customer_phone=customer_info['customer_phone'],
            event_title=customer_info['event_title'],
            event_description=customer_info.get('event_description', ''),
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            attendees_count=int(customer_info['attendees_count']),
            total_price=total_price,
            status='pending'
        )
        
        # إضافة الخدمات المختارة
        for service_data in selected_services:
            try:
                service = HallService.objects.get(id=service_data['id'], hall=hall, is_available=True)
                BookingService.objects.create(
                    booking=booking,
                    service=service,
                    quantity=service_data['quantity'],
                    price=service.price
                )
            except HallService.DoesNotExist:
                continue
        
        # إضافة الوجبات المختارة
        for meal_data in selected_meals:
            try:
                meal = HallMeal.objects.get(id=meal_data['id'], hall=hall, is_available=True)
                serving_time = datetime.strptime(meal_data['serving_time'], '%H:%M').time()
                BookingMeal.objects.create(
                    booking=booking,
                    meal=meal,
                    quantity=meal_data['quantity'],
                    price_per_person=meal.price_per_person,
                    serving_time=serving_time
                )
            except (HallMeal.DoesNotExist, ValueError):
                continue
        
        return JsonResponse({
            'success': True,
            'message': 'تم إرسال طلب الحجز بنجاح',
            'redirect_url': f'/booking/success/{booking.booking_id}/'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'حدث خطأ: {str(e)}'})

def booking_success(request, booking_id):
    """صفحة نجاح الحجز"""
    booking = get_object_or_404(Booking, booking_id=booking_id)
    
    context = {
        'booking': booking,
    }
    return render(request, 'hall_booking/booking/success.html', context)

# ==================== Hall Manager Dashboard Views ====================

@login_required
@user_passes_test(lambda u: u.is_staff or hasattr(u, 'hall_manager'))
def hall_manager_dashboard(request):
    """لوحة تحكم مدير القاعة"""
    try:
        hall_manager = request.user.hall_manager
        halls = Hall.objects.filter(manager=hall_manager)
    except:
        # إذا كان المستخدم admin
        halls = Hall.objects.all()
    
    # إضافة الإحصائيات لكل قاعة
    halls_with_stats = []
    for hall in halls:
        hall_stats = {
            'hall': hall,
            'total_bookings': hall.bookings.count(),
            'pending_bookings': hall.bookings.filter(status='pending').count(),
            'approved_bookings': hall.bookings.filter(status='approved').count(),
        }
        halls_with_stats.append(hall_stats)
    
    context = {
        'halls_with_stats': halls_with_stats,
    }
    return render(request, 'hall_booking/manager/dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or hasattr(u, 'hall_manager'))
def hall_management(request, hall_id):
    """صفحة إدارة القاعة الشاملة"""
    hall = get_object_or_404(Hall, id=hall_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_staff:
        if not hasattr(request.user, 'hall_manager') or hall.manager != request.user.hall_manager:
            return redirect('hall_booking:home')
    
    # إحصائيات القاعة
    total_bookings = Booking.objects.filter(hall=hall).count()
    pending_bookings = Booking.objects.filter(hall=hall, status='pending').count()
    approved_bookings = Booking.objects.filter(hall=hall, status='approved').count()
    
    # الحجوزات القادمة
    from datetime import datetime, timedelta
    upcoming_bookings = Booking.objects.filter(
        hall=hall,
        start_datetime__gte=datetime.now(),
        status__in=['approved', 'pending']
    ).order_by('start_datetime')[:5]
    
    # الخدمات والوجبات
    hall_services = hall.hall_services.all().order_by('name')
    hall_meals = hall.hall_meals.all().order_by('meal_type', 'name')
    
    # صور القاعة
    hall_images = hall.images.all()
    
    context = {
        'hall': hall,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'approved_bookings': approved_bookings,
        'upcoming_bookings': upcoming_bookings,
        'hall_services': hall_services,
        'hall_meals': hall_meals,
        'hall_images': hall_images,
    }
    return render(request, 'hall_booking/manager/hall_management.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or hasattr(u, 'hall_manager'))
def hall_schedule_management(request, hall_id):
    """إدارة جدول مواعيد القاعة"""
    hall = get_object_or_404(Hall, id=hall_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_staff:
        if not hasattr(request.user, 'hall_manager') or hall.manager != request.user.hall_manager:
            return redirect('hall_booking:home')
    
    from datetime import datetime, timedelta
    import calendar
    
    # الحصول على التاريخ المحدد أو التاريخ الحالي
    selected_date = request.GET.get('date')
    if selected_date:
        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except:
            selected_date = datetime.now().date()
    else:
        selected_date = datetime.now().date()
    
    # الحصول على نوع العرض
    view_type = request.GET.get('view', 'day')
    
    context = {
        'hall': hall,
        'selected_date': selected_date,
        'view_type': view_type,
    }
    
    if view_type == 'day':
        # عرض اليوم الواحد
        bookings = Booking.objects.filter(
            hall=hall,
            start_datetime__date=selected_date
        ).order_by('start_datetime')
        
        # إنشاء جدول زمني (من 8 صباحاً إلى 11 مساءً)
        time_slots = []
        for hour in range(8, 23):
            for minute in [0, 30]:
                time_str = f"{hour:02d}:{minute:02d}"
                
                # التحقق من وجود حجز في هذا الوقت
                slot_datetime = datetime.combine(selected_date, datetime.strptime(time_str, '%H:%M').time())
                is_booked = bookings.filter(
                    start_datetime__lte=slot_datetime,
                    end_datetime__gt=slot_datetime
                ).exists()
                
                # الحصول على تفاصيل الحجز إن وجد
                booking_details = None
                if is_booked:
                    booking_details = bookings.filter(
                        start_datetime__lte=slot_datetime,
                        end_datetime__gt=slot_datetime
                    ).first()
                
                time_slots.append({
                    'time': time_str,
                    'datetime': slot_datetime,
                    'is_booked': is_booked,
                    'booking': booking_details
                })
        
        context.update({
            'time_slots': time_slots,
            'bookings': bookings,
        })
    
    elif view_type == 'week':
        # عرض الأسبوع
        # الحصول على بداية ونهاية الأسبوع
        week_start = selected_date - timedelta(days=selected_date.weekday())
        week_end = week_start + timedelta(days=6)
        
        # الحصول على حجوزات الأسبوع
        week_bookings = Booking.objects.filter(
            hall=hall,
            start_datetime__date__range=[week_start, week_end]
        ).order_by('start_datetime')
        
        # تنظيم البيانات حسب الأيام
        week_days = []
        for i in range(7):
            day_date = week_start + timedelta(days=i)
            day_bookings = week_bookings.filter(start_datetime__date=day_date)
            week_days.append({
                'date': day_date,
                'bookings': day_bookings
            })
        
        context.update({
            'week_start': week_start,
            'week_end': week_end,
            'week_days': week_days,
            'hours_range': range(8, 23),
        })
    
    elif view_type == 'month':
        # عرض الشهر
        # الحصول على بداية ونهاية الشهر
        month_start = selected_date.replace(day=1)
        next_month = month_start.replace(month=month_start.month % 12 + 1) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1)
        month_end = next_month - timedelta(days=1)
        
        # الحصول على حجوزات الشهر
        month_bookings = Booking.objects.filter(
            hall=hall,
            start_datetime__date__range=[month_start, month_end]
        ).order_by('start_datetime')
        
        # إنشاء التقويم
        cal = calendar.monthcalendar(selected_date.year, selected_date.month)
        month_weeks = []
        
        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    # يوم من الشهر السابق أو التالي
                    week_data.append({
                        'day': '',
                        'date': None,
                        'bookings': [],
                        'is_other_month': True,
                        'is_today': False
                    })
                else:
                    day_date = selected_date.replace(day=day)
                    day_bookings = month_bookings.filter(start_datetime__date=day_date)
                    is_today = day_date == datetime.now().date()
                    
                    week_data.append({
                        'day': day,
                        'date': day_date,
                        'bookings': day_bookings,
                        'is_other_month': False,
                        'is_today': is_today
                    })
            month_weeks.append(week_data)
        
        context.update({
            'month_weeks': month_weeks,
        })
    
    return render(request, 'hall_booking/manager/schedule_management.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or hasattr(u, 'hall_manager'))
def block_time_slot(request, hall_id):
    """حجب فترة زمنية معينة"""
    if request.method == 'POST':
        hall = get_object_or_404(Hall, id=hall_id)
        
        # التحقق من الصلاحيات
        if not request.user.is_staff:
            if not hasattr(request.user, 'hall_manager') or hall.manager != request.user.hall_manager:
                return JsonResponse({'success': False, 'error': 'غير مصرح لك'})
        
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        reason = request.POST.get('reason', 'محجوب من قبل الإدارة')
        
        try:
            from datetime import datetime
            start_datetime = datetime.strptime(f"{date} {start_time}", '%Y-%m-%d %H:%M')
            end_datetime = datetime.strptime(f"{date} {end_time}", '%Y-%m-%d %H:%M')
            
            # إنشاء حجز إداري
            blocked_booking = Booking.objects.create(
                hall=hall,
                customer_name='الإدارة',
                customer_email='admin@system.com',
                customer_phone='000000000',
                event_title=reason,
                event_description='فترة محجوبة من قبل الإدارة',
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                attendees_count=0,
                total_price=0,
                status='approved',
                is_admin_block=True
            )
            
            return JsonResponse({'success': True, 'message': 'تم حجب الفترة الزمنية بنجاح'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'طريقة غير صحيحة'})

# ==================== إدارة الخدمات والوجبات ====================

@login_required
@user_passes_test(lambda u: u.is_staff or hasattr(u, 'hall_manager'))
def manage_hall_service(request, hall_id):
    """إدارة خدمات القاعة (إضافة، تعديل، حذف)"""
    hall = get_object_or_404(Hall, id=hall_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_staff:
        if not hasattr(request.user, 'hall_manager') or hall.manager != request.user.hall_manager:
            return JsonResponse({'success': False, 'error': 'غير مصرح لك'})
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            price = request.POST.get('price', 0)
            
            try:
                service = HallService.objects.create(
                    hall=hall,
                    name=name,
                    description=description,
                    price=float(price)
                )
                return JsonResponse({
                    'success': True, 
                    'message': 'تم إضافة الخدمة بنجاح',
                    'service': {
                        'id': service.id,
                        'name': service.name,
                        'description': service.description,
                        'price': service.price
                    }
                })
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        elif action == 'edit':
            service_id = request.POST.get('service_id')
            try:
                service = HallService.objects.get(id=service_id, hall=hall)
                service.name = request.POST.get('name', service.name)
                service.description = request.POST.get('description', service.description)
                service.price = float(request.POST.get('price', service.price))
                service.save()
                
                return JsonResponse({
                    'success': True, 
                    'message': 'تم تحديث الخدمة بنجاح'
                })
            except HallService.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'الخدمة غير موجودة'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        elif action == 'delete':
            service_id = request.POST.get('service_id')
            try:
                service = HallService.objects.get(id=service_id, hall=hall)
                service.delete()
                return JsonResponse({'success': True, 'message': 'تم حذف الخدمة بنجاح'})
            except HallService.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'الخدمة غير موجودة'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'طريقة غير صحيحة'})

@login_required
@user_passes_test(lambda u: u.is_staff or hasattr(u, 'hall_manager'))
def manage_hall_meal(request, hall_id):
    """إدارة وجبات القاعة (إضافة، تعديل، حذف)"""
    hall = get_object_or_404(Hall, id=hall_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_staff:
        if not hasattr(request.user, 'hall_manager') or hall.manager != request.user.hall_manager:
            return JsonResponse({'success': False, 'error': 'غير مصرح لك'})
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            price_per_person = request.POST.get('price_per_person', 0)
            meal_type = request.POST.get('meal_type', 'main')
            is_vegetarian = request.POST.get('is_vegetarian') == 'on'
            
            try:
                meal = HallMeal.objects.create(
                    hall=hall,
                    name=name,
                    description=description,
                    price_per_person=float(price_per_person),
                    meal_type=meal_type,
                    is_vegetarian=is_vegetarian
                )
                return JsonResponse({
                    'success': True, 
                    'message': 'تم إضافة الوجبة بنجاح',
                    'meal': {
                        'id': meal.id,
                        'name': meal.name,
                        'description': meal.description,
                        'price_per_person': meal.price_per_person,
                        'meal_type': meal.meal_type,
                        'is_vegetarian': meal.is_vegetarian
                    }
                })
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        elif action == 'edit':
            meal_id = request.POST.get('meal_id')
            try:
                meal = HallMeal.objects.get(id=meal_id, hall=hall)
                meal.name = request.POST.get('name', meal.name)
                meal.description = request.POST.get('description', meal.description)
                meal.price_per_person = float(request.POST.get('price_per_person', meal.price_per_person))
                meal.meal_type = request.POST.get('meal_type', meal.meal_type)
                meal.is_vegetarian = request.POST.get('is_vegetarian') == 'on'
                meal.save()
                
                return JsonResponse({
                    'success': True, 
                    'message': 'تم تحديث الوجبة بنجاح'
                })
            except HallMeal.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'الوجبة غير موجودة'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        elif action == 'delete':
            meal_id = request.POST.get('meal_id')
            try:
                meal = HallMeal.objects.get(id=meal_id, hall=hall)
                meal.delete()
                return JsonResponse({'success': True, 'message': 'تم حذف الوجبة بنجاح'})
            except HallMeal.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'الوجبة غير موجودة'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'طريقة غير صحيحة'})

@login_required
@user_passes_test(lambda u: u.is_staff or hasattr(u, 'hall_manager'))
def manage_hall_image(request, hall_id):
    """إدارة صور القاعة (رفع، حذف)"""
    hall = get_object_or_404(Hall, id=hall_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_staff:
        if not hasattr(request.user, 'hall_manager') or hall.manager != request.user.hall_manager:
            return JsonResponse({'success': False, 'error': 'غير مصرح لك'})
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'upload':
            title = request.POST.get('title', '')
            image_file = request.FILES.get('image')
            
            if not image_file:
                return JsonResponse({'success': False, 'error': 'لم يتم اختيار صورة'})
            
            try:
                image = HallImage.objects.create(
                    hall=hall,
                    title=title,
                    image=image_file
                )
                return JsonResponse({
                    'success': True, 
                    'message': 'تم رفع الصورة بنجاح',
                    'image': {
                        'id': image.id,
                        'title': image.title,
                        'url': image.image.url if image.image else ''
                    }
                })
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        elif action == 'delete':
            image_id = request.POST.get('image_id')
            try:
                image = HallImage.objects.get(id=image_id, hall=hall)
                # حذف الملف من النظام
                if image.image:
                    image.image.delete()
                image.delete()
                return JsonResponse({'success': True, 'message': 'تم حذف الصورة بنجاح'})
            except HallImage.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'الصورة غير موجودة'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'طريقة غير صحيحة'})

@login_required
@user_passes_test(lambda u: u.is_staff or hasattr(u, 'hall_manager'))
def manage_booking_status(request, hall_id, booking_id):
    """إدارة حالة الحجز (موافقة، رفض)"""
    hall = get_object_or_404(Hall, id=hall_id)
    booking = get_object_or_404(Booking, id=booking_id, hall=hall)
    
    # التحقق من الصلاحيات
    if not request.user.is_staff:
        if not hasattr(request.user, 'hall_manager') or hall.manager != request.user.hall_manager:
            return JsonResponse({'success': False, 'error': 'غير مصرح لك'})
    
    if request.method == 'POST':
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')
        
        try:
            if action == 'approve':
                booking.status = 'approved'
                booking.admin_notes = admin_notes
                booking.save()
                return JsonResponse({'success': True, 'message': 'تم الموافقة على الحجز'})
            
            elif action == 'reject':
                booking.status = 'rejected'
                booking.admin_notes = admin_notes
                booking.save()
                return JsonResponse({'success': True, 'message': 'تم رفض الحجز'})
            
            elif action == 'cancel':
                booking.status = 'cancelled'
                booking.admin_notes = admin_notes
                booking.save()
                return JsonResponse({'success': True, 'message': 'تم إلغاء الحجز'})
            
            elif action == 'note':
                booking.admin_notes = admin_notes
                booking.save()
                return JsonResponse({'success': True, 'message': 'تم تحديث الملاحظة'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'طريقة غير صحيحة'})

@login_required
@user_passes_test(lambda u: u.is_staff or hasattr(u, 'hall_manager'))
def hall_reports(request, hall_id):
    """تقارير القاعة المفصلة"""
    hall = get_object_or_404(Hall, id=hall_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_staff:
        if not hasattr(request.user, 'hall_manager') or hall.manager != request.user.hall_manager:
            return redirect('hall_booking:home')
    
    from datetime import datetime, timedelta
    from django.db.models import Count, Sum, Q
    
    # فترة التقرير (آخر 30 يوم)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    # إحصائيات عامة
    total_bookings = Booking.objects.filter(hall=hall).count()
    approved_bookings = Booking.objects.filter(hall=hall, status='approved').count()
    pending_bookings = Booking.objects.filter(hall=hall, status='pending').count()
    rejected_bookings = Booking.objects.filter(hall=hall, status='rejected').count()
    
    # إحصائيات الفترة الأخيرة
    recent_bookings = Booking.objects.filter(
        hall=hall,
        created_at__date__range=[start_date, end_date]
    )
    
    # الإيرادات
    total_revenue = Booking.objects.filter(
        hall=hall, 
        status='approved'
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    recent_revenue = recent_bookings.filter(
        status='approved'
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    # أكثر الخدمات طلباً
    popular_services = BookingService.objects.filter(
        booking__hall=hall,
        booking__status='approved'
    ).values('service__name').annotate(
        count=Count('service')
    ).order_by('-count')[:5]
    
    # أكثر الوجبات طلباً
    popular_meals = BookingMeal.objects.filter(
        booking__hall=hall,
        booking__status='approved'
    ).values('meal__name').annotate(
        count=Count('meal')
    ).order_by('-count')[:5]
    
    # الحجوزات حسب الشهر (آخر 6 شهور)
    monthly_bookings = []
    for i in range(6):
        month_start = (datetime.now().replace(day=1) - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        count = Booking.objects.filter(
            hall=hall,
            start_datetime__date__range=[month_start.date(), month_end.date()],
            status='approved'
        ).count()
        
        monthly_bookings.append({
            'month': month_start.strftime('%Y-%m'),
            'count': count
        })
    
    context = {
        'hall': hall,
        'total_bookings': total_bookings,
        'approved_bookings': approved_bookings,
        'pending_bookings': pending_bookings,
        'rejected_bookings': rejected_bookings,
        'total_revenue': total_revenue,
        'recent_revenue': recent_revenue,
        'popular_services': popular_services,
        'popular_meals': popular_meals,
        'monthly_bookings': monthly_bookings,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'hall_booking/manager/hall_reports.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or hasattr(u, 'hall_manager'))
def booking_details_modal(request, booking_id):
    """عرض تفاصيل الحجز في نافذة منبثقة"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # التحقق من الصلاحيات
    if not request.user.is_staff:
        if not hasattr(request.user, 'hall_manager') or booking.hall.manager != request.user.hall_manager:
            return JsonResponse({'success': False, 'error': 'غير مصرح لك'})
    
    # جلب الخدمات والوجبات المرتبطة بالحجز
    booking_services = BookingService.objects.filter(booking=booking)
    booking_meals = BookingMeal.objects.filter(booking=booking)
    
    # حساب التكلفة التفصيلية
    services_cost = sum(bs.service.price * bs.quantity for bs in booking_services)
    meals_cost = sum(bm.meal.price_per_person * bm.quantity for bm in booking_meals)
    hall_cost = booking.hall.base_price
    
    context = {
        'booking': booking,
        'booking_services': booking_services,
        'booking_meals': booking_meals,
        'services_cost': services_cost,
        'meals_cost': meals_cost,
        'hall_cost': hall_cost,
    }
    
    # رندر القالب
    from django.template.loader import render_to_string
    html = render_to_string('hall_booking/manager/booking_details_modal.html', context, request=request)
    
    return JsonResponse({
        'success': True,
        'html': html
    })

# ==================== Admin Statistics Views ====================

@staff_member_required
def admin_statistics_view(request):
    """صفحة الإحصائيات مع الرسوم البيانية"""
    # إحصائيات عامة
    total_halls = Hall.objects.count()
    total_bookings = Booking.objects.count()
    total_revenue = Booking.objects.filter(status='completed').aggregate(total=Sum('total_price'))['total'] or 0
    
    # إحصائيات الحجوزات حسب الحالة
    booking_stats = {
        'pending': Booking.objects.filter(status='pending').count(),
        'approved': Booking.objects.filter(status='approved').count(),
        'completed': Booking.objects.filter(status='completed').count(),
        'cancelled': Booking.objects.filter(status='cancelled').count(),
        'rejected': Booking.objects.filter(status='rejected').count(),
    }
    
    # إحصائيات القاعات حسب الفئة
    category_stats = Category.objects.annotate(
        hall_count=Count('hall'),
        booking_count=Count('hall__bookings')
    ).values('name', 'hall_count', 'booking_count')
    
    # إحصائيات المحافظات
    governorate_stats = Governorate.objects.annotate(
        hall_count=Count('hall'),
        booking_count=Count('hall__bookings')
    ).values('name', 'hall_count', 'booking_count')
    
    # أفضل القاعات (الأكثر حجزاً)
    top_halls = Hall.objects.annotate(
        booking_count=Count('bookings')
    ).order_by('-booking_count')[:10]
    
    # إحصائيات الإيرادات الشهرية (آخر 12 شهر)
    monthly_revenue = []
    for i in range(12):
        date = timezone.now() - timedelta(days=30*i)
        revenue = Booking.objects.filter(
            status='completed',
            created_at__year=date.year,
            created_at__month=date.month
        ).aggregate(total=Sum('total_price'))['total'] or 0
        monthly_revenue.append({
            'month': date.strftime('%Y-%m'),
            'revenue': float(revenue)
        })
    
    context = {
        'title': 'الإحصائيات والتقارير',
        'total_halls': total_halls,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'booking_stats': booking_stats,
        'category_stats': list(category_stats),
        'governorate_stats': list(governorate_stats),
        'top_halls': top_halls,
        'monthly_revenue': monthly_revenue[::-1],  # عكس الترتيب للحصول على الأحدث أولاً
    }
    
    return render(request, 'admin/statistics.html', context)

@staff_member_required
def admin_bookings_chart_api(request):
    """API للحصول على بيانات مخطط الحجوزات"""
    # بيانات الحجوزات حسب الشهر (آخر 12 شهر)
    months = []
    bookings_data = []
    
    for i in range(12):
        date = timezone.now() - timedelta(days=30*i)
        month_name = date.strftime('%Y-%m')
        booking_count = Booking.objects.filter(
            created_at__year=date.year,
            created_at__month=date.month
        ).count()
        
        months.append(month_name)
        bookings_data.append(booking_count)
    
    return JsonResponse({
        'labels': months[::-1],
        'data': bookings_data[::-1]
    })

@staff_member_required
def admin_revenue_chart_api(request):
    """API للحصول على بيانات مخطط الإيرادات"""
    # بيانات الإيرادات حسب الشهر (آخر 12 شهر)
    months = []
    revenue_data = []
    
    for i in range(12):
        date = timezone.now() - timedelta(days=30*i)
        month_name = date.strftime('%Y-%m')
        revenue = Booking.objects.filter(
            status='completed',
            created_at__year=date.year,
            created_at__month=date.month
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        months.append(month_name)
        revenue_data.append(float(revenue))
    
    return JsonResponse({
        'labels': months[::-1],
        'data': revenue_data[::-1]
    })

@staff_member_required
def admin_halls_chart_api(request):
    """API للحصول على بيانات مخطط القاعات حسب الفئة"""
    categories = Category.objects.annotate(
        hall_count=Count('hall')
    ).values('name', 'hall_count')
    
    labels = [cat['name'] for cat in categories]
    data = [cat['hall_count'] for cat in categories]
    
    return JsonResponse({
        'labels': labels,
        'data': data
    })