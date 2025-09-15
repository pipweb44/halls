from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from ..models import HallAdditionalService

@admin.register(HallAdditionalService)
class HallAdditionalServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'hall', 'price', 'is_available', 'created_at')
    list_filter = ('is_available', 'hall')
    search_fields = ('name', 'description', 'hall__name')
    list_editable = ('is_available', 'price')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('معلومات الخدمة'), {
            'fields': ('hall', 'name', 'description')
        }),
        (_('التسعير والتوفر'), {
            'fields': ('price', 'is_available')
        }),
        (_('التواريخ'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('hall')
