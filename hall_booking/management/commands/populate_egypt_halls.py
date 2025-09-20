from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from hall_booking.models import Hall, Category, Governorate, City, HallImage
import requests
import random

class Command(BaseCommand):
    help = 'إضافة قاعات مع صور في جميع محافظات مصر'

    def handle(self, *args, **options):
        # التأكد من وجود الفئات
        categories = list(Category.objects.all())
        if not categories:
            self.stdout.write(self.style.ERROR('لا توجد فئات! يرجى إضافة الفئات أولاً'))
            return

        # التأكد من وجود المحافظات والمدن
        governorates = list(Governorate.objects.all())
        if not governorates:
            self.stdout.write(self.style.ERROR('لا توجد محافظات! يرجى تشغيل populate_egypt_locations أولاً'))
            return

        # أسماء القاعات المصرية
        hall_names = [
            'قاعة النيل الذهبية', 'قاعة الأهرام الملكية', 'قاعة الفراعنة الكبرى',
            'قاعة كليوباترا', 'قاعة رمسيس الثاني', 'قاعة الإسكندرية',
            'قاعة القاهرة الفاطمية', 'قاعة المعز لدين الله', 'قاعة صلاح الدين',
            'قاعة الأزهر الشريف', 'قاعة خان الخليلي', 'قاعة القلعة',
            'قاعة الجزيرة', 'قاعة الزمالك', 'قاعة المقطم',
            'قاعة الهرم الأكبر', 'قاعة أبو الهول', 'قاعة سقارة',
            'قاعة دهشور', 'قاعة ميت رهينة', 'قاعة الفيوم الجميلة',
            'قاعة وادي الريان', 'قاعة قارون', 'قاعة هوارة',
            'قاعة اللاهون', 'قاعة المنيا الأثرية', 'قاعة تل العمارنة',
            'قاعة بني حسن', 'قاعة دير المحرق', 'قاعة أسيوط التاريخية',
            'قاعة أبيدوس', 'قاعة دندرة', 'قاعة الأقصر الفرعونية',
            'قاعة الكرنك', 'قاعة حتشبسوت', 'قاعة وادي الملوك',
            'قاعة فيلة', 'قاعة أبو سمبل', 'قاعة كوم أمبو',
            'قاعة إدفو', 'قاعة الإسماعيلية', 'قاعة قناة السويس',
            'قاعة بورسعيد البحرية', 'قاعة السويس الباسلة', 'قاعة سيناء',
            'قاعة شرم الشيخ', 'قاعة دهب الذهبية', 'قاعة نويبع',
            'قاعة الغردقة المرجانية', 'قاعة مرسى علم', 'قاعة سفاجا',
            'قاعة الإسكندرية العروس', 'قاعة المنتزه', 'قاعة ستانلي',
            'قاعة القلعة البحرية', 'قاعة المكتبة الجديدة', 'قاعة كورنيش الإسكندرية'
        ]

        # أوصاف القاعات
        descriptions = [
            'قاعة فاخرة مجهزة بأحدث التقنيات والديكورات الأنيقة، مناسبة لجميع المناسبات الخاصة والمؤتمرات.',
            'قاعة عصرية بتصميم مصري أصيل، تتميز بالإضاءة المميزة والمساحات الواسعة.',
            'قاعة راقية مع إطلالة رائعة، مجهزة بأنظمة صوتية متطورة وخدمات ضيافة متميزة.',
            'قاعة أنيقة بطراز معماري فريد، توفر أجواء مثالية للاحتفالات والمناسبات الرسمية.',
            'قاعة حديثة مكيفة بالكامل، مع مرافق متكاملة وخدمات عالية الجودة.',
            'قاعة فسيحة بديكورات فاخرة، مناسبة للأفراح والمؤتمرات والفعاليات الكبرى.',
            'قاعة مميزة بموقع استراتيجي، توفر خدمات شاملة وأجواء راقية لضيوفكم.',
            'قاعة عملية وأنيقة، مجهزة بكافة وسائل الراحة والتقنيات الحديثة.'
        ]

        # المميزات المختلفة
        features_options = [
            ['تكييف مركزي', 'نظام صوتي متطور', 'إضاءة LED', 'مواقف سيارات'],
            ['واي فاي مجاني', 'شاشات عرض', 'مسرح', 'خدمة ضيافة'],
            ['كاميرات مراقبة', 'مولد كهرباء', 'مصعد', 'دورات مياه فاخرة'],
            ['حديقة خارجية', 'منطقة أطفال', 'مطبخ مجهز', 'خدمة أمن'],
            ['إطلالة بحرية', 'تراس خارجي', 'نافورة', 'إضاءة ملونة'],
            ['قاعة VIP', 'غرف تبديل ملابس', 'منطقة استقبال', 'خدمة تصوير']
        ]

        halls_created = 0
        images_created = 0

        # URLs للصور التجريبية (يمكن استبدالها بصور حقيقية)
        sample_images = [
            'https://images.unsplash.com/photo-1519167758481-83f29c8e8d4b?w=800',
            'https://images.unsplash.com/photo-1464366400600-7168b8af9bc3?w=800',
            'https://images.unsplash.com/photo-1511795409834-ef04bbd61622?w=800',
            'https://images.unsplash.com/photo-1505236858219-8359eb29e329?w=800',
            'https://images.unsplash.com/photo-1478146896981-b80fe463b330?w=800',
            'https://images.unsplash.com/photo-1519225421980-715cb0215aed?w=800',
            'https://images.unsplash.com/photo-1464207687429-7505649dae38?w=800',
            'https://images.unsplash.com/photo-1540979388789-6cee28a1cdc9?w=800'
        ]

        for governorate in governorates:
            cities = list(governorate.cities.all())
            if not cities:
                continue

            # إنشاء 3-5 قاعات في كل محافظة
            halls_per_governorate = random.randint(3, 5)
            
            for i in range(halls_per_governorate):
                # اختيار مدينة عشوائية في المحافظة
                city = random.choice(cities)
                
                # اختيار اسم قاعة عشوائي
                base_name = random.choice(hall_names)
                hall_name = f"{base_name} - {city.name}"
                
                # التأكد من عدم تكرار الاسم
                counter = 1
                original_name = hall_name
                while Hall.objects.filter(name=hall_name).exists():
                    hall_name = f"{original_name} {counter}"
                    counter += 1

                # اختيار فئة عشوائية
                category = random.choice(categories)
                
                # اختيار وصف عشوائي
                description = random.choice(descriptions)
                
                # تحديد السعة والسعر
                capacity = random.choice([50, 75, 100, 150, 200, 250, 300, 400, 500])
                price_per_hour = random.randint(200, 1000)
                
                # اختيار مميزات عشوائية
                features = random.choice(features_options)
                
                # عنوان تفصيلي
                addresses = [
                    f"شارع النيل، {city.name}",
                    f"شارع الجمهورية، {city.name}",
                    f"كورنيش النيل، {city.name}",
                    f"شارع المحطة، {city.name}",
                    f"ميدان التحرير، {city.name}",
                    f"شارع الجيش، {city.name}"
                ]
                address = random.choice(addresses)

                try:
                    # إنشاء القاعة
                    hall = Hall.objects.create(
                        name=hall_name,
                        category=category,
                        governorate=governorate,
                        city=city,
                        address=address,
                        description=description,
                        capacity=capacity,
                        price_per_hour=price_per_hour,
                        status='available',
                        features=features,
                        phone=f"0{random.randint(10, 15)}{random.randint(10000000, 99999999)}",
                        email=f"info@{hall_name.replace(' ', '').lower()}.com"
                    )
                    
                    halls_created += 1
                    
                    # إضافة صور للقاعة
                    num_images = random.randint(2, 4)
                    for j in range(num_images):
                        try:
                            image_url = random.choice(sample_images)
                            response = requests.get(image_url, timeout=10)
                            
                            if response.status_code == 200:
                                image_content = ContentFile(response.content)
                                image_name = f"hall_{hall.id}_{j+1}.jpg"
                                
                                # تحديد نوع الصورة
                                image_types = ['main', 'gallery', 'interior', 'exterior']
                                image_type = 'main' if j == 0 else random.choice(image_types[1:])
                                
                                hall_image = HallImage.objects.create(
                                    hall=hall,
                                    image_type=image_type,
                                    title=f"صورة {j+1} لقاعة {hall.name}",
                                    is_featured=(j == 0),
                                    order=j
                                )
                                hall_image.image.save(image_name, image_content, save=True)
                                images_created += 1
                                
                        except Exception as e:
                            self.stdout.write(f'خطأ في تحميل الصورة: {e}')
                            continue
                    
                    if halls_created % 5 == 0:
                        self.stdout.write(f'تم إنشاء {halls_created} قاعة...')
                        
                except Exception as e:
                    self.stdout.write(f'خطأ في إنشاء القاعة {hall_name}: {e}')
                    continue

        self.stdout.write(
            self.style.SUCCESS(
                f'تم إنشاء {halls_created} قاعة و {images_created} صورة بنجاح في جميع محافظات مصر!'
            )
        )
