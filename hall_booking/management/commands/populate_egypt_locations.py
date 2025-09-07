from django.core.management.base import BaseCommand
from hall_booking.models import Governorate, City

class Command(BaseCommand):
    help = 'إضافة جميع محافظات ومدن مصر'

    def handle(self, *args, **options):
        # بيانات المحافظات والمدن المصرية
        egypt_data = {
            'القاهرة': {
                'name_en': 'Cairo',
                'code': 'CAI',
                'region': 'cairo',
                'cities': [
                    {'name': 'القاهرة', 'name_en': 'Cairo', 'is_capital': True},
                    {'name': 'مدينة نصر', 'name_en': 'Nasr City', 'is_capital': False},
                    {'name': 'المعادي', 'name_en': 'Maadi', 'is_capital': False},
                    {'name': 'حلوان', 'name_en': 'Helwan', 'is_capital': False},
                    {'name': 'التجمع الخامس', 'name_en': 'New Cairo', 'is_capital': False},
                    {'name': 'مصر الجديدة', 'name_en': 'Heliopolis', 'is_capital': False},
                ]
            },
            'الجيزة': {
                'name_en': 'Giza',
                'code': 'GIZ',
                'region': 'cairo',
                'cities': [
                    {'name': 'الجيزة', 'name_en': 'Giza', 'is_capital': True},
                    {'name': 'الهرم', 'name_en': 'Haram', 'is_capital': False},
                    {'name': 'فيصل', 'name_en': 'Faisal', 'is_capital': False},
                    {'name': 'أكتوبر', 'name_en': '6th of October', 'is_capital': False},
                    {'name': 'الشيخ زايد', 'name_en': 'Sheikh Zayed', 'is_capital': False},
                    {'name': 'البدرشين', 'name_en': 'Badrashein', 'is_capital': False},
                ]
            },
            'القليوبية': {
                'name_en': 'Qalyubia',
                'code': 'QLY',
                'region': 'cairo',
                'cities': [
                    {'name': 'بنها', 'name_en': 'Benha', 'is_capital': True},
                    {'name': 'شبرا الخيمة', 'name_en': 'Shubra El Kheima', 'is_capital': False},
                    {'name': 'القناطر الخيرية', 'name_en': 'Qanater', 'is_capital': False},
                    {'name': 'كفر شكر', 'name_en': 'Kafr Shukr', 'is_capital': False},
                    {'name': 'طوخ', 'name_en': 'Tukh', 'is_capital': False},
                ]
            },
            'الإسكندرية': {
                'name_en': 'Alexandria',
                'code': 'ALX',
                'region': 'delta',
                'cities': [
                    {'name': 'الإسكندرية', 'name_en': 'Alexandria', 'is_capital': True},
                    {'name': 'برج العرب', 'name_en': 'Borg El Arab', 'is_capital': False},
                    {'name': 'العامرية', 'name_en': 'Ameria', 'is_capital': False},
                    {'name': 'أبو قير', 'name_en': 'Abu Qir', 'is_capital': False},
                ]
            },
            'البحيرة': {
                'name_en': 'Beheira',
                'code': 'BHR',
                'region': 'delta',
                'cities': [
                    {'name': 'دمنهور', 'name_en': 'Damanhour', 'is_capital': True},
                    {'name': 'كفر الدوار', 'name_en': 'Kafr El Dawar', 'is_capital': False},
                    {'name': 'رشيد', 'name_en': 'Rosetta', 'is_capital': False},
                    {'name': 'إدكو', 'name_en': 'Edko', 'is_capital': False},
                    {'name': 'أبو المطامير', 'name_en': 'Abu El Matamir', 'is_capital': False},
                ]
            },
            'الغربية': {
                'name_en': 'Gharbia',
                'code': 'GHR',
                'region': 'delta',
                'cities': [
                    {'name': 'طنطا', 'name_en': 'Tanta', 'is_capital': True},
                    {'name': 'المحلة الكبرى', 'name_en': 'El Mahalla El Kubra', 'is_capital': False},
                    {'name': 'كفر الزيات', 'name_en': 'Kafr El Zayat', 'is_capital': False},
                    {'name': 'زفتى', 'name_en': 'Zefta', 'is_capital': False},
                    {'name': 'السنطة', 'name_en': 'El Santa', 'is_capital': False},
                ]
            },
            'كفر الشيخ': {
                'name_en': 'Kafr El Sheikh',
                'code': 'KFS',
                'region': 'delta',
                'cities': [
                    {'name': 'كفر الشيخ', 'name_en': 'Kafr El Sheikh', 'is_capital': True},
                    {'name': 'دسوق', 'name_en': 'Desouk', 'is_capital': False},
                    {'name': 'فوه', 'name_en': 'Fooh', 'is_capital': False},
                    {'name': 'مطوبس', 'name_en': 'Metoubes', 'is_capital': False},
                    {'name': 'بيلا', 'name_en': 'Bella', 'is_capital': False},
                ]
            },
            'المنوفية': {
                'name_en': 'Monufia',
                'code': 'MNF',
                'region': 'delta',
                'cities': [
                    {'name': 'شبين الكوم', 'name_en': 'Shebin El Kom', 'is_capital': True},
                    {'name': 'منوف', 'name_en': 'Menouf', 'is_capital': False},
                    {'name': 'سرس الليان', 'name_en': 'Sers El Lyan', 'is_capital': False},
                    {'name': 'أشمون', 'name_en': 'Ashmoun', 'is_capital': False},
                    {'name': 'الباجور', 'name_en': 'El Bagour', 'is_capital': False},
                ]
            },
            'الدقهلية': {
                'name_en': 'Dakahlia',
                'code': 'DKH',
                'region': 'delta',
                'cities': [
                    {'name': 'المنصورة', 'name_en': 'Mansoura', 'is_capital': True},
                    {'name': 'طلخا', 'name_en': 'Talkha', 'is_capital': False},
                    {'name': 'ميت غمر', 'name_en': 'Mit Ghamr', 'is_capital': False},
                    {'name': 'دكرنس', 'name_en': 'Dekernes', 'is_capital': False},
                    {'name': 'أجا', 'name_en': 'Aga', 'is_capital': False},
                ]
            },
            'دمياط': {
                'name_en': 'Damietta',
                'code': 'DMT',
                'region': 'delta',
                'cities': [
                    {'name': 'دمياط', 'name_en': 'Damietta', 'is_capital': True},
                    {'name': 'رأس البر', 'name_en': 'Ras El Bar', 'is_capital': False},
                    {'name': 'فارسكور', 'name_en': 'Faraskour', 'is_capital': False},
                    {'name': 'الزرقا', 'name_en': 'El Zarqa', 'is_capital': False},
                ]
            },
            'الشرقية': {
                'name_en': 'Sharqia',
                'code': 'SHR',
                'region': 'delta',
                'cities': [
                    {'name': 'الزقازيق', 'name_en': 'Zagazig', 'is_capital': True},
                    {'name': 'بلبيس', 'name_en': 'Belbeis', 'is_capital': False},
                    {'name': 'مشتول السوق', 'name_en': 'Mashtoul El Souk', 'is_capital': False},
                    {'name': 'القرين', 'name_en': 'El Qurein', 'is_capital': False},
                    {'name': 'أبو حماد', 'name_en': 'Abu Hammad', 'is_capital': False},
                ]
            },
            'بورسعيد': {
                'name_en': 'Port Said',
                'code': 'PTS',
                'region': 'canal',
                'cities': [
                    {'name': 'بورسعيد', 'name_en': 'Port Said', 'is_capital': True},
                    {'name': 'بور فؤاد', 'name_en': 'Port Fouad', 'is_capital': False},
                ]
            },
            'الإسماعيلية': {
                'name_en': 'Ismailia',
                'code': 'ISM',
                'region': 'canal',
                'cities': [
                    {'name': 'الإسماعيلية', 'name_en': 'Ismailia', 'is_capital': True},
                    {'name': 'فايد', 'name_en': 'Fayed', 'is_capital': False},
                    {'name': 'القنطرة شرق', 'name_en': 'El Qantara Sharq', 'is_capital': False},
                    {'name': 'أبو صوير', 'name_en': 'Abu Sueir', 'is_capital': False},
                ]
            },
            'السويس': {
                'name_en': 'Suez',
                'code': 'SUZ',
                'region': 'canal',
                'cities': [
                    {'name': 'السويس', 'name_en': 'Suez', 'is_capital': True},
                    {'name': 'الأربعين', 'name_en': 'El Arbaeen', 'is_capital': False},
                    {'name': 'عتاقة', 'name_en': 'Ataqah', 'is_capital': False},
                ]
            },
            'شمال سيناء': {
                'name_en': 'North Sinai',
                'code': 'NSI',
                'region': 'sinai',
                'cities': [
                    {'name': 'العريش', 'name_en': 'El Arish', 'is_capital': True},
                    {'name': 'رفح', 'name_en': 'Rafah', 'is_capital': False},
                    {'name': 'الشيخ زويد', 'name_en': 'Sheikh Zuweid', 'is_capital': False},
                    {'name': 'بئر العبد', 'name_en': 'Bir El Abd', 'is_capital': False},
                ]
            },
            'جنوب سيناء': {
                'name_en': 'South Sinai',
                'code': 'SSI',
                'region': 'sinai',
                'cities': [
                    {'name': 'الطور', 'name_en': 'El Tor', 'is_capital': True},
                    {'name': 'شرم الشيخ', 'name_en': 'Sharm El Sheikh', 'is_capital': False},
                    {'name': 'دهب', 'name_en': 'Dahab', 'is_capital': False},
                    {'name': 'نويبع', 'name_en': 'Nuweiba', 'is_capital': False},
                    {'name': 'سانت كاترين', 'name_en': 'Saint Catherine', 'is_capital': False},
                ]
            },
            'البحر الأحمر': {
                'name_en': 'Red Sea',
                'code': 'RSE',
                'region': 'red_sea',
                'cities': [
                    {'name': 'الغردقة', 'name_en': 'Hurghada', 'is_capital': True},
                    {'name': 'سفاجا', 'name_en': 'Safaga', 'is_capital': False},
                    {'name': 'القصير', 'name_en': 'El Quseir', 'is_capital': False},
                    {'name': 'مرسى علم', 'name_en': 'Marsa Alam', 'is_capital': False},
                ]
            },
            'الفيوم': {
                'name_en': 'Fayoum',
                'code': 'FYM',
                'region': 'upper_egypt',
                'cities': [
                    {'name': 'الفيوم', 'name_en': 'Fayoum', 'is_capital': True},
                    {'name': 'سنورس', 'name_en': 'Sennoures', 'is_capital': False},
                    {'name': 'طامية', 'name_en': 'Tamiya', 'is_capital': False},
                    {'name': 'إطسا', 'name_en': 'Etsa', 'is_capital': False},
                ]
            },
            'بني سويف': {
                'name_en': 'Beni Suef',
                'code': 'BSW',
                'region': 'upper_egypt',
                'cities': [
                    {'name': 'بني سويف', 'name_en': 'Beni Suef', 'is_capital': True},
                    {'name': 'الواسطى', 'name_en': 'El Wasta', 'is_capital': False},
                    {'name': 'ناصر', 'name_en': 'Nasser', 'is_capital': False},
                    {'name': 'إهناسيا', 'name_en': 'Ehnasia', 'is_capital': False},
                ]
            },
            'المنيا': {
                'name_en': 'Minya',
                'code': 'MNY',
                'region': 'upper_egypt',
                'cities': [
                    {'name': 'المنيا', 'name_en': 'Minya', 'is_capital': True},
                    {'name': 'ملوي', 'name_en': 'Mallawi', 'is_capital': False},
                    {'name': 'سمالوط', 'name_en': 'Samalut', 'is_capital': False},
                    {'name': 'بني مزار', 'name_en': 'Beni Mazar', 'is_capital': False},
                    {'name': 'مغاغة', 'name_en': 'Maghagha', 'is_capital': False},
                ]
            },
            'أسيوط': {
                'name_en': 'Assiut',
                'code': 'AST',
                'region': 'upper_egypt',
                'cities': [
                    {'name': 'أسيوط', 'name_en': 'Assiut', 'is_capital': True},
                    {'name': 'ديروط', 'name_en': 'Dairut', 'is_capital': False},
                    {'name': 'القوصية', 'name_en': 'El Qusiya', 'is_capital': False},
                    {'name': 'منفلوط', 'name_en': 'Manfalut', 'is_capital': False},
                    {'name': 'أبنوب', 'name_en': 'Abnoub', 'is_capital': False},
                ]
            },
            'سوهاج': {
                'name_en': 'Sohag',
                'code': 'SOH',
                'region': 'upper_egypt',
                'cities': [
                    {'name': 'سوهاج', 'name_en': 'Sohag', 'is_capital': True},
                    {'name': 'أخميم', 'name_en': 'Akhmim', 'is_capital': False},
                    {'name': 'البلينا', 'name_en': 'El Balyana', 'is_capital': False},
                    {'name': 'المراغة', 'name_en': 'El Maragha', 'is_capital': False},
                    {'name': 'طما', 'name_en': 'Tama', 'is_capital': False},
                ]
            },
            'قنا': {
                'name_en': 'Qena',
                'code': 'QNA',
                'region': 'upper_egypt',
                'cities': [
                    {'name': 'قنا', 'name_en': 'Qena', 'is_capital': True},
                    {'name': 'الأقصر', 'name_en': 'Luxor', 'is_capital': False},
                    {'name': 'إسنا', 'name_en': 'Esna', 'is_capital': False},
                    {'name': 'قوص', 'name_en': 'Qus', 'is_capital': False},
                    {'name': 'نقادة', 'name_en': 'Naqada', 'is_capital': False},
                ]
            },
            'الأقصر': {
                'name_en': 'Luxor',
                'code': 'LXR',
                'region': 'upper_egypt',
                'cities': [
                    {'name': 'الأقصر', 'name_en': 'Luxor', 'is_capital': True},
                    {'name': 'إسنا', 'name_en': 'Esna', 'is_capital': False},
                    {'name': 'الطود', 'name_en': 'El Tod', 'is_capital': False},
                ]
            },
            'أسوان': {
                'name_en': 'Aswan',
                'code': 'ASW',
                'region': 'upper_egypt',
                'cities': [
                    {'name': 'أسوان', 'name_en': 'Aswan', 'is_capital': True},
                    {'name': 'إدفو', 'name_en': 'Edfu', 'is_capital': False},
                    {'name': 'كوم أمبو', 'name_en': 'Kom Ombo', 'is_capital': False},
                    {'name': 'دراو', 'name_en': 'Daraw', 'is_capital': False},
                ]
            },
            'الوادي الجديد': {
                'name_en': 'New Valley',
                'code': 'NVL',
                'region': 'new_valley',
                'cities': [
                    {'name': 'الخارجة', 'name_en': 'El Kharga', 'is_capital': True},
                    {'name': 'الداخلة', 'name_en': 'El Dakhla', 'is_capital': False},
                    {'name': 'الفرافرة', 'name_en': 'El Farafra', 'is_capital': False},
                    {'name': 'باريس', 'name_en': 'Paris', 'is_capital': False},
                ]
            },
            'مطروح': {
                'name_en': 'Matrouh',
                'code': 'MTR',
                'region': 'red_sea',
                'cities': [
                    {'name': 'مرسى مطروح', 'name_en': 'Marsa Matrouh', 'is_capital': True},
                    {'name': 'الحمام', 'name_en': 'El Hammam', 'is_capital': False},
                    {'name': 'العلمين', 'name_en': 'El Alamein', 'is_capital': False},
                    {'name': 'سيوة', 'name_en': 'Siwa', 'is_capital': False},
                ]
            },
        }

        governorates_created = 0
        cities_created = 0

        for gov_name, gov_data in egypt_data.items():
            # إنشاء المحافظة
            governorate, created = Governorate.objects.get_or_create(
                name=gov_name,
                defaults={
                    'name_en': gov_data['name_en'],
                    'code': gov_data['code'],
                    'region': gov_data['region']
                }
            )
            
            if created:
                governorates_created += 1
                self.stdout.write(f'تم إنشاء محافظة: {gov_name}')

            # إنشاء المدن
            for city_data in gov_data['cities']:
                city, created = City.objects.get_or_create(
                    name=city_data['name'],
                    governorate=governorate,
                    defaults={
                        'name_en': city_data['name_en'],
                        'is_capital': city_data['is_capital']
                    }
                )
                
                if created:
                    cities_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'تم إنشاء {governorates_created} محافظة و {cities_created} مدينة بنجاح!'
            )
        )
