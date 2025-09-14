from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import uuid
from django.utils.text import slugify
from django.core.exceptions import ValidationError

# Move the Meal model to the top to resolve circular imports

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
        ('north_upper', 'صعيد مصر العليا'),
        ('south_upper', 'صعيد مصر السفلى'),
        ('north_coast', 'الساحل الشمالي'),
        ('red_sea', 'البحر الأحمر'),
        ('new_valley', 'الوادي الجديد'),
    ])
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

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
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "مدينة/مركز"
        verbose_name_plural = "المدن والمراكز"
        ordering = ['name']
        unique_together = ['name', 'governorate']

    def __str__(self):
        return f"{self.name} - {self.governorate.name}"


# نموذج الفئات
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="اسم الفئة")
    description = models.TextField(verbose_name="الوصف")
    icon = models.CharField(max_length=50, default="fas fa-building", verbose_name="الأيقونة")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "فئة"
        verbose_name_plural = "الفئات"
        ordering = ['name']

    def __str__(self):
        return self.name


# نموذج القاعات
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
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم الهاتف")
    email = models.EmailField(blank=True, null=True, verbose_name="البريد الإلكتروني")
    website = models.URLField(blank=True, null=True, verbose_name="الموقع الإلكتروني")
    latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True, verbose_name="خط العرض")
    longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True, verbose_name="خط الطول")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "قاعة"
        verbose_name_plural = "القاعات"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_full_address(self):
        """الحصول على العنوان الكامل"""
        return f"{self.address}، {self.city.name}، {self.governorate.name}"

    def get_location_display(self):
        """عرض الموقع بشكل مختصر"""
        return f"{self.city.name} - {self.governorate.name}"

    def get_manager(self):
        """الحصول على مدير القاعة"""
        try:
            return self.manager
        except HallManager.DoesNotExist:
            return None

    def has_manager(self):
        """تحقق من وجود مدير للقاعة"""
        return hasattr(self, 'manager')

    def get_manager_name(self):
        """الحصول على اسم مدير القاعة"""
        if self.has_manager():
            return self.manager.user.get_full_name() or self.manager.user.username
        return "لا يوجد مدير"


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
        verbose_name = "صورة القاعة"
        verbose_name_plural = "صور القاعات"
        ordering = ['order', '-uploaded_at']

    def __str__(self):
        return f"{self.hall.name} - {self.get_image_type_display()}"


# نموذج الحجوزات
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
        ordering = ['-start_datetime']

    def __str__(self):
        return f"{self.event_title} - {self.hall.name}"

    def get_duration_hours(self):
        """حساب مدة الحجز بالساعات"""
        duration = self.end_datetime - self.start_datetime
        return round(duration.total_seconds() / 3600, 2)

    def calculate_total_price(self):
        """حساب السعر الإجمالي للحجز"""
        duration_hours = self.get_duration_hours()
        return round(float(duration_hours) * float(self.hall.price_per_hour), 2)

    def save(self, *args, **kwargs):
        """حفظ الحجز مع حساب السعر الإجمالي"""
        if not self.pk:  # إذا كان الحجز جديداً
            self.total_price = self.calculate_total_price()
        super().save(*args, **kwargs)


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
        verbose_name = "مدير القاعة"
        verbose_name_plural = "مديرو القاعات"
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.user.username} - {self.hall.name}"

    def can_manage_bookings(self):
        """تحقق من إمكانية إدارة الحجوزات"""
        return self.permission_level in ['manage', 'schedule']

    def can_edit_hall(self):
        """تحقق من إمكانية تعديل بيانات القاعة"""
        return self.permission_level == 'manage'


# نموذج رسائل الاتصال
class Contact(models.Model):
    name = models.CharField(max_length=200, verbose_name="الاسم")
    email = models.EmailField(verbose_name="البريد الإلكتروني")
    phone = models.CharField(max_length=20, verbose_name="رقم الهاتف")
    subject = models.CharField(max_length=200, verbose_name="الموضوع")
    message = models.TextField(verbose_name="الرسالة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإرسال")
    is_read = models.BooleanField(default=False, verbose_name="مقروءة")

    class Meta:
        verbose_name = "رسالة اتصال"
        verbose_name_plural = "رسائل الاتصال"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"


# نموذج الإشعارات
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


# ===========================================
# نماذج إدارة الوجبات والخدمات
# ===========================================
# Note: Meal-related models have been moved to the meal_system app

