from django.core.management.base import BaseCommand
from hall_booking.models import Hall, Booking
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'إضافة حجوزات تجريبية'

    def handle(self, *args, **options):
        # أسماء العملاء التجريبية
        customer_names = [
            'أحمد محمد', 'فاطمة علي', 'محمد أحمد', 'سارة محمود', 'علي حسن',
            'نور الدين', 'مريم أحمد', 'حسن علي', 'زينب محمد', 'عبد الله أحمد',
            'آمنة علي', 'يوسف محمد', 'خديجة أحمد', 'عمر حسن', 'فاطمة الزهراء',
            'محمد علي', 'عائشة أحمد', 'علي محمد', 'مريم حسن', 'أحمد علي'
        ]

        # أسماء الأحداث
        event_titles = [
            'مؤتمر التكنولوجيا', 'حفل زفاف', 'ندوة تعليمية', 'معرض تجاري',
            'حفل عيد ميلاد', 'اجتماع عمل', 'ورشة تدريبية', 'حفل تخرج',
            'مؤتمر طبي', 'معرض فني', 'حفل خطوبة', 'ندوة ثقافية',
            'اجتماع مجلس إدارة', 'حفل شركة', 'مؤتمر اقتصادي'
        ]

        # أوصاف الأحداث
        event_descriptions = [
            'حدث مميز يجمع نخبة من المتخصصين في المجال',
            'حفل احتفالي رائع مع أجواء من البهجة والسرور',
            'ندوة تعليمية تهدف إلى تطوير المهارات والمعرفة',
            'معرض تجاري يضم أفضل المنتجات والخدمات',
            'حفل عيد ميلاد مميز مع أجواء احتفالية رائعة',
            'اجتماع عمل مهم لمناقشة الخطط المستقبلية',
            'ورشة تدريبية متخصصة لتنمية المهارات',
            'حفل تخرج احتفالي للطلاب المتفوقين',
            'مؤتمر طبي متخصص في أحدث التطورات الطبية',
            'معرض فني يضم إبداعات الفنانين المحليين'
        ]

        # الحصول على جميع القاعات
        halls = list(Hall.objects.all())
        
        if not halls:
            self.stdout.write(self.style.ERROR('لا توجد قاعات متاحة. يرجى إنشاء القاعات أولاً.'))
            return

        bookings_created = 0
        
        # إنشاء حجوزات في الماضي (مكتملة)
        for i in range(20):
            hall = random.choice(halls)
            customer_name = random.choice(customer_names)
            event_title = random.choice(event_titles)
            event_description = random.choice(event_descriptions)
            
            # تاريخ في الماضي
            start_date = datetime.now() - timedelta(days=random.randint(1, 30))
            end_date = start_date + timedelta(hours=random.randint(2, 8))
            
            # حساب السعر الإجمالي
            hours = (end_date - start_date).total_seconds() / 3600
            total_price = float(hall.price_per_hour) * hours
            
            booking = Booking.objects.create(
                hall=hall,
                customer_name=customer_name,
                customer_email=f"{customer_name.replace(' ', '.').lower()}@example.com",
                customer_phone=f"01{random.randint(100000000, 999999999)}",
                event_title=event_title,
                event_description=event_description,
                start_datetime=start_date,
                end_datetime=end_date,
                attendees_count=random.randint(10, hall.capacity),
                total_price=total_price,
                status='completed'
            )
            bookings_created += 1

        # إنشاء حجوزات في المستقبل (موافق عليها)
        for i in range(15):
            hall = random.choice(halls)
            customer_name = random.choice(customer_names)
            event_title = random.choice(event_titles)
            event_description = random.choice(event_descriptions)
            
            # تاريخ في المستقبل
            start_date = datetime.now() + timedelta(days=random.randint(1, 30))
            end_date = start_date + timedelta(hours=random.randint(2, 8))
            
            # حساب السعر الإجمالي
            hours = (end_date - start_date).total_seconds() / 3600
            total_price = float(hall.price_per_hour) * hours
            
            booking = Booking.objects.create(
                hall=hall,
                customer_name=customer_name,
                customer_email=f"{customer_name.replace(' ', '.').lower()}@example.com",
                customer_phone=f"01{random.randint(100000000, 999999999)}",
                event_title=event_title,
                event_description=event_description,
                start_datetime=start_date,
                end_datetime=end_date,
                attendees_count=random.randint(10, hall.capacity),
                total_price=total_price,
                status='approved'
            )
            bookings_created += 1

        # إنشاء حجوزات معلقة
        for i in range(10):
            hall = random.choice(halls)
            customer_name = random.choice(customer_names)
            event_title = random.choice(event_titles)
            event_description = random.choice(event_descriptions)
            
            # تاريخ في المستقبل
            start_date = datetime.now() + timedelta(days=random.randint(1, 30))
            end_date = start_date + timedelta(hours=random.randint(2, 8))
            
            # حساب السعر الإجمالي
            hours = (end_date - start_date).total_seconds() / 3600
            total_price = float(hall.price_per_hour) * hours
            
            booking = Booking.objects.create(
                hall=hall,
                customer_name=customer_name,
                customer_email=f"{customer_name.replace(' ', '.').lower()}@example.com",
                customer_phone=f"01{random.randint(100000000, 999999999)}",
                event_title=event_title,
                event_description=event_description,
                start_datetime=start_date,
                end_datetime=end_date,
                attendees_count=random.randint(10, hall.capacity),
                total_price=total_price,
                status='pending'
            )
            bookings_created += 1

        self.stdout.write(
            self.style.SUCCESS(f'تم إنشاء {bookings_created} حجز تجريبي بنجاح!')
        ) 