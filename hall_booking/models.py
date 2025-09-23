from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from django.utils.text import slugify

# نموذج المحافظات المصرية
class Governorate(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="اسم المحافظة")
    name_en = models.CharField(max_length=100, unique=True, verbose_name="الاسم بالإنجليزية")
    code = models.CharField(max_length=10, unique=True, verbose_name="كود المحافظة")
    region = models.CharField(max_length=50, verbose_name="المنطقة", choices=[
        ('cairo', 'القاهرة الكبرى'),
        ('delta', 'الدلتا'),
        ('canal', 'قناة السويس'),
        ('sinai', 'سيناء'),
        ('red_sea', 'البحر الأحمر'),
        ('upper_egypt', 'صعيد مصر'),
        ('new_valley', 'الوادي الجديد'),
    ])
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "محافظة"
        verbose_name_plural = "المحافظات"
        ordering = ['name']

    def __str__(self):
        return self.name

# نموذج المراكز والمدن
class City(models.Model):
    name = models.CharField(max_length=100, verbose_name="اسم المدينة/المركز")
    name_en = models.CharField(max_length=100, verbose_name="الاسم بالإنجليزية")
    governorate = models.ForeignKey(Governorate, on_delete=models.CASCADE, related_name='cities', verbose_name="المحافظة")
    is_capital = models.BooleanField(default=False, verbose_name="عاصمة المحافظة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "مدينة/مركز"
        verbose_name_plural = "المدن والمراكز"
        ordering = ['governorate', 'name']
        unique_together = ['name', 'governorate']

    def __str__(self):
        return f"{self.name} - {self.governorate.name}"

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="اسم الفئة")
    description = models.TextField(verbose_name="الوصف")
    icon = models.CharField(max_length=50, default="fas fa-building", verbose_name="الأيقونة")
    
    class Meta:
        verbose_name = "فئة القاعة"
        verbose_name_plural = "فئات القاعات"
    
    def __str__(self):
        return self.name

class Hall(models.Model):
    STATUS_CHOICES = [
        ('available', 'متاح'),
        ('maintenance', 'صيانة'),
        ('booked', 'محجوز'),
    ]

    name = models.CharField(max_length=200, verbose_name="اسم القاعة")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="الفئة")
    governorate = models.ForeignKey(Governorate, on_delete=models.CASCADE, verbose_name="المحافظة")
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="المدينة/المركز")
    address = models.TextField(verbose_name="العنوان التفصيلي", help_text="الشارع، الحي، معالم مميزة")
    description = models.TextField(verbose_name="الوصف")
    capacity = models.PositiveIntegerField(verbose_name="السعة")
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر للساعة")
    image = models.ImageField(upload_to='halls/', verbose_name="الصورة")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name="الحالة")
    features = models.JSONField(default=list, verbose_name="المميزات")
    # تم نقل العلاقات إلى النماذج الفرعية (HallService و HallMeal) كـ ForeignKey
    # معلومات إضافية
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم الهاتف")
    email = models.EmailField(blank=True, null=True, verbose_name="البريد الإلكتروني")
    website = models.URLField(blank=True, null=True, verbose_name="الموقع الإلكتروني")
    # إحداثيات الموقع
    latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True, verbose_name="خط العرض")
    longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True, verbose_name="خط الطول")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "قاعة"
        verbose_name_plural = "القاعات"

    def __str__(self):
        return self.name

    def get_full_address(self):
        """الحصول على العنوان الكامل"""
        return f"{self.address}, {self.city.name}, {self.governorate.name}"

    def get_location_display(self):
        """عرض الموقع بشكل مختصر"""
        return f"{self.city.name} - {self.governorate.name}"

    def get_manager(self):
        """الحصول على مدير القاعة"""
        try:
            return self.manager if hasattr(self, 'manager') and self.manager.is_active else None
        except:
            return None

    def has_manager(self):
        """تحقق من وجود مدير للقاعة"""
        return hasattr(self, 'manager') and self.manager.is_active

    def get_manager_name(self):
        """الحصول على اسم مدير القاعة"""
        manager = self.get_manager()
        if manager:
            return manager.user.get_full_name() or manager.user.username
        return "غير محدد"
        
    def get_thumbnail_preview(self):
        """عرض معاينة مصغرة للصورة"""
        if self.image and hasattr(self.image, 'url'):
            from django.utils.html import format_html
            return format_html('<img src="{}" style="max-height: 200px; max-width: 200px;" />', self.image.url)
        return "لا توجد صورة"
    get_thumbnail_preview.short_description = "معاينة الصورة"

