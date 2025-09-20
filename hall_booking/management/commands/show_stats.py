from django.core.management.base import BaseCommand
from hall_booking.models import Category, Hall, Booking
from django.db.models import Count, Avg, Sum
from datetime import datetime

class Command(BaseCommand):
    help = 'عرض إحصائيات البيانات التجريبية'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== إحصائيات البيانات التجريبية ==='))
        
        # إحصائيات الفئات
        self.stdout.write('\n📊 إحصائيات الفئات:')
        categories = Category.objects.annotate(hall_count=Count('hall'))
        for category in categories:
            self.stdout.write(f'  • {category.name}: {category.hall_count} قاعة')
        
        # إحصائيات القاعات
        self.stdout.write('\n🏢 إحصائيات القاعات:')
        total_halls = Hall.objects.count()
        available_halls = Hall.objects.filter(status='available').count()
        avg_price = Hall.objects.aggregate(avg_price=Avg('price_per_hour'))['avg_price']
        avg_capacity = Hall.objects.aggregate(avg_capacity=Avg('capacity'))['avg_capacity']
        
        self.stdout.write(f'  • إجمالي القاعات: {total_halls}')
        self.stdout.write(f'  • القاعات المتاحة: {available_halls}')
        self.stdout.write(f'  • متوسط السعر للساعة: {avg_price:.2f} جنيه')
        self.stdout.write(f'  • متوسط السعة: {avg_capacity:.0f} شخص')
        
        # إحصائيات الحجوزات
        self.stdout.write('\n📅 إحصائيات الحجوزات:')
        total_bookings = Booking.objects.count()
        completed_bookings = Booking.objects.filter(status='completed').count()
        approved_bookings = Booking.objects.filter(status='approved').count()
        pending_bookings = Booking.objects.filter(status='pending').count()
        total_revenue = Booking.objects.filter(status='completed').aggregate(total=Sum('total_price'))['total'] or 0
        
        self.stdout.write(f'  • إجمالي الحجوزات: {total_bookings}')
        self.stdout.write(f'  • الحجوزات المكتملة: {completed_bookings}')
        self.stdout.write(f'  • الحجوزات الموافق عليها: {approved_bookings}')
        self.stdout.write(f'  • الحجوزات المعلقة: {pending_bookings}')
        self.stdout.write(f'  • إجمالي الإيرادات: {total_revenue:.2f} جنيه')
        
        # إحصائيات حسب المحافظات
        self.stdout.write('\n🗺️ إحصائيات حسب المحافظات:')
        halls_by_governorate = {}
        for hall in Hall.objects.all():
            # استخراج اسم المحافظة من اسم القاعة
            name_parts = hall.name.split(' - ')
            if len(name_parts) > 1:
                area = name_parts[1]
                # تحديد المحافظة بناءً على المنطقة
                governorate = self.get_governorate_from_area(area)
                if governorate:
                    halls_by_governorate[governorate] = halls_by_governorate.get(governorate, 0) + 1
        
        for governorate, count in sorted(halls_by_governorate.items(), key=lambda x: x[1], reverse=True):
            self.stdout.write(f'  • {governorate}: {count} قاعة')
        
        self.stdout.write('\n✅ تم عرض جميع الإحصائيات بنجاح!')

    def get_governorate_from_area(self, area):
        """تحديد المحافظة بناءً على المنطقة"""
        governorates = {
            'القاهرة': ['وسط البلد', 'المعادي', 'مدينة نصر', 'الزمالك', 'مصر الجديدة', 'المرج'],
            'الإسكندرية': ['سموحة', 'سيدي جابر', 'المنتزه', 'العجمي', 'ميامي', 'ستانلي'],
            'الجيزة': ['الدقي', 'المهندسين', '6 أكتوبر', 'الشيخ زايد', 'الهرم', 'بولاق الدكرور'],
            'الشرقية': ['الزقازيق', 'العاشر من رمضان', 'بلبيس', 'أبو كبير', 'فاقوس', 'ههيا'],
            'الغربية': ['طنطا', 'المحلة الكبرى', 'زفتى', 'سمنود', 'قطور', 'بسيون'],
            'كفر الشيخ': ['كفر الشيخ', 'دسوق', 'فوه', 'مطوبس', 'سيدي سالم', 'الرياض'],
            'المنوفية': ['شبين الكوم', 'سادات', 'أشمون', 'الباجور', 'قويسنا', 'بركة السبع'],
            'المنيا': ['المنيا', 'مطاي', 'بني مزار', 'مغاغة', 'سمالوط', 'أبو قرقاص'],
            'أسيوط': ['أسيوط', 'ديروط', 'منفلوط', 'أبنوب', 'البداري', 'ساحل سليم'],
            'سوهاج': ['سوهاج', 'أخميم', 'البلينا', 'مرسى', 'الغنايم', 'طهطا'],
            'قنا': ['قنا', 'قوص', 'نقادة', 'دشنا', 'أبو تشت', 'فرشوط'],
            'الأقصر': ['الأقصر', 'إسنا', 'الطود', 'بياضة العرب', 'الزينية', 'القرنة'],
            'أسوان': ['أسوان', 'كوم أمبو', 'دراو', 'نصر النوبة', 'كلابشة', 'إدفو'],
            'بني سويف': ['بني سويف', 'الواسطي', 'ناصر', 'إهناسيا', 'ببا', 'سمسطا'],
            'الفيوم': ['الفيوم', 'سنورس', 'طامية', 'إطسا', 'يوسف الصديق', 'إبشواي'],
            'دمياط': ['دمياط', 'فارسكور', 'الزرقا', 'كفر البطيخ', 'الروضة', 'السرو'],
            'الدقهلية': ['المنصورة', 'ميت غمر', 'أجا', 'السنبلاوين', 'بني عبيد', 'المنزلة'],
            'البحيرة': ['دمنهور', 'كفر الدوار', 'رشيد', 'إدكو', 'أبو المطامير', 'حوش عيسى'],
            'الإسماعيلية': ['الإسماعيلية', 'فايد', 'القنطرة شرق', 'القنطرة غرب', 'التل الكبير', 'أبو صوير'],
            'بورسعيد': ['بورسعيد', 'بورفؤاد', 'العرب', 'الزهور', 'المناخ', 'الضواحي'],
            'شمال سيناء': ['العريش', 'رفح', 'بئر العبد', 'نخل', 'الحسنة', 'الشيخ زويد'],
            'جنوب سيناء': ['الطور', 'سانت كاترين', 'دهب', 'نويبع', 'شرم الشيخ', 'طابا'],
            'البحر الأحمر': ['الغردقة', 'رأس غارب', 'سفاجا', 'القصير', 'مرسى علم', 'برنيس'],
            'الوادي الجديد': ['الخارجة', 'الداخلة', 'الفرافرة', 'باريس', 'موط', 'بلاط'],
            'مطروح': ['مرسى مطروح', 'سيدي براني', 'السلوم', 'سيوة', 'النجيلة', 'راس الحكمة']
        }
        
        for governorate, areas in governorates.items():
            if area in areas:
                return governorate
        return None 