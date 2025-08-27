from django import forms
from django.core.validators import MinValueValidator
from datetime import datetime, timedelta
from .models import Booking, Contact, Hall
from django.utils import timezone
# Define a custom validator for the start and end datetime fields
# This validator checks that the start datetime is before the end datetime

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['customer_name', 'customer_email', 'customer_phone', 'event_title', 
                 'event_description', 'start_datetime', 'end_datetime', 'attendees_count']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم العميل'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'البريد الإلكتروني'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الهاتف'}),
            'event_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان الحدث'}),
            'event_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'وصف الحدث'}),
            'start_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'attendees_count': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'عدد الحضور'}),
        }
        labels = {
            'customer_name': 'اسم العميل',
            'customer_email': 'البريد الإلكتروني',
            'customer_phone': 'رقم الهاتف',
            'event_title': 'عنوان الحدث',
            'event_description': 'وصف الحدث',
            'start_datetime': 'تاريخ ووقت البداية',
            'end_datetime': 'تاريخ ووقت النهاية',
            'attendees_count': 'عدد الحضور',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Accept the HTML5 datetime-local format (e.g. 2025-08-27T18:30)
        dt_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
        self.fields['start_datetime'].input_formats = dt_formats
        self.fields['end_datetime'].input_formats = dt_formats

    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')
        
        if start_datetime and end_datetime:
            if start_datetime >= end_datetime:
                raise forms.ValidationError('تاريخ النهاية يجب أن يكون بعد تاريخ البداية')
            
            if start_datetime < timezone.now():
                raise forms.ValidationError('لا يمكن حجز تاريخ في الماضي')
        
        return cleaned_data

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الاسم الكامل'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'البريد الإلكتروني'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الهاتف'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الموضوع'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'الرسالة'}),
        }
        labels = {
            'name': 'الاسم',
            'email': 'البريد الإلكتروني',
            'phone': 'رقم الهاتف',
            'subject': 'الموضوع',
            'message': 'الرسالة',
        }

class HallForm(forms.ModelForm):
    class Meta:
        model = Hall
        fields = ['name', 'category', 'description', 'capacity', 'price_per_hour', 'image', 'status', 'features']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم القاعة'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'وصف القاعة'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'السعة'}),
            'price_per_hour': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'السعر للساعة', 'step': '0.01'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'features': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'المميزات (كل مميزة في سطر منفصل)'}),
        }
        labels = {
            'name': 'اسم القاعة',
            'category': 'الفئة',
            'description': 'الوصف',
            'capacity': 'السعة',
            'price_per_hour': 'السعر للساعة',
            'image': 'الصورة',
            'status': 'الحالة',
            'features': 'المميزات',
        }

    def clean_features(self):
        features = self.cleaned_data.get('features')
        if features:
            # إذا كان features نص، قم بتقسيمه
            if isinstance(features, str):
                features_list = [feature.strip() for feature in features.split('\n') if feature.strip()]
                return features_list
            # إذا كان features قائمة، قم بتنظيفها
            elif isinstance(features, list):
                return [feature.strip() for feature in features if feature.strip()]
        return []

    def clean_price_per_hour(self):
        price = self.cleaned_data.get('price_per_hour')
        if price and price <= 0:
            raise forms.ValidationError('السعر يجب أن يكون أكبر من صفر')
        return price

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity and capacity <= 0:
            raise forms.ValidationError('السعة يجب أن تكون أكبر من صفر')
        return capacity 