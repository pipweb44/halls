from django.db import models
from django.utils.html import format_html
from .models import MealItem


class MealComponent(models.Model):
    """نموذج مكونات الوجبة"""
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
    
    meal_item = models.ForeignKey(MealItem, on_delete=models.CASCADE, related_name='components', verbose_name="صنف الوجبة")
    name = models.CharField(max_length=200, verbose_name="اسم المكون")
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPE_CHOICES, default='main', verbose_name="نوع المكون")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    quantity = models.CharField(max_length=100, blank=True, null=True, verbose_name="الكمية")
    is_optional = models.BooleanField(default=False, verbose_name="اختياري")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتيب العرض")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "مكون وجبة"
        verbose_name_plural = "مكونات الوجبات"
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} - {self.meal_item.name}"


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
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />'.format(self.image.url))
        return ""
    image_tag.short_description = 'صورة مصغرة'
    image_tag.allow_tags = True
