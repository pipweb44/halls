from django.core.management.base import BaseCommand
from hall_booking.models import Contact
import random

class Command(BaseCommand):
    help = 'إضافة رسائل تواصل تجريبية'

    def handle(self, *args, **options):
        # أسماء العملاء التجريبية
        customer_names = [
            'أحمد محمد', 'فاطمة علي', 'محمد أحمد', 'سارة محمود', 'علي حسن',
            'نور الدين', 'مريم أحمد', 'حسن علي', 'زينب محمد', 'عبد الله أحمد',
            'آمنة علي', 'يوسف محمد', 'خديجة أحمد', 'عمر حسن', 'فاطمة الزهراء'
        ]

        # عناوين الرسائل
        subjects = [
            'استفسار عن القاعات المتاحة',
            'طلب معلومات إضافية',
            'استفسار عن الأسعار',
            'طلب حجز قاعة',
            'شكوى أو اقتراح',
            'استفسار عن الخدمات',
            'طلب عرض أسعار',
            'استفسار عن التواريخ المتاحة',
            'طلب معلومات عن الفعاليات',
            'استفسار عن الشروط والأحكام'
        ]

        # محتوى الرسائل
        messages = [
            'أريد معرفة القاعات المتاحة في الأسبوع القادم وأسعارها.',
            'هل يمكنني الحصول على معلومات إضافية عن خدماتكم؟',
            'أحتاج إلى قاعة لحفل زفاف في الشهر القادم.',
            'أريد معرفة الأسعار والخدمات المقدمة.',
            'هل توجد قاعات مناسبة لمؤتمر يضم 100 شخص؟',
            'أحتاج إلى معلومات عن الخدمات الإضافية المقدمة.',
            'أريد عرض أسعار لقاعة اجتماعات صغيرة.',
            'هل توجد تواريخ متاحة في نهاية الشهر؟',
            'أحتاج إلى معلومات عن إعدادات القاعات للفعاليات.',
            'أريد معرفة الشروط والأحكام للحجز.'
        ]

        contacts_created = 0

        # إنشاء رسائل مقروءة
        for i in range(15):
            contact = Contact.objects.create(
                name=random.choice(customer_names),
                email=f"{random.choice(customer_names).replace(' ', '.').lower()}@example.com",
                phone=f"01{random.randint(100000000, 999999999)}",
                subject=random.choice(subjects),
                message=random.choice(messages),
                is_read=True
            )
            contacts_created += 1

        # إنشاء رسائل غير مقروءة
        for i in range(8):
            contact = Contact.objects.create(
                name=random.choice(customer_names),
                email=f"{random.choice(customer_names).replace(' ', '.').lower()}@example.com",
                phone=f"01{random.randint(100000000, 999999999)}",
                subject=random.choice(subjects),
                message=random.choice(messages),
                is_read=False
            )
            contacts_created += 1

        self.stdout.write(
            self.style.SUCCESS(f'تم إنشاء {contacts_created} رسالة تواصل تجريبية بنجاح!')
        ) 