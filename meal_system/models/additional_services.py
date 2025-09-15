from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

class HallAdditionalService(models.Model):
    """
    نموذج لإدارة الخدمات الإضافية المتاحة للقاعة
    مثل: الديكور، التصوير، الساوند سيستم، إلخ
    """
    hall = models.ForeignKey(
        'hall_booking.Hall',
        on_delete=models.CASCADE,
        related_name='meal_additional_services',
        verbose_name=_("القاعة")
    )
    name = models.CharField(max_length=200, verbose_name=_("اسم الخدمة"))
    description = models.TextField(blank=True, null=True, verbose_name=_("وصف الخدمة"))
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("سعر الخدمة"),
        help_text=_("سعر الخدمة الإضافية بالريال")
    )
    is_available = models.BooleanField(default=True, verbose_name=_("متاحة"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإضافة"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("تاريخ التحديث"))

    objects = models.Manager()

    class Meta:
        verbose_name = _("خدمة إضافية")
        verbose_name_plural = _("الخدمات الإضافية")
        ordering = ['name']
        unique_together = ['hall', 'name']

    def __str__(self):
        return f"{self.name} - {self.hall.name} ({self.price} ريال)"

    def clean(self):
        if self.price < 0:
            raise ValidationError({
                'price': _('يجب أن يكون السعر أكبر من أو يساوي الصفر')
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
