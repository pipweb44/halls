from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from datetime import datetime, timedelta
import json
from .models import Hall, Category, Booking, Contact, HallManager
from .forms import BookingForm, ContactForm, HallForm
from django.contrib.auth.models import User
from django.db.models import Sum
import calendar
from django.core.paginator import Paginator
from django.contrib.auth import update_session_auth_hash

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
    featured_halls = Hall.objects.filter(status='available')[:6]
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
    search_query = request.GET.get('search')
    
    halls = Hall.objects.filter(status='available')
    
    if category_id:
        halls = halls.filter(category_id=category_id)
    
    if search_query:
        halls = halls.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    categories = Category.objects.all()
    
    context = {
        'halls': halls,
        'categories': categories,
        'selected_category': category_id,
        'search_query': search_query,
    }
    return render(request, 'hall_booking/halls_list.html', context)

def hall_detail(request, hall_id):
    """تفاصيل القاعة"""
    hall = get_object_or_404(Hall, id=hall_id)
    
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
                'selected_date': selected_date,
                'bookings': bookings,
            }
        else:
            context = {'hall': hall}
    else:
        context = {'hall': hall}
    
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

def dashboard(request):
    """لوحة الإدارة المتقدمة"""
    if not request.user.is_staff:
        return redirect('hall_booking:home')
    total_bookings = Booking.objects.count()
    pending_bookings = Booking.objects.filter(status='pending').count()
    total_halls = Hall.objects.count()
    available_halls = Hall.objects.filter(status='available').count()
    total_users = User.objects.count()
    total_revenue = Booking.objects.filter(status='completed').aggregate(total=Sum('total_price'))['total'] or 0
    # بيانات الرسم البياني: عدد الحجوزات لكل شهر في آخر 12 شهر
    from django.utils import timezone
    import calendar
    now = timezone.now()
    monthly_bookings = []
    month_labels = []
    for i in range(11, -1, -1):
        month = (now.month - i - 1) % 12 + 1
        year = now.year if now.month - i > 0 else now.year - 1
        count = Booking.objects.filter(created_at__year=year, created_at__month=month).count()
        monthly_bookings.append(count)
        month_labels.append(calendar.month_name[month])
    context = {
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'total_halls': total_halls,
        'available_halls': available_halls,
        'total_users': total_users,
        'total_revenue': total_revenue,
        'monthly_bookings': monthly_bookings,
        'month_labels': month_labels,
    }
    return render(request, 'hall_booking/dashboard.html', context)

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
    return render(request, 'hall_booking/admin/halls_list.html', context)

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
    return render(request, 'hall_booking/admin/hall_form.html', context)

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
    return render(request, 'hall_booking/admin/hall_form.html', context)

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
    return render(request, 'hall_booking/admin/hall_confirm_delete.html', context)

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
    return render(request, 'hall_booking/admin/bookings_list.html', context)

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
    return render(request, 'hall_booking/admin/contacts_list.html', context)

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
                return redirect('hall_booking:dashboard')
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
                        return redirect('hall_booking:dashboard')
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
        # For now, we'll just redirect to dashboard
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