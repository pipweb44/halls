from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hall_booking.models import (
    Governorate, City, Category, Hall, HallImage, HallManager, 
    HallService, HallMeal, Booking, BookingService, BookingMeal
)
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Load sample data for the hall booking system'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create superuser if not exists
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write('Created superuser: admin / admin123')

        # Create Governorates
        governorates_data = [
            {'name': 'القاهرة', 'name_en': 'Cairo', 'code': 'C', 'region': 'cairo'},
            {'name': 'الجيزة', 'name_en': 'Giza', 'code': 'GZ', 'region': 'cairo'},
            {'name': 'الاسكندرية', 'name_en': 'Alexandria', 'code': 'ALX', 'region': 'delta'},
        ]
        governorates = {}
        for data in governorates_data:
            gov = Governorate.objects.create(**data)
            governorates[gov.name] = gov
            self.stdout.write(f'Created governorate: {gov.name}')

        # Create Cities
        cities_data = [
            {'name': 'مدينة نصر', 'name_en': 'Nasr City', 'governorate': governorates['القاهرة'], 'is_capital': False},
            {'name': 'المعادي', 'name_en': 'Maadi', 'governorate': governorates['القاهرة'], 'is_capital': False},
            {'name': 'الدقي', 'name_en': 'Dokki', 'governorate': governorates['الجيزة'], 'is_capital': False},
            {'name': 'المنتزه', 'name_en': 'Montaza', 'governorate': governorates['الاسكندرية'], 'is_capital': False},
        ]
        cities = {}
        for data in cities_data:
            city = City.objects.create(**data)
            cities[city.name] = city
            self.stdout.write(f'Created city: {city.name}')

        # Create Categories
        categories_data = [
            {'name': 'قاعات أفراح', 'description': 'قاعات حفلات الأفراح والمناسبات الكبيرة'},
            {'name': 'قاعات مؤتمرات', 'description': 'قاعات المؤتمرات والندوات'},
            {'name': 'قاعات اجتماعات', 'description': 'قاعات الاجتماعات والتدريب'},
        ]
        categories = {}
        for data in categories_data:
            cat = Category.objects.create(**data)
            categories[cat.name] = cat
            self.stdout.write(f'Created category: {cat.name}')

        # Create Halls
        halls_data = [
            {
                'name': 'قاعة النخيل الملكية',
                'category': categories['قاعات أفراح'],
                'governorate': governorates['القاهرة'],
                'city': cities['مدينة نصر'],
                'address': 'شارع مصطفى النحاس، مدينة نصر',
                'description': 'أفخم قاعات الأفراح في القاهرة الكبرى',
                'capacity': 500,
                'price_per_hour': 5000,
                'status': 'available',
                'features': ['تكييف مركزي', 'شاشات عرض', 'إضاءة متطورة', 'موقف سيارات'],
                'phone': '01001234567',
                'email': 'info@alnakhil.com',
            },
            {
                'name': 'قاعة المؤتمرات الكبرى',
                'category': categories['قاعات مؤتمرات'],
                'governorate': governorates['الجيزة'],
                'city': cities['الدقي'],
                'address': 'شارع الدقي الرئيسي',
                'description': 'أكبر قاعات المؤتمرات في الجيزة',
                'capacity': 1000,
                'price_per_hour': 3000,
                'status': 'available',
                'features': ['صوتيات متطورة', 'ترجمة فورية', 'واي فاي مجاني', 'كافتيريا'],
                'phone': '01007654321',
                'email': 'info@conference-hall.com',
            },
        ]
        halls = {}
        for data in halls_data:
            # Extract features before creating hall
            features = data.pop('features')
            hall = Hall.objects.create(**data)
            hall.features = features  # Add features after creation
            hall.save()
            halls[hall.name] = hall
            self.stdout.write(f'Created hall: {hall.name}')

        # Create Hall Services
        services_data = [
            {'name': 'خدمة الصوتيات', 'description': 'نظام صوتي متكامل مع ميكروفونات', 'price': 1000, 'hall': halls['قاعة النخيل الملكية']},
            {'name': 'خدمة الإضاءة', 'description': 'إضاءة احترافية مع مؤثرات ضوئية', 'price': 1500, 'hall': halls['قاعة النخيل الملكية']},
            {'name': 'خدمة الترجمة', 'description': 'ترجمة فورية بثلاث لغات', 'price': 2000, 'hall': halls['قاعة المؤتمرات الكبرى']},
        ]
        services = {}
        for data in services_data:
            service = HallService.objects.create(**data)
            services[service.name] = service
            self.stdout.write(f'Created service: {service.name} for {service.hall.name}')

        # Create Hall Meals
        meals_data = [
            {
                'name': 'بوفيه فاخر',
                'description': 'بوفيه مفتوح بجميع أنواع المشويات والمقبلات',
                'meal_type': 'buffet',
                'price_per_person': 250,
                'is_vegetarian': False,
                'min_order': 50,
                'hall': halls['قاعة النخيل الملكية']
            },
            {
                'name': 'وجبة غداء',
                'description': 'وجبة غداء متكاملة تشمل مشوي ومقبلات وحلويات',
                'meal_type': 'lunch',
                'price_per_person': 150,
                'is_vegetarian': False,
                'min_order': 30,
                'hall': halls['قاعة المؤتمرات الكبرى']
            },
        ]
        meals = {}
        for data in meals_data:
            meal = HallMeal.objects.create(**data)
            meals[meal.name] = meal
            self.stdout.write(f'Created meal: {meal.name} for {meal.hall.name}')

        # Create Hall Managers
        managers_data = [
            {
                'user': User.objects.create_user('manager1', 'manager1@example.com', 'manager123', first_name='أحمد', last_name='محمد'),
                'hall': halls['قاعة النخيل الملكية'],
                'permission_level': 'manage'
            },
            {
                'user': User.objects.create_user('manager2', 'manager2@example.com', 'manager123', first_name='محمد', last_name='علي'),
                'hall': halls['قاعة المؤتمرات الكبرى'],
                'permission_level': 'manage'
            },
        ]
        for data in managers_data:
            manager = HallManager.objects.create(**data)
            self.stdout.write(f'Created manager: {manager.user.username} for {manager.hall.name}')

        # Create some bookings
        now = datetime.now()
        bookings_data = [
            {
                'hall': halls['قاعة النخيل الملكية'],
                'user': User.objects.get(username='admin'),
                'customer_name': 'أحمد السيد',
                'customer_email': 'ahmed@example.com',
                'customer_phone': '01001234567',
                'event_title': 'حفل زفاف',
                'event_description': 'حفل زفاف السيد/ أحمد والسيدة/ مريم',
                'start_datetime': now + timedelta(days=7),
                'end_datetime': now + timedelta(days=7, hours=6),
                'attendees_count': 300,
                'total_price': 30000,
                'status': 'approved'
            },
        ]
        for data in bookings_data:
            booking = Booking.objects.create(**data)
            
            # Add services to booking
            if booking.hall == halls['قاعة النخيل الملكية']:
                BookingService.objects.create(
                    booking=booking,
                    service=services['خدمة الصوتيات'],
                    quantity=1,
                    price=1000,
                    notes='مطلوب ميكروفونات لاسلكية'
                )
            
            # Add meals to booking
            if booking.hall == halls['قاعة النخيل الملكية']:
                BookingMeal.objects.create(
                    booking=booking,
                    meal=meals['بوفيه فاخر'],
                    quantity=300,
                    price_per_person=250,
                    total_price=75000,
                    serving_time=(now + timedelta(days=7, hours=3)).time(),
                    notes='يوجد 50 شخص نباتي'
                )
            
            self.stdout.write(f'Created booking: {booking.event_title} at {booking.hall.name}')

        self.stdout.write(self.style.SUCCESS('Successfully loaded sample data!'))
