# noqa: E501
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from hall_booking.models import Category, Hall
import random
import requests
from io import BytesIO

class Command(BaseCommand):
    help = 'إضافة 10 قاعات بفئات عشوائية وصور من الإنترنت'

    def handle(self, *args, **options):
        # صور قاعات من Unsplash (روابط مباشرة)
        image_urls = [
            'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1464983953574-0892a716854b?auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1465101046530-73398c7f28ca?auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1465101178521-c1a9136a3b99?auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1465101046530-73398c7f28ca?auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?auto=format&fit=crop&w=800&q=80',
        ]
        hall_names = [
            'قاعة النخبة', 'قاعة الفخامة', 'قاعة الريادة', 'قاعة السعادة', 'قاعة الأمل',
            'قاعة الزهور', 'قاعة القمة', 'قاعة الماسة', 'قاعة اللؤلؤة', 'قاعة النجوم'
        ]
        features_list = [
            ['مكيف هواء', 'إضاءة متطورة', 'نظام صوت'],
            ['شاشة عرض', 'واي فاي مجاني', 'مقاعد مريحة'],
            ['مطبخ مجهز', 'موقف سيارات', 'خدمة تنظيف'],
            ['مصعد', 'مكيف مركزي', 'نظام أمان'],
            ['مطبخ تجاري', 'موقف سيارات كبير', 'خدمة كاملة'],
        ]
        categories = list(Category.objects.all())  # noqa
        if not categories:
            self.stdout.write(self.style.ERROR('لا توجد فئات قاعات في قاعدة البيانات!'))
            return
        for i in range(10):
            name = hall_names[i % len(hall_names)]
            category = random.choice(categories)
            description = f"{name} - قاعة مجهزة بالكامل تناسب جميع أنواع المناسبات والفعاليات."
            capacity = random.randint(50, 400)
            price_per_hour = random.randint(200, 1000)
            status = 'available'
            features = random.choice(features_list)
            image_url = image_urls[i % len(image_urls)]
            # تحميل الصورة
            try:
                response = requests.get(image_url)
                response.raise_for_status()
                image_content = ContentFile(response.content)
                image_name = f"hall_{i+1}.jpg"
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'فشل تحميل الصورة: {e}'))
                image_content = None
                image_name = None
            hall = Hall(
                name=name,
                category=category,
                description=description,
                capacity=capacity,
                price_per_hour=price_per_hour,
                status=status,
                features=features
            )
            if image_content:
                hall.image.save(image_name, image_content, save=False)  # noqa
            hall.save()
            self.stdout.write(self.style.SUCCESS(f'تمت إضافة القاعة: {name}'))
        self.stdout.write(self.style.SUCCESS('تمت إضافة 10 قاعات بنجاح!')) 