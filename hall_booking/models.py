from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

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
    description = models.TextField(verbose_name="الوصف")
    capacity = models.PositiveIntegerField(verbose_name="السعة")
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر للساعة")
    image = models.ImageField(upload_to='halls/', verbose_name="الصورة")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name="الحالة")
    features = models.JSONField(default=list, verbose_name="المميزات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "قاعة"
        verbose_name_plural = "القاعات"
    
    def __str__(self):
        return self.name

# نموذج صور القاعة
class HallImage(models.Model):
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, related_name='images', verbose_name="القاعة")
    image = models.ImageField(upload_to='halls/gallery/', verbose_name="صورة إضافية")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الرفع")

    class Meta:
        verbose_name = "صورة قاعة"
        verbose_name_plural = "صور القاعات"

    def __str__(self):
        return f"صورة لـ {self.hall.name}"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'في الانتظار'),
        ('approved', 'موافق عليه'),
        ('rejected', 'مرفوض'),
        ('cancelled', 'ملغي'),
        ('completed', 'مكتمل'),
    ]
    
    booking_id = models.UUIDField(default=uuid.uuid4, editable=False, verbose_name="رقم الحجز")
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, verbose_name="القاعة")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings', verbose_name="المستخدم")
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