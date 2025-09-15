from django.db import models
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class HallSpecificManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_available=True)

class HallMealCategory(models.Model):
    """تصنيفات الوجبات الخاصة بكل قاعة"""
    hall = models.ForeignKey('hall_booking.Hall', on_delete=models.CASCADE, related_name='meal_categories', verbose_name="القاعة")
    name = models.CharField(max_length=200, verbose_name="اسم التصنيف")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    image = models.ImageField(upload_to='hall_meal_categories/', blank=True, null=True, verbose_name="صورة التصنيف")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتيب العرض")
    min_selections = models.PositiveIntegerField(default=0, verbose_name="الحد الأدنى للاختيار")
    max_selections = models.PositiveIntegerField(null=True, blank=True, verbose_name="الحد الأقصى للاختيار")
    is_required = models.BooleanField(default=False, verbose_name="إجباري")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    objects = models.Manager()
    available = HallSpecificManager()

    class Meta:
        verbose_name = "تصنيف وجبات القاعة"
        verbose_name_plural = "تصنيفات وجبات القاعات"
        ordering = ['hall', 'order', 'name']
        unique_together = ['hall', 'name']
        
    def meals_count(self):
        return self.meals.count()
    meals_count.short_description = 'عدد الوجبات'

    def __str__(self):
        return f"{self.name} - {self.hall.name}"

    def image_tag(self):
        if self.image:
            return format_html('<img src="{}" style="max-height: 50px;" />'.format(self.image.url))
        return ""
    image_tag.short_description = 'صورة مصغرة'
    image_tag.allow_tags = True

class HallMealComponent(models.Model):
    """مكونات الوجبات الخاصة بكل قاعة"""
    hall = models.ForeignKey('hall_booking.Hall', on_delete=models.CASCADE, related_name='meal_components', verbose_name="القاعة")
    name = models.CharField(max_length=200, verbose_name="اسم المكون")
    component_type = models.CharField(max_length=20, choices=[
        ('main', 'طبق رئيسي'),
        ('side', 'طبق جانبي'),
        ('salad', 'سلطة'),
        ('sauce', 'صوص'),
        ('bread', 'خبز'),
        ('drink', 'مشروب'),
        ('dessert', 'حلويات'),
        ('other', 'أخرى'),
    ], default='main', verbose_name="نوع المكون")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    is_available = models.BooleanField(default=True, verbose_name="متوفر")
    image = models.ImageField(upload_to='hall_components/', blank=True, null=True, verbose_name="صورة المكون")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    objects = models.Manager()
    available = HallSpecificManager()

    class Meta:
        verbose_name = "مكون وجبة القاعة"
        verbose_name_plural = "مكونات وجبات القاعات"
        ordering = ['name']
        unique_together = ['hall', 'name']

    def __str__(self):
        return f"{self.name} - {self.hall.name}"

    def image_tag(self):
        if self.image:
            return format_html('<img src="{}" style="max-height: 50px;" />'.format(self.image.url))
        return ""
    image_tag.short_description = 'صورة مصغرة'
    image_tag.allow_tags = True

class HallMealComponentItem(models.Model):
    """مكونات كل وجبة قاعة"""
    meal = models.ForeignKey('HallMeal', on_delete=models.CASCADE, related_name='meal_components', verbose_name="الوجبة")
    component = models.ForeignKey('HallMealComponent', on_delete=models.CASCADE, verbose_name="المكون")
    quantity = models.PositiveIntegerField(default=1, verbose_name="الكمية")
    is_optional = models.BooleanField(default=False, verbose_name="اختياري")
    additional_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="سعر إضافي")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتيب العرض")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "مكون الوجبة"
        verbose_name_plural = "مكونات الوجبات"
        ordering = ['order', 'component__name']
        unique_together = ['meal', 'component']

    def __str__(self):
        return f"{self.component.name} - {self.meal.name}"

    def total_price(self):
        return (self.component.price + self.additional_price) * self.quantity
    total_price.short_description = 'السعر الإجمالي'

class HallMeal(models.Model):
    """الوجبات الخاصة بكل قاعة"""
    hall = models.ForeignKey('hall_booking.Hall', on_delete=models.CASCADE, related_name='meals', verbose_name="القاعة")
    category = models.ForeignKey(
            'HallMealCategory',
            on_delete=models.PROTECT,
            related_name='meals',
            verbose_name="التصنيف",
            help_text="يجب اختيار تصنيف موجود مسبقاً"
        )
    name = models.CharField(max_length=200, verbose_name="اسم الوجبة")
    description = models.TextField(verbose_name="وصف الوجبة")
    base_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر الأساسي")
    is_available = models.BooleanField(default=True, verbose_name="متاح")
    image = models.ImageField(upload_to='hall_meals/', blank=True, null=True, verbose_name="صورة الوجبة")
    min_components = models.PositiveIntegerField(default=0, verbose_name="الحد الأدنى للمكونات")
    max_components = models.PositiveIntegerField(null=True, blank=True, verbose_name="الحد الأقصى للمكونات")
    order_in_category = models.PositiveIntegerField(default=0, verbose_name="ترتيب العرض في التصنيف")
    components = models.ManyToManyField(
        'HallMealComponent',
        through='HallMealComponentItem',
        through_fields=('meal', 'component'),
        related_name='meals',
        verbose_name="المكونات"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    objects = models.Manager()
    available = HallSpecificManager()

    class Meta:
        verbose_name = "وجبة قاعة"
        verbose_name_plural = "وجبات القاعات"
        ordering = ['category', 'order_in_category', 'name']
        unique_together = ['hall', 'category', 'name']

    def clean(self):
        if self.category and self.category.hall_id != self.hall_id:
            raise ValidationError({'category': 'يجب أن يكون التصنيف تابعاً لنفس قاعة الوجبة'})

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.pk:
            last_order = HallMeal.objects.filter(
                hall=self.hall,
                category=self.category
            ).order_by('-order_in_category').first()
            self.order_in_category = (last_order.order_in_category + 1) if last_order else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.hall.name}"

    def image_tag(self):
        if self.image:
            return format_html('<img src="{}" style="max-height: 50px;" />'.format(self.image.url))
        return ""
    image_tag.short_description = 'صورة مصغرة'
    image_tag.allow_tags = True
