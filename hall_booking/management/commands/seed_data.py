from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils import timezone
from hall_booking.models import (
    Governorate, City, Category, Hall, HallImage, HallManager, 
    Ingredient, IngredientImage, Meal, MealImage, MealIngredient, HallMeal, 
    AdditionalService, Booking, BookingService, BookingMeal, Notification, Contact
)
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
import os
import requests
from django.conf import settings
from datetime import datetime, timedelta
import random
from urllib.parse import urlparse

# Sample data for objects without requiring external images
SAMPLE_IMAGES = {
    'halls': [
        'halls/hall1.jpg',
        'halls/hall2.jpg',
        'halls/hall3.jpg',
    ],
    'meals': [
        'meals/meal1.jpg',
        'meals/meal2.jpg',
        'meals/meal3.jpg',
    ],
    'ingredients': [
        'ingredients/ingredient1.jpg',
        'ingredients/ingredient2.jpg',
        'ingredients/ingredient3.jpg',
    ]
}

def create_sample_image(path, model_name):
    """Create a sample image file in the media directory"""
    try:
        # Create directory if it doesn't exist
        dir_path = os.path.join(settings.MEDIA_ROOT, os.path.dirname(path))
        os.makedirs(dir_path, exist_ok=True)
        
        # Create an empty file as a placeholder
        full_path = os.path.join(settings.MEDIA_ROOT, path)
        with open(full_path, 'wb') as f:
            f.write(b'')  # Empty file
            
        return path
    except Exception as e:
        print(f"Error creating sample image {path}: {str(e)}")
        return None

