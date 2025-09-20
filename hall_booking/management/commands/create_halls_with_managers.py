from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from hall_booking.models import Category, Hall, HallImage, HallManager
import random
import requests
from io import BytesIO

class Command(BaseCommand):
    help = 'إنشاء قاعات مع صور من الإنترنت ومديرين تجريبيين'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='عدد القاعات المراد إنشاؤها (افتراضي: 5)',
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # أسماء القاعات
        hall_names = [
            'قاعة الأمل الكبرى',
            'قاعة النور للمؤتمرات',
            'قاعة الياسمين',
            'قاعة الفردوس',
            'قاعة الزهراء',
            'قاعة الأندلس',
            'قاعة القدس',
            'قاعة الحرمين',
            'قاعة الأقصى',
            'قاعة الكوثر'
        ]
        
        # روابط صور القاعات من الإنترنت
        image_urls = [
            'https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=800&h=600&fit=crop',
            'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&h=600&fit=crop',
            'https://images.unsplash.com/photo-1511578314322-379afb476865?w=800&h=600&fit=crop',
            'https://images.unsplash.com/photo-1505236858219-8359eb29e329?w=800&h=600&fit=crop',
            'https://images.unsplash.com/photo-1464366400600-7168b8af9bc3?w=800&h=600&fit=crop',
            'https://images.unsplash.com/photo-1571624436279-b272aff752b5?w=800&h=600&fit=crop',
            'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop',
            'https://images.unsplash.com/photo-1587825140708-dfaf72ae4b04?w=800&h=600&fit=crop',
            'https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?w=800&h=600&fit=crop',
            'https://images.unsplash.com/photo-1597149962419-0d900ac2e4c4?w=800&h=600&fit=crop'
        ]
        
        # صور إضافية للمعرض
        gallery_urls = [
            'https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1511578314322-379afb476865?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1505236858219-8359eb29e329?w=600&h=400&fit=crop',
            'https://images.unsplash.com/photo-1464366400600-7168b8af9bc3?w=600&h=400&fit=crop'
        ]
        
        # مميزات القاعات
        features_list = [
            ['مكيف', 'صوتيات', 'إضاءة', 'مسرح'],
            ['واي فاي', 'بروجكتر', 'مايك', 'كراسي مريحة'],
            ['مطبخ', 'حمامات', 'موقف سيارات', 'أمان'],
            ['تكييف مركزي', 'نظام صوتي متطور', 'شاشة عرض كبيرة'],
            ['إضاءة LED', 'نظام تهوية', 'مدخل منفصل', 'خدمة ضيافة']
        ]
        
        # التأكد من وجود فئات
        categories = list(Category.objects.all())
        if not categories:
            self.stdout.write(self.style.ERROR('لا توجد فئات قاعات في قاعدة البيانات!'))
            return
        
        halls_created = 0
        managers_created = 0
        
        for i in range(count):
            # إنشاء مستخدم جديد ليكون مدير القاعة
            username = f'hall_manager_{i+1}'
            email = f'manager{i+1}@example.com'
            
            # التحقق من عدم وجود المستخدم مسبقاً
            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='manager123',
                    first_name=f'مدير',
                    last_name=f'القاعة {i+1}'
                )
                managers_created += 1
            
            # إنشاء القاعة
            hall_name = hall_names[i % len(hall_names)]
            unique_name = f"{hall_name} - {i+1}"
            
            category = random.choice(categories)
            capacity = random.randint(50, 500)
            price_per_hour = random.randint(100, 1000)
            features = random.choice(features_list)
            
            description = f"قاعة {unique_name} - قاعة مجهزة بالكامل تناسب جميع أنواع المناسبات والفعاليات. تتميز بموقع مميز وخدمة عالية الجودة."
            
            # تحميل الصورة الرئيسية
            main_image_url = image_urls[i % len(image_urls)]
            try:
                response = requests.get(main_image_url, timeout=10)
                response.raise_for_status()
                image_content = ContentFile(response.content)
                image_name = f"hall_{i+1}_main.jpg"
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'فشل تحميل الصورة الرئيسية: {e}'))
                image_content = None
                image_name = None
            
            # إنشاء القاعة
            hall = Hall.objects.create(
                name=unique_name,
                category=category,
                description=description,
                capacity=capacity,
                price_per_hour=price_per_hour,
                status='available',
                features=features
            )
            
            # إضافة الصورة الرئيسية
            if image_content and image_name:
                hall.image.save(image_name, image_content, save=True)
            
            # إضافة صور إضافية للمعرض
            for j, gallery_url in enumerate(gallery_urls[:3]):  # إضافة 3 صور لكل قاعة
                try:
                    response = requests.get(gallery_url, timeout=10)
                    response.raise_for_status()
                    gallery_image_content = ContentFile(response.content)
                    gallery_image_name = f"hall_{i+1}_gallery_{j+1}.jpg"
                    
                    hall_image = HallImage.objects.create(
                        hall=hall,
                        image_type='gallery',
                        title=f'صورة {j+1} لقاعة {hall.name}',
                        order=j+1
                    )
                    hall_image.image.save(gallery_image_name, gallery_image_content, save=True)
                    
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'فشل تحميل صورة المعرض {j+1}: {e}'))
            
            # تعيين المستخدم كمدير للقاعة
            if not HallManager.objects.filter(user=user).exists():
                HallManager.objects.create(
                    user=user,
                    hall=hall,
                    permission_level='manage',
                    is_active=True,
                    notes=f'مدير تجريبي للقاعة {hall.name}'
                )
            
            halls_created += 1
            if halls_created % 2 == 0:
                self.stdout.write(f'تم إنشاء {halls_created} قاعة...')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'تم إنشاء {halls_created} قاعة و {managers_created} مدير قاعة بنجاح!'
            )
        )
        
        # عرض معلومات المديرين
        self.stdout.write('\n=== معلومات مديري القاعات ===')
        for manager in HallManager.objects.filter(is_active=True):
            self.stdout.write(
                f'المدير: {manager.user.username} | القاعة: {manager.hall.name} | كلمة المرور: manager123'
            )
