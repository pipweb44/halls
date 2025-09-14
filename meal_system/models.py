from django.db import models
from django.utils.html import format_html

class MealCategory(models.Model):
    """نموذج أصناف الوجبات الرئيسية"""
    name = models.CharField(max_length=200, verbose_name="اسم الصنف")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    image = models.ImageField(upload_to='meal_categories/', blank=True, null=True, verbose_name="صورة الصنف")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتيب العرض")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "صنف الوجبات"
        verbose_name_plural = "أصناف الوجبات"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def image_tag(self):
        if self.image:
            return format_html('<img src="{}" style="max-height: 50px;" />'.format(self.image.url))
        return ""
    image_tag.short_description = 'صورة مصغرة'
    image_tag.allow_tags = True


class MealItem(models.Model):
    """نموذج الوجبات الرئيسية"""
    category = models.ForeignKey(MealCategory, on_delete=models.CASCADE, related_name='meals', verbose_name="الصنف")
    name = models.CharField(max_length=200, verbose_name="اسم الوجبة")
    description = models.TextField(verbose_name="وصف الوجبة")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    is_available = models.BooleanField(default=True, verbose_name="متاح")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتيب العرض")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "وجبة"
        verbose_name_plural = "الوجبات"
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} - {self.category.name}"


class MealItemImage(models.Model):
    """نموذج صور الوجبات"""
    meal = models.ForeignKey(MealItem, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='meals/', verbose_name="صورة الوجبة")
    caption = models.CharField(max_length=200, blank=True, null=True, verbose_name="تعليق")
    is_primary = models.BooleanField(default=False, verbose_name="صورة رئيسية")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "صورة وجبة"
        verbose_name_plural = "صور الوجبات"
        ordering = ['-is_primary', '-created_at']

    def __str__(self):
        return f"صورة {self.caption or 'وجبة'}"

    def image_tag(self):
        if self.image:
            return format_html('<img src="{}" style="max-height: 50px;" />'.format(self.image.url))
        return ""
    image_tag.short_description = 'صورة مصغرة'
    image_tag.allow_tags = True


class MealComponent(models.Model):
    COMPONENT_TYPE_CHOICES = [
        ('main', 'طبق رئيسي'),
        ('side', 'طبق جانبي'),
        ('salad', 'سلطة'),
        ('sauce', 'صوص'),
        ('bread', 'خبز'),
        ('drink', 'مشروب'),
        ('dessert', 'حلويات'),
        ('other', 'أخرى'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="اسم المكون")
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPE_CHOICES, default='main', verbose_name="نوع المكون")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    is_available = models.BooleanField(default=True, verbose_name="متوفر")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = 'مكون الوجبة'
        verbose_name_plural = 'مكونات الوجبات'
        ordering = ['component_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_component_type_display()})"


class MealItemComponent(models.Model):
    meal = models.ForeignKey(MealItem, on_delete=models.CASCADE, related_name='meal_components', verbose_name="الوجبة")
    component = models.ForeignKey(MealComponent, on_delete=models.CASCADE, verbose_name="المكون")
    quantity = models.CharField(max_length=100, blank=True, null=True, verbose_name="الكمية")
    is_optional = models.BooleanField(default=False, verbose_name="اختياري")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتيب العرض")

    class Meta:
        verbose_name = 'مكون الوجبة'
        verbose_name_plural = 'مكونات الوجبات'
        ordering = ['order']
        unique_together = ('meal', 'component')

    def __str__(self):
        return f"{self.meal.name} - {self.component.name}"


class MealComponentImage(models.Model):
    """نموذج صور مكونات الوجبات"""
    component = models.ForeignKey(MealComponent, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='meal_components/', verbose_name="صورة المكون")
    caption = models.CharField(max_length=200, blank=True, null=True, verbose_name="تعليق")
    is_primary = models.BooleanField(default=False, verbose_name="صورة رئيسية")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "صورة مكون وجبة"
        verbose_name_plural = "صور مكونات الوجبات"
        ordering = ['-is_primary', '-created_at']

    def __str__(self):
        return f"صورة {self.caption or 'مكون'}"

    def image_tag(self):
        if self.image:
            return format_html('<img src="{}" style="max-height: 50px;" />'.format(self.image.url))
        return ""
    image_tag.short_description = 'صورة مصغرة'
    image_tag.allow_tags = True