# نموذج صور القاعة
class HallImage(models.Model):
    IMAGE_TYPE_CHOICES = [
        ('main', 'صورة رئيسية'),
        ('gallery', 'معرض الصور'),
        ('interior', 'صور داخلية'),
        ('exterior', 'صور خارجية'),
        ('facilities', 'صور المرافق'),
    ]

    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, related_name='images', verbose_name="القاعة")
    image = models.ImageField(upload_to='halls/gallery/', verbose_name="الصورة")
    image_type = models.CharField(
        max_length=20,
        choices=IMAGE_TYPE_CHOICES,
        default='gallery',
        verbose_name="نوع الصورة"
    )
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name="عنوان الصورة")
    description = models.TextField(blank=True, null=True, verbose_name="وصف الصورة")
    is_featured = models.BooleanField(default=False, verbose_name="صورة مميزة")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتيب العرض")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الرفع")

    class Meta:
        verbose_name = "صورة قاعة"
        verbose_name_plural = "صور القاعات"
        ordering = ['order', '-uploaded_at']

    def __str__(self):
        return f"صورة لـ {self.hall.name} - {self.get_image_type_display()}"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'في الانتظار'),
        ('approved', 'موافق عليه'),
        ('rejected', 'مرفوض'),
        ('cancelled', 'ملغي'),
        ('completed', 'مكتمل'),
    ]
    
    booking_id = models.UUIDField(default=uuid.uuid4, editable=False, verbose_name="رقم الحجز")
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, related_name='bookings', verbose_name="القاعة")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='user_bookings', verbose_name="المستخدم")
    customer_name = models.CharField(max_length=200, verbose_name="اسم العميل")
    customer_email = models.EmailField(verbose_name="البريد الإلكتروني")
    customer_phone = models.CharField(max_length=20, verbose_name="رقم الهاتف")
    event_title = models.CharField(max_length=200, verbose_name="عنوان الحدث")
    event_description = models.TextField(verbose_name="وصف الحدث")
    start_datetime = models.DateTimeField(verbose_name="تاريخ ووقت البداية")
    end_datetime = models.DateTimeField(verbose_name="تاريخ ووقت النهاية")
    attendees_count = models.PositiveIntegerField(verbose_name="عدد الحضور")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر الإجمالي")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="الحالة")
    admin_notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات الإدارة")
    is_admin_block = models.BooleanField(default=False, verbose_name="حجب إداري")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الطلب")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "حجز"
        verbose_name_plural = "الحجوزات"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer_name} - {self.hall.name} - {self.event_title}"
    
    def get_duration_hours(self):
        duration = self.end_datetime - self.start_datetime
        return duration.total_seconds() / 3600
    
    def calculate_total_price(self):
        # تأكد أن start_datetime و end_datetime هما datetime فعلاً
        start = self.start_datetime
        end = self.end_datetime
        if not (hasattr(start, 'hour') and hasattr(end, 'hour')):
            return 0
        hours = self.get_duration_hours()
        # إذا كان الحجز ليوم كامل (أي الوقت 00:00:00)
        if start.hour == 0 and end.hour == 0 and hours % 24 == 0:
            days = int(hours // 24)
            return float(self.hall.price_per_hour) * 24 * days  # noqa
        return float(self.hall.price_per_hour) * hours  # noqa

# نموذج مدير القاعة
class HallManager(models.Model):
    PERMISSION_CHOICES = [
        ('view', 'عرض فقط'),
        ('manage', 'إدارة كاملة'),
        ('schedule', 'إدارة الجدولة فقط'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="المستخدم")
    hall = models.OneToOneField(Hall, on_delete=models.CASCADE, related_name='manager', verbose_name="القاعة")
    permission_level = models.CharField(
        max_length=20,
        choices=PERMISSION_CHOICES,
        default='manage',
        verbose_name="مستوى الصلاحية"
    )
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التعيين")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")

    class Meta:
        verbose_name = "مدير قاعة"
        verbose_name_plural = "مديري القاعات"
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.hall.name}"

    def can_manage_bookings(self):
        """تحقق من إمكانية إدارة الحجوزات"""
        return self.permission_level in ['manage', 'schedule'] and self.is_active

    def can_edit_hall(self):
        """تحقق من إمكانية تعديل بيانات القاعة"""
        return self.permission_level == 'manage' and self.is_active

class HallService(models.Model):
    """خدمات إضافية خاصة بكل قاعة"""
    hall = models.ForeignKey('Hall', on_delete=models.CASCADE, related_name='hall_services', verbose_name="القاعة")
    name = models.CharField(max_length=100, verbose_name="اسم الخدمة")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    is_available = models.BooleanField(default=True, verbose_name="متاحة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "خدمة القاعة"
        verbose_name_plural = "خدمات القاعات"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.price} ج.م"


