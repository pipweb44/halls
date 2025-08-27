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
from .models import Hall, Category, Booking, Contact
from .forms import BookingForm, ContactForm, HallForm
from django.contrib.auth.models import User
from django.db.models import Sum
import calendar
from django.core.paginator import Paginator
from django.contrib.auth import update_session_auth_hash

def is_admin(user):
    return user.is_staff

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
            booking.total_price = booking.calculate_total_price()
            booking.save()
            
            messages.success(request, 'تم إرسال طلب الحجز بنجاح! سنتواصل معك قريباً.')
            return redirect('hall_booking:hall_detail', hall_id=hall_id)
    else:
        form = BookingForm()
    
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
    
    # جلب طلبات الحجز الخاصة بالمستخدم بناءً على بريده الإلكتروني
    user_email = request.user.email
    user_bookings = Booking.objects.filter(customer_email=user_email).order_by('-created_at') if user_email else Booking.objects.none()
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
    return render(request, 'hall_booking/admin/user_detail.html', {'user_obj': user}) 