class Command(BaseCommand):
    help = 'Seeds the database with initial data'

    def create_governorates_and_cities(self):
        """Create sample governorates and cities"""
        governorates = [
            {
                'name': 'الرياض',
                'name_en': 'Riyadh',
                'code': '01',
                'region': 'المنطقة الوسطى',
                'cities': ['الرياض', 'الدرعية', 'الخرج', 'الدوادمي']
            },
            {
                'name': 'مكة المكرمة',
                'name_en': 'Makkah',
                'code': '02',
                'region': 'المنطقة الغربية',
                'cities': ['مكة المكرمة', 'جدة', 'الطائف', 'القنفذة']
            },
            {
                'name': 'المدينة المنورة',
                'name_en': 'Madinah',
                'code': '03',
                'region': 'المنطقة الغربية',
                'cities': ['المدينة المنورة', 'ينبع', 'العلا', 'المدائن']
            }
        ]
        
        created_governorates = []
        for gov_data in governorates:
            gov = Governorate.objects.create(
                name=gov_data['name'],
                name_en=gov_data['name_en'],
                code=gov_data['code'],
                region=gov_data['region']
            )
            created_governorates.append(gov)
            
            # Create cities for this governorate
            for city_name in gov_data['cities']:
                City.objects.create(
                    name=city_name,
                    name_en=city_name,
                    governorate=gov,
                    is_capital=(city_name == gov_data['cities'][0])
                )
        
        return created_governorates
    
    def create_categories(self):
        """Create sample categories"""
        categories = [
            {'name': 'قاعات أفراح', 'description': 'قاعات حفلات الزفاف والمناسبات الكبيرة'},
            {'name': 'قاعات مؤتمرات', 'description': 'قاعات مخصصة للمؤتمرات والندوات'},
            {'name': 'قاعات مناسبات', 'description': 'قاعات للمناسبات العائلية والاجتماعات'},
            {'name': 'قاعات تدريب', 'description': 'قاعات مخصصة للدورات التدريبية وورش العمل'}
        ]
        
        return [Category.objects.create(**cat) for cat in categories]
    
    def create_ingredients(self):
        """Create sample ingredients with images"""
        ingredients = [
            {'name': 'أرز بسمتي', 'description': 'أرز هندي عالي الجودة', 'is_allergen': False},
            {'name': 'دجاج مشوي', 'description': 'صدر دجاج مشوي', 'is_allergen': False},
            {'name': 'لحم بقري', 'description': 'لحم بقري مشوي', 'is_allergen': False},
            {'name': 'جمبري', 'description': 'جمبري طازج', 'is_allergen': True},
            {'name': 'فطر', 'description': 'فطر طازج', 'is_allergen': False},
            {'name': 'بصل', 'description': 'بصل أحمر', 'is_allergen': False},
            {'name': 'ثوم', 'description': 'ثوم طازج', 'is_allergen': False},
            {'name': 'بهارات مشكلة', 'description': 'خليط بهارات', 'is_allergen': False},
            {'name': 'زبدة', 'description': 'زبدة طبيعية', 'is_allergen': True},
            {'name': 'زيت زيتون', 'description': 'زيت زيتون بكر ممتاز', 'is_allergen': False}
        ]
        
        created_ingredients = []
        for i, ing_data in enumerate(ingredients):
            # Create a sample image path
            img_path = f'ingredients/{ing_data["name"]}.jpg'
            img_path = create_sample_image(img_path, f'ingredient_{i}')
            
            # Create ingredient with main image
            ing = Ingredient.objects.create(
                name=ing_data['name'],
                description=ing_data['description'],
                is_allergen=ing_data['is_allergen']
            )
            
            # Add main image
            if img_path:
                ing.image = img_path
                ing.save()
                
                # Add additional images
                for j in range(2):  # Add 2 more images per ingredient
                    img_path = f'ingredients/{ing_data["name"]}_{j+1}.jpg'
                    img_path = create_sample_image(img_path, f'ingredient_{i}_{j}')
                    if img_path:
                        ing_img = IngredientImage.objects.create(
                            ingredient=ing,
                            image=img_path,
                            caption=f'صورة إضافية لـ {ing_data["name"]}',
                            is_primary=(j == 0)  # First additional image is primary
                        )
            
            created_ingredients.append(ing)
        
        return created_ingredients
    
    def create_meals(self, ingredients):
        """Create sample meals with ingredients and images"""
        meals = [
            {
                'name': 'كبسة دجاج',
                'description': 'أرز كبسة مع دجاج مشوي',
                'meal_type': 'lunch',
                'price_per_person': 35.0,
                'preparation_time': 60,
                'ingredients': [
                    {'ingredient': ingredients[0], 'quantity': '2 كوب', 'is_optional': False, 'notes': 'يغسل الأرز جيداً'},
                    {'ingredient': ingredients[1], 'quantity': '1 كيلو', 'is_optional': False, 'notes': 'متبل ومشوي'},
                    {'ingredient': ingredients[5], 'quantity': '2 حبة', 'is_optional': True, 'notes': 'مفروم ناعم'},
                    {'ingredient': ingredients[6], 'quantity': '5 فصوص', 'is_optional': False, 'notes': 'مهروس'},
                    {'ingredient': ingredients[7], 'quantity': 'ملعقة صغيرة', 'is_optional': False, 'notes': ''}
                ]
            },
            {
                'name': 'شاورما لحم',
                'description': 'شاورما لحم بقري مع خبز صاج',
                'meal_type': 'dinner',
                'price_per_person': 45.0,
                'preparation_time': 45,
                'ingredients': [
                    {'ingredient': ingredients[2], 'quantity': '1 كيلو', 'is_optional': False, 'notes': 'شرائح رفيعة'},
                    {'ingredient': ingredients[5], 'quantity': '3 حبة', 'is_optional': True, 'notes': 'حلقات'},
                    {'ingredient': ingredients[6], 'quantity': '1 رأس', 'is_optional': False, 'notes': 'مهروس'},
                    {'ingredient': ingredients[9], 'quantity': '3 ملاعق', 'is_optional': False, 'notes': 'للتشويح'}
                ]
            },
            {
                'name': 'سلطة سيزر',
                'description': 'سلطة سيزر مع دجاج مشوي',
                'meal_type': 'lunch',
                'price_per_person': 25.0,
                'preparation_time': 20,
                'ingredients': [
                    {'ingredient': ingredients[1], 'quantity': '500 جرام', 'is_optional': False, 'notes': 'مشوي ومقطع'},
                    {'ingredient': ingredients[4], 'quantity': '200 جرام', 'is_optional': True, 'notes': 'شرائح'},
                    {'ingredient': ingredients[5], 'quantity': '1 حبة', 'is_optional': False, 'notes': 'مقطع مكعبات'}
                ]
            }
        ]
        
        created_meals = []
        for i, meal_data in enumerate(meals):
            # Create a sample image path
            img_path = f'meals/{meal_data["name"]}.jpg'
            img_path = create_sample_image(img_path, f'meal_{i}')
            
            # Create meal with main image
            meal = Meal.objects.create(
                name=meal_data['name'],
                description=meal_data['description'],
                meal_type=meal_data['meal_type'],
                price_per_person=meal_data['price_per_person'],
                preparation_time=meal_data['preparation_time']
            )
            
            # Add main image
            if img_path:
                meal.image = img_path
                meal.save()
                
                # Add additional images
                for j in range(2):  # Add 2 more images per meal
                    img_path = f'meals/{meal_data["name"]}_{j+1}.jpg'
                    img_path = create_sample_image(img_path, f'meal_{i}_{j}')
                    if img_path:
                        meal_img = MealImage.objects.create(
                            meal=meal,
                            image=img_path,
                            caption=f'صورة إضافية لـ {meal_data["name"]}',
                            is_primary=(j == 0)  # First additional image is primary
                        )
            
            # Add ingredients to meal
            for ing_data in meal_data['ingredients']:
                MealIngredient.objects.create(
                    meal=meal,
                    ingredient=ing_data['ingredient'],
                    quantity=ing_data['quantity'],
                    is_optional=ing_data['is_optional'],
                    notes=ing_data.get('notes', '')
                )
            
            created_meals.append(meal)
        
        return created_meals
    
    def create_halls(self, governorates, categories):
        """Create sample halls with images"""
        halls_data = [
            {
                'name': 'قاعة الأفراح الملكية',
                'description': 'أفخم قاعات الأفراح في المدينة',
                'address': 'حي العليا، شارع الملك فهد',
                'price_per_hour': 2000.0,
                'capacity': 500,
                'governorate': governorates[0],
                'city': City.objects.filter(governorate=governorates[0]).first(),
                'category': categories[0],
                'features': {
                    'amenities': ['تكييف مركزي', 'شاشات عرض', 'موقف سيارات', 'خدمات استقبال', 'إضاءة متطورة'],
                    'rules': ['ممنوع التدخين', 'الالتزام بالموعد المحدد', 'ممنوع إحضار أطعمة من الخارج']
                },
                'status': 'available'
            },
            {
                'name': 'قاعة المؤتمرات الكبرى',
                'description': 'أحدث صيحة في قاعات المؤتمرات',
                'address': 'حي النخيل، شارع العليا العام',
                'price_per_hour': 1500.0,
                'capacity': 300,
                'governorate': governorates[1],
                'city': City.objects.filter(governorate=governorates[1]).first(),
                'category': categories[1],
                'features': {
                    'amenities': ['شاشات عرض', 'إنترنت لاسلكي', 'خدمات استقبال', 'تكييف مركزي'],
                    'rules': ['الالتزام بالزي الرسمي', 'الالتزام بالمواعيد']
                },
                'status': 'available'
            },
            {
                'name': 'منتجع المناسبات',
                'description': 'أجواء عائلية راقية',
                'address': 'حي الروضة، شارع الأمير محمد بن عبدالعزيز',
                'price_per_hour': 2500.0,
                'capacity': 700,
                'governorate': governorates[2],
                'city': City.objects.filter(governorate=governorates[2]).first(),
                'category': categories[2],
                'features': {
                    'amenities': ['حديقة خارجية', 'مسبح', 'مواقف واسعة', 'ملاعب أطفال'],
                    'rules': ['ممنوع إحضار أطعمة من الخارج', 'الالتزام بالمواعيد']
                },
                'status': 'available'
            }
        ]
        
        created_halls = []
        for i, hall_data in enumerate(halls_data):
            try:
                # Create the hall first without the image
                hall = Hall.objects.create(
                    name=hall_data['name'],
                    category=hall_data['category'],
                    governorate=hall_data['governorate'],
                    city=hall_data['city'],
                    address=hall_data['address'],
                    description=hall_data['description'],
                    capacity=hall_data['capacity'],
                    price_per_hour=hall_data['price_per_hour'],
                    status=hall_data['status'],
                    features=hall_data['features'],
                    phone=f'05{random.randint(10000000, 99999999)}',
                    email=f'info@hall{i+1}.com',
                    website=f'https://hall{i+1}.example.com',
                    latitude=24.7 + (i * 0.1),
                    longitude=46.7 + (i * 0.1)
                )
                
                # Create and set the main image
                img_path = f'halls/hall_{i+1}.jpg'
                img_path = create_sample_image(img_path, f'hall_{i}')
                if img_path:
                    hall.image = img_path
                    hall.save()
                
                # Create additional hall images
                self.create_hall_images(hall)
                
                # Assign manager to some halls
                if i % 2 == 0 and hasattr(self, 'manager_user'):
                    HallManager.objects.create(
                        user=self.manager_user,
                        hall=hall,
                        permission_level='manage',
                        is_active=True,
                        notes=f'مدير {hall.name}'
                    )
                
                created_halls.append(hall)
                print(f'Created hall: {hall.name}')
                
            except Exception as e:
                print(f'Error creating hall {hall_data.get("name", "")}: {str(e)}')
        
        return created_halls
    
    def create_hall_images(self, hall):
        """Create sample images for a hall"""
        image_types = ['main', 'gallery', 'interior', 'exterior', 'facilities']
        
        for i, img_type in enumerate(image_types):
            try:
                # Create a sample image path
                img_path = f'halls/{hall.id}_{img_type}_{i+1}.jpg'
                img_path = create_sample_image(img_path, f'{hall.name}_{img_type}')
                
                if img_path:
                    HallImage.objects.create(
                        hall=hall,
                        image=img_path,
                        image_type=img_type,
                        title=f'{img_type} {i+1}',
                        is_featured=(i == 0),
                        order=i
                    )
            except Exception as e:
                print(f"Error creating hall image: {str(e)}")
    
    def create_hall_meals(self, halls, meals):
        """Create sample hall meals with different prices"""
        hall_meals = []
        for hall in halls:
            for meal in meals:
                # Random price variation for each hall
                price_override = meal.price_per_person * random.uniform(0.8, 1.2)
                
                # Only set price_override 50% of the time to show both scenarios
                use_override = random.choice([True, False])
                
                hall_meals.append({
                    'hall': hall,
                    'meal': meal,
                    'price_override': round(price_override, 2) if use_override else None,
                    'is_available': random.choice([True, True, True, False]),  # 75% chance of being available
                    'min_order': random.choice([1, 5, 10]),
                    'max_order': random.choice([None, 50, 100, 200]),
                    'extra_notes': 'متوفر أيام نهاية الأسبوع فقط' if random.choice([True, False]) else ''
                })
        
        return [HallMeal.objects.create(**hm) for hm in hall_meals]
        
    def create_additional_services(self, halls):
        """Create sample additional services for halls"""
        services = []
        service_data = [
            {
                'name': 'خدمة الصوتيات',
                'description': 'نظام صوتي متكامل مع ميكروفونات',
                'price': 500.0,
                'price_unit': 'event',
                'service_type': 'equipment',
                'is_available': True
            },
            {
                'name': 'خدمة التصوير',
                'description': 'مصور محترف مع إضاءة احترافية',
                'price': 1000.0,
                'price_unit': 'hour',
                'service_type': 'photography',
                'is_available': True
            },
            {
                'name': 'خدمة الديكور',
                'description': 'تجهيز كامل للقاعة مع الديكورات',
                'price': 2000.0,
                'price_unit': 'event',
                'service_type': 'decoration',
                'is_available': True
            },
        ]
        
        for hall in halls:
            for service_item in service_data:
                service = service_item.copy()
                service['hall'] = hall
                services.append(AdditionalService.objects.create(**service))
        
    
    def create_hall_images(self, hall):
        """Create sample images for a hall"""
        image_types = ['main', 'gallery', 'interior', 'exterior', 'facilities']
        
        for i, img_type in enumerate(image_types):
            try:
                # Create a sample image path
                img_path = f'halls/{hall.id}_{img_type}_{i+1}.jpg'
                img_path = create_sample_image(img_path, f'{hall.name}_{img_type}')
                
                if img_path:
                    HallImage.objects.create(
                        hall=hall,
                        image=img_path,
                        image_type=img_type,
                        title=f'{img_type} {i+1}',
                        is_featured=(i == 0),
                        order=i
                    )
            except Exception as e:
                print(f"Error creating hall image: {str(e)}")
    
    def create_hall_meals(self, halls, meals):
        """Create sample hall meals with different prices"""
        hall_meals = []
        for hall in halls:
            for meal in meals:
                # Random price variation for each hall
                price_override = meal.price_per_person * random.uniform(0.8, 1.2)
                
                # Only set price_override 50% of the time to show both scenarios
                use_override = random.choice([True, False])
                
                hall_meals.append({
                    'hall': hall,
                    'meal': meal,
                    'price_override': round(price_override, 2) if use_override else None,
                    'is_available': random.choice([True, True, True, False]),  # 75% chance of being available
                    'min_order': random.choice([1, 5, 10]),
                    'max_order': random.choice([None, 50, 100, 200]),
                    'extra_notes': 'متوفر أيام نهاية الأسبوع فقط' if random.choice([True, False]) else ''
                })
        
        return [HallMeal.objects.create(**hm) for hm in hall_meals]
    
    def create_additional_services(self, halls):
        """Create sample additional services for halls"""
        services = []
        service_data = [
            {
                'name': 'خدمة الصوتيات',
                'description': 'نظام صوتي متكامل مع ميكروفونات',
                'price': 500.0,
                'price_unit': 'event',
                'service_type': 'equipment',
                'is_available': True
            },
            {
                'name': 'خدمة التصوير',
                'description': 'مصور محترف مع إضاءة احترافية',
                'price': 1000.0,
                'price_unit': 'hour',
                'service_type': 'photography',
                'is_available': True
            },
            {
                'name': 'خدمة الديكور',
                'description': 'تجهيز كامل للقاعة مع الديكورات',
                'price': 2000.0,
                'price_unit': 'event',
                'service_type': 'decoration',
                'is_available': True
            },
        ]
        
        for hall in halls:
            for service_item in service_data:
                service = service_item.copy()
                service['hall'] = hall
                services.append(AdditionalService.objects.create(**service))
        
        return services
    
    def create_bookings(self, halls, users, hall_meals, additional_services):
        """Create sample bookings with services and meals"""
        bookings = []
        status_choices = ['pending', 'approved', 'rejected', 'cancelled', 'completed']
        
        for i in range(10):  # Create 10 sample bookings
            try:
                hall = random.choice(halls)
                start_time = timezone.now() + timedelta(days=random.randint(-30, 30), hours=random.randint(9, 20))
                end_time = start_time + timedelta(hours=random.randint(2, 6))
                
                # Create customer data
                user = random.choice(users) if users and random.choice([True, False]) else None
                customer_name = f'عميل {i+1}'
                customer_email = f'customer{i+1}@example.com'
                customer_phone = f'05{random.randint(10000000, 99999999)}'
                
                # Create a booking
                booking = Booking.objects.create(
                    hall=hall,
                    user=user,
                    customer_name=customer_name,
                    customer_email=customer_email,
                    customer_phone=customer_phone,
                    event_title=f'مناسبة {i+1}',
                    event_description=f'وصف مناسبة {i+1} مع تفاصيل إضافية',
                    start_datetime=start_time,
                    end_datetime=end_time,
                    attendees_count=random.randint(10, 200),
                    status=random.choice(status_choices),
                    admin_notes='ملاحظات إدارية' if random.choice([True, False]) else None
                )
                
                # The total_price will be calculated automatically in the save() method
                
                # Add meals to booking if any are available for this hall
                hall_hall_meals = [hm for hm in hall_meals if hm.hall == hall and hm.is_available]
                if hall_hall_meals:
                    for _ in range(random.randint(1, min(3, len(hall_hall_meals)))):  # 1-3 meals per booking
                        meal = random.choice(hall_hall_meals)
                        BookingMeal.objects.create(
                            booking=booking,
                            hall_meal=meal,
                            quantity=random.randint(1, 5),
                            price_per_unit=meal.get_price(),
                            notes='ملاحظات خاصة بالوجبة' if random.choice([True, False]) else None
                        )
                
                # Add services to booking if any are available for this hall
                hall_services = [s for s in additional_services if s.hall == hall and s.is_available]
                if hall_services:
                    for _ in range(random.randint(0, min(2, len(hall_services)))):  # 0-2 services per booking
                        service = random.choice(hall_services)
                        BookingService.objects.create(
                            booking=booking,
                            service=service,
                            quantity=random.randint(1, 3),
                            price=service.price,
                            notes='ملاحظات خاصة بالخدمة' if random.choice([True, False]) else None
                        )
                
                # Refresh the booking to get the calculated total_price
                booking.refresh_from_db()
                bookings.append(booking)
                
            except Exception as e:
                print(f"Error creating booking {i+1}: {str(e)}")
        
        return bookings
    
    def create_contacts_and_notifications(self, users):
        """Create sample contacts and notifications"""
        # Create sample contacts
        for i in range(5):
            Contact.objects.create(
                name=f'مرسل {i+1}',
                email=f'sender{i+1}@example.com',
                subject=f'استفسار {i+1}',
                message=f'هذا نموذج استفسار رقم {i+1}',
                is_read=random.choice([True, False])
            )
        
        # Create sample notifications
        notification_types = ['booking_confirmation', 'payment_received', 'booking_reminder', 'new_message']
        for user in users:
            for i in range(3):  # 3 notifications per user
                Notification.objects.create(
                    user=user,
                    title=f'إشعار {i+1}',
                    message=f'هذا نموذج إشعار رقم {i+1}',
                    notification_type=random.choice(notification_types),
                    is_read=random.choice([True, False])
                )
        
        # Create sample notifications
        notification_types = ['booking_confirmation', 'payment_received', 'booking_reminder', 'new_message']
        for user in users:
            for i in range(3):  # 3 notifications per user
                Notification.objects.create(
                    user=user,
                    title=f'إشعار {i+1}',
                    message=f'هذا نموذج إشعار رقم {i+1}',
                    notification_type=random.choice(notification_types),
                    is_read=random.choice([True, False])
                )
    
    def handle(self, *args, **options):
        self.stdout.write('Seeding data...')
        
        # Clear existing data (except users and groups)
        self.stdout.write('Clearing existing data...')
        BookingMeal.objects.all().delete()
        BookingService.objects.all().delete()
        Booking.objects.all().delete()
        HallMeal.objects.all().delete()
        AdditionalService.objects.all().delete()
        HallManager.objects.all().delete()
        HallImage.objects.all().delete()
        Hall.objects.all().delete()
        MealIngredient.objects.all().delete()
        MealImage.objects.all().delete()
        Meal.objects.all().delete()
        IngredientImage.objects.all().delete()
        Ingredient.objects.all().delete()
        City.objects.all().delete()
        Governorate.objects.all().delete()
        Category.objects.all().delete()
        Contact.objects.all().delete()
        Notification.objects.all().delete()
        
        # Create groups if they don't exist
        admin_group, _ = Group.objects.get_or_create(name='Hall Admins')
        manager_group, _ = Group.objects.get_or_create(name='Hall Managers')
        
        # Create or get admin user
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            admin.groups.add(admin_group)
            self.stdout.write(self.style.SUCCESS('Created admin user'))
        
        # Create test manager user
        manager, created = User.objects.get_or_create(
            username='manager',
            defaults={
                'email': 'manager@example.com',
                'first_name': 'Hall',
                'last_name': 'Manager',
                'is_staff': False
            }
        )
        if created:
            manager.set_password('manager123')
            manager.save()
            manager.groups.add(manager_group)
            self.stdout.write(self.style.SUCCESS('Created manager user'))
        
        # Create test customer user
        customer, created = User.objects.get_or_create(
            username='customer',
            defaults={
                'email': 'customer@example.com',
                'first_name': 'Customer',
                'last_name': 'User',
                'is_staff': False
            }
        )
        if created:
            customer.set_password('customer123')
            customer.save()
            self.stdout.write(self.style.SUCCESS('Created customer user'))
        
        # Create sample data
        self.stdout.write('Creating governorates and cities...')
        governorates = self.create_governorates_and_cities()
        
        self.stdout.write('Creating categories...')
        categories = self.create_categories()
        
        self.stdout.write('Creating ingredients...')
        ingredients = self.create_ingredients()
        
        self.stdout.write('Creating meals...')
        meals = self.create_meals(ingredients)
        
        self.stdout.write('Creating halls...')
        halls = self.create_halls(governorates, categories)
        
        self.stdout.write('Creating additional services...')
        additional_services = self.create_additional_services(halls)
        
        self.stdout.write('Creating hall meals...')
        hall_meals = self.create_hall_meals(halls, meals)
        
        self.stdout.write('Creating bookings...')
        users = [admin, manager, customer]
        bookings = self.create_bookings(halls, users, hall_meals, additional_services)
        
        self.stdout.write('Creating contacts and notifications...')
        self.create_contacts_and_notifications(users)
        
        # Assign manager to halls
        for i, hall in enumerate(halls):
            if i == 0:  # Assign first hall to manager
                HallManager.objects.create(
                    user=manager,
                    hall=hall,
                    permission_level='full',
                    is_active=True
                )
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded the database!'))
        self.stdout.write(self.style.SUCCESS('Admin credentials:'))
        self.stdout.write(self.style.SUCCESS('  Username: admin'))
        self.stdout.write(self.style.SUCCESS('  Password: admin123'))
        self.stdout.write(self.style.SUCCESS('Manager credentials:'))
        self.stdout.write(self.style.SUCCESS('  Username: manager'))
        self.stdout.write(self.style.SUCCESS('  Password: manager123'))
        self.stdout.write(self.style.SUCCESS('Customer credentials:'))
        self.stdout.write(self.style.SUCCESS('  Username: customer'))
        self.stdout.write(self.style.SUCCESS('  Password: customer123'))
        
        # Create or get admin user
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
        admin.groups.add(admin_group)
        
        # Create or get manager user
        manager, created = User.objects.get_or_create(
            username='manager1',
            defaults={
                'email': 'manager1@example.com',
                'first_name': 'Hall',
                'last_name': 'Manager',
                'is_staff': True
            }
        )
        if created:
            manager.set_password('manager123')
            manager.save()
        manager.groups.add(manager_group)
        
        # Create or get regular user
        user, created = User.objects.get_or_create(
            username='user1',
            defaults={
                'email': 'user1@example.com',
                'first_name': 'Regular',
                'last_name': 'User'
            }
        )
        if created:
            user.set_password('user123')
            user.save()
        
        # Create governorates and cities
        cairo = Governorate.objects.create(
            name='القاهرة',
            name_en='Cairo',
            code='CAI',
            region='cairo'
        )
        
        giza = Governorate.objects.create(
            name='الجيزة',
            name_en='Giza',
            code='GIZ',
            region='cairo'
        )
        
        # Create cities
        nasr_city = City.objects.create(
            name='مدينة نصر',
            name_en='Nasr City',
            governorate=cairo,
            is_capital=False
        )
        
        dokki = City.objects.create(
            name='الدقي',
            name_en='Dokki',
            governorate=giza,
            is_capital=False
        )
        
        # Create categories
        wedding_hall = Category.objects.create(
            name='قاعات أفراح',
            description='أجمل قاعات الأفراح في القاهرة الكبرى',
            icon='fas fa-glass-cheers'
        )
        
        conference_hall = Category.objects.create(
            name='قاعات مؤتمرات',
            description='أفضل قاعات المؤتمرات والمعارض',
            icon='fas fa-chalkboard-teacher'
        )
        
        # Create ingredients
        chicken = Ingredient.objects.create(
            name='دجاج',
            description='لحم دجاج طازج',
            is_allergen=False
        )
        
        rice = Ingredient.objects.create(
            name='أرز',
            description='أرز مصري عالي الجودة',
            is_allergen=False
        )
        
        # Create meals
        koshari = Meal.objects.create(
            name='كشري',
            description='وجبة شعبية لذيذة',
            meal_type='lunch',
            price_per_person=50.00,
            is_available=True,
            preparation_time=30
        )
        koshari.ingredients.add(rice, through_defaults={'quantity': '200g', 'is_optional': False})
        
        chicken_meal = Meal.objects.create(
            name='فراخ مشوية',
            description='فراخ مشوية مع أرز',
            meal_type='dinner',
            price_per_person=120.00,
            is_available=True,
            preparation_time=45
        )
        chicken_meal.ingredients.add(chicken, rice, 
                                   through_defaults={'quantity': 'قطعة', 'is_optional': False})
        
        # Create halls
        royal_hall = Hall.objects.create(
            name='رويال هول',
            category=wedding_hall,
            governorate=cairo,
            city=nasr_city,
            address='شارع النصر، مدينة نصر',
            description='أفخم قاعات الأفراح في القاهرة',
            capacity=500,
            price_per_hour=5000.00,
            status='available',
            phone='01001234567',
            email='info@royalhall.com',
            website='https://royalhall.com',
            latitude=30.0626,
            longitude=31.3339
        )
        
        # Add hall images
        HallImage.objects.create(
            hall=royal_hall,
            image_type='main',
            title='صورة رئيسية للقاعة',
            is_featured=True,
            order=1
        )
        
        # Create hall manager
        hall_manager = HallManager.objects.create(
            user=manager,
            hall=royal_hall,
            permission_level='manage',
            is_active=True,
            notes='مدير القاعة الرئيسي'
        )
        
        # Create hall meals
        royal_meal = HallMeal.objects.create(
            hall=royal_hall,
            meal=koshari,
            is_available=True,
            price_override=60.00,
            min_order=10,
            max_order=100
        )
        
        # Create additional services
        photography = AdditionalService.objects.create(
            hall=royal_hall,
            name='خدمة التصوير',
            description='تصوير كامل للفعالية',
            service_type='photography',
            price=5000.00,
            price_unit='event',
            is_available=True,
            requires_approval=True
        )
        
        # Create booking
        booking = Booking.objects.create(
            hall=royal_hall,
            user=user,
            customer_name='محمد أحمد',
            customer_email='mohamed@example.com',
            customer_phone='01001234567',
            event_title='حفل زفاف',
            event_description='حفل زفاف محمد وسارة',
            start_datetime=timezone.now() + timedelta(days=30),
            end_datetime=timezone.now() + timedelta(days=30, hours=6),
            attendees_count=200,
            total_price=30000.00,
            status='pending'
        )
        
        # Add services to booking
        BookingService.objects.create(
            booking=booking,
            service=photography,
            quantity=1,
            price=5000.00,
            notes='تصوير كامل للحفل'
        )
        
        # Add meals to booking
        booking_meal = BookingMeal.objects.create(
            booking=booking,
            hall_meal=royal_meal,
            quantity=200,
            notes='بدون بهارات حارة'
        )
        # Calculate and update total price
        booking_meal.total_price = booking_meal.quantity * booking_meal.hall_meal.get_price()
        booking_meal.save()
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded the database!'))