class HallMeal(models.Model):
    """وجبات طعام خاصة بكل قاعة"""
    MEAL_TYPES = [
        ('breakfast', 'إفطار'),
        ('lunch', 'غداء'),
        ('dinner', 'عشاء'),
        ('snack', 'سناك'),
        ('buffet', 'بوفيه مفتوح'),
    ]
    
    hall = models.ForeignKey('Hall', on_delete=models.CASCADE, related_name='hall_meals', verbose_name="القاعة")
    name = models.CharField(max_length=100, verbose_name="اسم الوجبة")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES, verbose_name="نوع الوجبة")
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر للفرد")
    is_vegetarian = models.BooleanField(default=False, verbose_name="نباتية")
    is_available = models.BooleanField(default=True, verbose_name="متاحة")
    min_order = models.PositiveIntegerField(default=1, verbose_name="الحد الأدنى للطلب")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "وجبة القاعة"
        verbose_name_plural = "وجبات القاعات"
        ordering = ['meal_type', 'name']

    def __str__(self):
        return f"{self.get_meal_type_display()} - {self.name}"


class BookingService(models.Model):
    """خدمات إضافية تم اختيارها في الحجز"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booking_services', verbose_name="الحجز")
    service = models.ForeignKey('HallService', on_delete=models.CASCADE, verbose_name="الخدمة")
    quantity = models.PositiveIntegerField(default=1, verbose_name="الكمية")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    
    class Meta:
        unique_together = ['booking', 'service']  # منع تكرار نفس الخدمة في الحجز
        verbose_name_plural = "خدمات الحجوزات"

    def __str__(self):
        return f"{self.service.name} - {self.booking.booking_id}"


class BookingMeal(models.Model):
    """وجبات طعام تم اختيارها في الحجز"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booking_meals', verbose_name="الحجز")
    meal = models.ForeignKey('HallMeal', on_delete=models.CASCADE, verbose_name="الوجبة")
    quantity = models.PositiveIntegerField(verbose_name="العدد")
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر للفرد")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر الإجمالي")
    serving_time = models.TimeField(verbose_name="موعد التقديم")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        unique_together = ['booking', 'meal', 'serving_time']  # منع تكرار نفس الوجبة في نفس الوقت

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.price_per_person
        super().save(*args, **kwargs)

        return f"{self.meal.name} - {self.booking.booking_id}"


class Contact(models.Model):
    name = models.CharField(max_length=200, verbose_name="الاسم")
    email = models.EmailField(verbose_name="البريد الإلكتروني")
    phone = models.CharField(max_length=20, verbose_name="رقم الهاتف")
    subject = models.CharField(max_length=200, verbose_name="الموضوع")
    message = models.TextField(verbose_name="الرسالة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإرسال")
    is_read = models.BooleanField(default=False, verbose_name="مقروءة")

    class Meta:
        verbose_name = "رسالة تواصل"
        verbose_name_plural = "رسائل التواصل"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('booking_approved', 'تم الموافقة على الحجز'),
        ('booking_rejected', 'تم رفض الحجز'),
        ('booking_cancelled', 'تم إلغاء الحجز'),
        ('booking_completed', 'تم إكمال الحجز'),
        ('booking_reminder', 'تذكير بالحجز'),
        ('general', 'إشعار عام'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name="المستخدم")
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True, verbose_name="الحجز")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, verbose_name="نوع الإشعار")
    title = models.CharField(max_length=200, verbose_name="العنوان")
    message = models.TextField(verbose_name="الرسالة")
    is_read = models.BooleanField(default=False, verbose_name="مقروء")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "إشعار"
        verbose_name_plural = "الإشعارات"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def mark_as_read(self):
        """تحديد الإشعار كمقروء"""
        self.is_read = True
        self.save()

# إشارات لإنشاء الإشعارات تلقائياً
@receiver(post_save, sender=Booking)
def create_booking_notification(sender, instance, created, **kwargs):
    """إنشاء إشعار عند تغيير حالة الحجز"""
    if not created and instance.user:  # فقط عند التحديث وليس الإنشاء
        # التحقق من تغيير الحالة
        if hasattr(instance, '_state') and instance._state.adding is False:
            try:
                old_instance = Booking.objects.get(pk=instance.pk)
                if old_instance.status != instance.status:
                    # إنشاء الإشعار حسب الحالة الجديدة
                    notification_data = get_notification_data(instance.status, instance)
                    if notification_data:
                        Notification.objects.create(
                            user=instance.user,
                            booking=instance,
                            notification_type=notification_data['type'],
                            title=notification_data['title'],
                            message=notification_data['message']
                        )
            except Booking.DoesNotExist:
                pass