class IngredientImage(models.Model):
    """نموذج صور المكونات"""
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE, related_name='images', verbose_name="المكون")
    image = models.ImageField(upload_to='ingredients/', verbose_name="الصورة")
    caption = models.CharField(max_length=200, blank=True, null=True, verbose_name="تعليق")
    is_primary = models.BooleanField(default=False, verbose_name="صورة رئيسية")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتيب العرض")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "صورة المكون"
        verbose_name_plural = "صور المكونات"
        ordering = ['order', '-is_primary', 'created_at']

    def __str__(self):
        return f"صورة لـ {self.ingredient.name}"

    def save(self, *args, **kwargs):
        # Ensure only one primary image per ingredient
        if self.is_primary:
            IngredientImage.objects.filter(ingredient=self.ingredient, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class Ingredient(models.Model):
    """نموذج المكونات المستخدمة في تحضير الوجبات"""
    name = models.CharField(max_length=100, verbose_name="اسم المكون")
    description = models.TextField(blank=True, null=True, verbose_name="وصف المكون")
    is_allergen = models.BooleanField(default=False, verbose_name="مسبب للحساسية")
    image = models.ImageField(upload_to='ingredients/main/', blank=True, null=True, verbose_name="الصورة الرئيسية")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "مكون"
        verbose_name_plural = "المكونات"
        ordering = ['name']

    def __str__(self):
        return self.name


class MealImage(models.Model):
    """نموذج صور الوجبات"""
    meal = models.ForeignKey('Meal', on_delete=models.CASCADE, related_name='meal_images', verbose_name="الوجبة")
    image = models.ImageField(upload_to='meals/gallery/', verbose_name="الصورة")
    caption = models.CharField(max_length=200, blank=True, null=True, verbose_name="تعليق")
    is_primary = models.BooleanField(default=False, verbose_name="صورة رئيسية")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتيب العرض")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "صورة الوجبة"
        verbose_name_plural = "صور الوجبات"
        ordering = ['order', '-is_primary', 'created_at']

    def __str__(self):
        return f"صورة لـ {self.meal.name}"

    def save(self, *args, **kwargs):
        # Ensure only one primary image per meal
        if self.is_primary:
            MealImage.objects.filter(meal=self.meal, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class Meal(models.Model):
    """نموذج الوجبات المتاحة في القاعة"""
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'إفطار'),
        ('lunch', 'غداء'),
        ('dinner', 'عشاء'),
        ('snack', 'سناك'),
        ('buffet', 'بوفيه'),
        ('custom', 'مخصص'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="اسم الوجبة")
    description = models.TextField(verbose_name="وصف الوجبة")
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES, verbose_name="نوع الوجبة")
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر للفرد")
    is_available = models.BooleanField(default=True, verbose_name="متاح للطلب")
    preparation_time = models.PositiveIntegerField(help_text="مدة التحضير بالدقائق", verbose_name="مدة التحضير")
    ingredients = models.ManyToManyField('Ingredient', through='MealIngredient', verbose_name="المكونات")
    image = models.ImageField(upload_to='meals/main/', blank=True, null=True, verbose_name="الصورة الرئيسية")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "وجبة"
        verbose_name_plural = "الوجبات"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_meal_type_display()})"


class MealIngredient(models.Model):
    """نموذج علاقة بين الوجبة ومكوناتها"""
    meal = models.ForeignKey('Meal', on_delete=models.CASCADE, verbose_name="الوجبة")
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE, verbose_name="المكون")
    quantity = models.CharField(max_length=50, verbose_name="الكمية")
    is_optional = models.BooleanField(default=False, verbose_name="اختياري")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات إضافية")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "مكون الوجبة"
        verbose_name_plural = "مكونات الوجبات"
        unique_together = ['meal', 'ingredient']

    def __str__(self):
        return f"{self.meal.name} - {self.ingredient.name}"


class HallMeal(models.Model):
    """نموذج ربط الوجبات بالقاعات مع إمكانية تخصيص السعر"""
    hall = models.ForeignKey('Hall', on_delete=models.CASCADE, related_name='hall_meals', verbose_name="القاعة")
    meal = models.ForeignKey('Meal', on_delete=models.CASCADE, verbose_name="الوجبة")
    is_available = models.BooleanField(default=True, verbose_name="متاح")
    extra_notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات إضافية")
    price_override = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="تعديل السعر (اختياري)",
        help_text="اتركه فارغاً لاستخدام السعر الافتراضي للوجبة"
    )
    min_order = models.PositiveIntegerField(default=1, verbose_name="الحد الأدنى للطلب")
    max_order = models.PositiveIntegerField(null=True, blank=True, verbose_name="الحد الأقصى للطلب")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "وجبة القاعة"
        verbose_name_plural = "وجبات القاعات"
        unique_together = ['hall', 'meal']

    def __str__(self):
        return f"{self.meal.name} - {self.hall.name}"
    
    def get_price(self):
        """الحصول على سعر الوجبة مع مراعاة السعر المعدل"""
        return self.price_override if self.price_override is not None else self.meal.price_per_person