def get_notification_data(status, booking):
    """الحصول على بيانات الإشعار حسب حالة الحجز"""
    status_messages = {
        'approved': {
            'type': 'booking_approved',
            'title': 'تم الموافقة على حجزك!',
            'message': f'تم الموافقة على حجز "{booking.event_title}" في قاعة {booking.hall.name}. سيتم التواصل معك قريباً لتأكيد التفاصيل.'
        },
        'rejected': {
            'type': 'booking_rejected',
            'title': 'تم رفض حجزك',
            'message': f'نأسف لإبلاغك أنه تم رفض حجز "{booking.event_title}" في قاعة {booking.hall.name}. يرجى التواصل معنا للمزيد من التفاصيل.'
        },
        'completed': {
            'type': 'booking_completed',
            'title': 'تم إكمال حجزك بنجاح',
            'message': f'تم إكمال حجز "{booking.event_title}" في قاعة {booking.hall.name} بنجاح. نشكرك لاختيارك خدماتنا!'
        },
        'cancelled': {
            'type': 'booking_cancelled',
            'title': 'تم إلغاء حجزك',
            'message': f'تم إلغاء حجز "{booking.event_title}" في قاعة {booking.hall.name}.'
        }
    }
    return status_messages.get(status)

class SiteSettings(models.Model):
    """إعدادات الموقع الديناميكية"""
    site_name = models.CharField(max_length=200, default="a7jazili", verbose_name="اسم الموقع")
    site_name_ar = models.CharField(max_length=200, default="احجزلي", verbose_name="اسم الموقع بالعربية")
    logo = models.ImageField(upload_to='site_logo/', blank=True, null=True, verbose_name="شعار الموقع")
    favicon = models.ImageField(upload_to='site_icons/', blank=True, null=True, verbose_name="أيقونة الموقع")
    
    # معلومات التواصل
    phone_primary = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف الأساسي")
    phone_secondary = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف الثانوي")
    email_primary = models.EmailField(blank=True, verbose_name="البريد الإلكتروني الأساسي")
    email_secondary = models.EmailField(blank=True, verbose_name="البريد الإلكتروني الثانوي")
    
    # العنوان
    address = models.TextField(blank=True, verbose_name="العنوان الكامل")
    city = models.CharField(max_length=100, blank=True, verbose_name="المدينة")
    country = models.CharField(max_length=100, default="مصر", verbose_name="البلد")
    
    # وسائل التواصل الاجتماعي
    facebook_url = models.URLField(blank=True, verbose_name="رابط فيسبوك")
    twitter_url = models.URLField(blank=True, verbose_name="رابط تويتر")
    instagram_url = models.URLField(blank=True, verbose_name="رابط انستجرام")
    linkedin_url = models.URLField(blank=True, verbose_name="رابط لينكد إن")
    youtube_url = models.URLField(blank=True, verbose_name="رابط يوتيوب")
    whatsapp_number = models.CharField(max_length=20, blank=True, verbose_name="رقم واتساب")
    telegram_url = models.URLField(blank=True, verbose_name="رابط تليجرام")
    
    # إعدادات إضافية
    footer_text = models.TextField(blank=True, default="جميع الحقوق محفوظة", verbose_name="نص الفوتر")
    copyright_year = models.IntegerField(default=2024, verbose_name="سنة حقوق النشر")
    meta_description = models.TextField(blank=True, verbose_name="وصف الموقع (SEO)")
    meta_keywords = models.TextField(blank=True, verbose_name="كلمات مفتاحية (SEO)")
    
    # معلومات إضافية
    working_hours = models.CharField(max_length=200, blank=True, verbose_name="ساعات العمل")
    support_email = models.EmailField(blank=True, verbose_name="بريد الدعم الفني")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "إعدادات الموقع"
        verbose_name_plural = "إعدادات الموقع"
    
    def __str__(self):
        return f"إعدادات {self.site_name_ar or self.site_name}"
    
    def save(self, *args, **kwargs):
        # التأكد من وجود إعداد واحد فقط
        if not self.pk and SiteSettings.objects.exists():
            raise ValueError("يمكن وجود إعداد واحد فقط للموقع")
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """الحصول على إعدادات الموقع"""
        settings, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'site_name': 'a7jazili',
                'site_name_ar': 'احجزلي',
                'phone_primary': '+20123456789',
                'email_primary': 'info@a7jazili.com',
                'address': 'القاهرة، مصر',
            }
        )
        return settings