class AdditionalService(models.Model):
    """نموذج الخدمات الإضافية التي يمكن إضافتها للحجز"""
    SERVICE_TYPE_CHOICES = [
        ('equipment', 'معدات'),
        ('staff', 'طاقم عمل'),
        ('decoration', 'ديكور'),
        ('entertainment', 'ترفيه'),
        ('photography', 'تصوير'),
        ('other', 'أخرى'),
    ]
    
    UNIT_CHOICES = [
        ('hour', 'ساعة'),
        ('day', 'يوم'),
        ('event', 'للفعالية'),
        ('person', 'للفرد'),
        ('unit', 'قطعة'),
    ]
    
    hall = models.ForeignKey('Hall', on_delete=models.CASCADE, related_name='additional_services', verbose_name="القاعة")
    name = models.CharField(max_length=200, verbose_name="اسم الخدمة")
    description = models.TextField(verbose_name="وصف الخدمة")
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES, verbose_name="نوع الخدمة")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    price_unit = models.CharField(max_length=10, choices=UNIT_CHOICES, verbose_name="وحدة السعر")
    is_available = models.BooleanField(default=True, verbose_name="متاح")
    requires_approval = models.BooleanField(default=False, verbose_name="يتطلب موافقة")
    max_quantity = models.PositiveIntegerField(null=True, blank=True, verbose_name="الحد الأقصى للكمية")
    image = models.ImageField(upload_to='services/', blank=True, null=True, verbose_name="صورة الخدمة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "خدمة إضافية"
        verbose_name_plural = "الخدمات الإضافية"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.hall.name}"


class BookingService(models.Model):
    """نموذج تفاصيل الخدمات المطلوبة في الحجز"""
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='booking_services', verbose_name="الحجز")
    service = models.ForeignKey('AdditionalService', on_delete=models.CASCADE, verbose_name="الخدمة")
    quantity = models.PositiveIntegerField(default=1, verbose_name="الكمية")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "خدمة الحجز"
        verbose_name_plural = "خدمات الحجز"

    def __str__(self):
        return f"{self.service.name} - {self.booking.event_title}"


class BookingMeal(models.Model):
    """نموذج تفاصيل الوجبات المطلوبة في الحجز"""
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='booking_meals', verbose_name="الحجز")
    hall_meal = models.ForeignKey('HallMeal', on_delete=models.CASCADE, verbose_name="وجبة القاعة")
    quantity = models.PositiveIntegerField(default=1, verbose_name="الكمية")
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="سعر الوحدة")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر الإجمالي")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات خاصة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "وجبة الحجز"
        verbose_name_plural = "وجبات الحجز"

    def __str__(self):
        return f"{self.hall_meal.meal.name} - {self.booking.event_title}"
    
    def save(self, *args, **kwargs):
        """حساب السعر الإجمالي تلقائياً"""
        if not self.price_per_unit and self.hall_meal:
            self.price_per_unit = self.hall_meal.get_price()
        self.total_price = self.quantity * (self.price_per_unit or 0)
        super().save(*args, **kwargs)


# ===========================================
# إشارات لإنشاء الإشعارات تلقائياً
# ===========================================
@receiver(post_save, sender=Booking)
def create_booking_notification(sender, instance, created, **kwargs):
    """إنشاء إشعار عند تغيير حالة الحجز"""
    if not created and 'status' in instance.tracker.changed():
        try:
            # الحصول على بيانات الإشعار المناسبة
            notification_data = get_notification_data(instance.status, instance)
            
            # إنشاء الإشعار للمستخدم
            if instance.user:
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
            'message': f'تمت الموافقة على حجز "{booking.event_title}" في قاعة {booking.hall.name}. سيتم التواصل معك قريباً لتأكيد التفاصيل.'
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
            'message': f'تم إلغاء حجز "{booking.event_title}" في قاعة {booking.hall.name} بناءً على طلبك.'
        },
        'pending': {
            'type': 'booking_reminder',
            'title': 'تذكير بالحجز القادم',
            'message': f'تذكير بموعد حجزك القادم "{booking.event_title}" في قاعة {booking.hall.name} بتاريخ {booking.start_datetime.strftime("%Y-%m-%d %H:%M")}.'
        },
    }
    
    return status_messages.get(status, {
        'type': 'general',
        'title': 'تحديث حالة الحجز',
        'message': f'تم تحديث حالة حجزك "{booking.event_title}" إلى {booking.get_status_display()}. '
                  f'يرجى مراجعة تفاصيل الحجز للمزيد من المعلومات.'
    })
