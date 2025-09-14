import os
import requests
from io import BytesIO
from django.core.files import File
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files.images import ImageFile
from hall_booking.models import Hall, Governorate, City, Category
from meal_system.hall_meals_models import HallMealCategory, HallMealComponent, HallMeal, HallMealComponentItem

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with sample meal data'

    def handle(self, *args, **options):
        self.stdout.write("Starting to populate database with sample meal data...")
        
        # Create test users if they don't exist
        admin_user = self.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create a governorate and city for the hall
        governorate = Governorate.objects.first() or Governorate.objects.create(name='القاهرة')
        city = City.objects.first() or City.objects.create(name='مدينة نصر', governorate=governorate)
        
        # Create a category for the hall if it doesn't exist
        category = Category.objects.first() or Category.objects.create(
            name='قاعات أفراح',
            description='قاعات حفلات وأفراح',
            icon='fas fa-glass-cheers'
        )
        
        # Create a test hall
        hall = Hall.objects.first() or Hall.objects.create(
            name='قاعة الفرح الكبير',
            description='أجمل قاعة أفراح في المدينة',
            address='123 شارع التحرير',
            capacity=500,
            price_per_hour=5000,
            status='available',
            governorate=governorate,
            city=city,
            phone='+201234567890',
            email='info@alforah.com',
            features=['تكييف', 'شاشة عرض', 'صوتيات', 'إضاءة', 'موقف سيارات'],
            category=category
        )
        
        # Sample meal categories with images
        categories = [
            {
                'name': 'مقبلات',
                'image_url': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd',
                'description': 'أشهى المقبلات الشرقية'
            },
            {
                'name': 'مشويات',
                'image_url': 'https://images.unsplash.com/photo-1555939594-78d4c082adf4',
                'description': 'ألذ المشويات على الفحم'
            },
            {
                'name': 'حلويات',
                'image_url': 'https://images.unsplash.com/photo-1551024601-bec78aea704c',
                'description': 'أشهى الحلويات الشرقية'
            },
            {
                'name': 'مشروبات',
                'image_url': 'https://images.unsplash.com/photo-1551024601-bec78aea704c',
                'description': 'أطيب المشروبات الباردة والساخنة'
            }
        ]
        
        # Sample components
        components = [
            # Starters
            {'name': 'سلطة يوناني', 'component_type': 'salad', 'price': 20, 'image_url': 'https://images.unsplash.com/photo-1541015409461-d186390f0b45'},
            {'name': 'متبل باذنجان', 'component_type': 'side', 'price': 15, 'image_url': 'https://images.unsplash.com/photo-1601050690597-df0568f70950'},
            {'name': 'حمص', 'component_type': 'side', 'price': 15, 'image_url': 'https://images.unsplash.com/photo-1597362925123-77861d3fbac7'},
            
            # Grills
            {'name': 'شيش طاووق', 'component_type': 'main', 'price': 50, 'image_url': 'https://images.unsplash.com/photo-1601050690597-df0568f70950'},
            {'name': 'كفتة مشوية', 'component_type': 'main', 'price': 60, 'image_url': 'https://images.unsplash.com/photo-1544025162-d76694265947'},
            {'name': 'شيش كباب', 'component_type': 'main', 'price': 70, 'image_url': 'https://images.unsplash.com/photo-1544025162-d76694265947'},
            
            # Desserts
            {'name': 'كنافة', 'component_type': 'dessert', 'price': 30, 'image_url': 'https://images.unsplash.com/photo-1610621063504-9eab03ac5b9b'},
            {'name': 'بقلاوة', 'component_type': 'dessert', 'price': 35, 'image_url': 'https://images.unsplash.com/photo-1563806259919-8d8c7c75f8d9'},
            
            # Drinks
            {'name': 'عصير برتقال', 'component_type': 'drink', 'price': 15, 'image_url': 'https://images.unsplash.com/photo-1621263764928-df1444c5e859'},
            {'name': 'عصير مانجو', 'component_type': 'drink', 'price': 20, 'image_url': 'https://images.unsplash.com/photo-1621263764928-df1444c5e859'},
        ]
        
        # Create categories
        created_categories = []
        for cat_data in categories:
            category, created = HallMealCategory.objects.get_or_create(
                hall=hall,
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'is_active': True,
                    'order': len(created_categories) + 1
                }
            )
            if created or not category.image:
                self.download_image(category, 'image', cat_data['image_url'])
            created_categories.append(category)
            self.stdout.write(f"{'Created' if created else 'Found'} category: {category.name}")
        
        # Create components
        created_components = []
        for comp_data in components:
            component, created = HallMealComponent.objects.get_or_create(
                hall=hall,
                name=comp_data['name'],
                defaults={
                    'component_type': comp_data['component_type'],
                    'price': comp_data['price'],
                    'is_available': True
                }
            )
            if created or not component.image:
                self.download_image(component, 'image', comp_data['image_url'])
            created_components.append(component)
            self.stdout.write(f"{'Created' if created else 'Found'} component: {component.name}")
        
        # Sample meals
        meals = [
            {
                'name': 'سفرة المشويات الكاملة',
                'category': 'مشويات',
                'description': 'سفرة متكاملة من أشهى المشويات',
                'price': 250,
                'components': ['شيش طاووق', 'كفتة مشوية', 'شيش كباب', 'سلطة يوناني', 'أرز بسمتي'],
                'image_url': 'https://images.unsplash.com/photo-1555939594-78d4c082adf4'
            },
            {
                'name': 'سفرة المقبلات',
                'category': 'مقبلات',
                'description': 'أشهى المقبلات الشرقية',
                'price': 150,
                'components': ['حمص', 'متبل باذنجان', 'سلطة يوناني'],
                'image_url': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd'
            },
            {
                'name': 'سفرة الحلويات',
                'category': 'حلويات',
                'description': 'أشهى الحلويات الشرقية',
                'price': 100,
                'components': ['كنافة', 'بقلاوة'],
                'image_url': 'https://images.unsplash.com/photo-1610621063504-9eab03ac5b9b'
            }
        ]
        
        # Create meals
        for meal_data in meals:
            category = HallMealCategory.objects.get(name=meal_data['category'], hall=hall)
            # Check if meal already exists
            meal, created = HallMeal.objects.get_or_create(
                hall=hall,
                name=meal_data['name'],
                category=category,
                defaults={
                    'description': meal_data['description'],
                    'base_price': meal_data['price'],
                    'is_available': True,
                    'min_components': 0,  # Default value for existing rows
                    'max_components': None,  # Default value for existing rows
                    'order_in_category': 1  # Default value
                }
            )
            if created:
                self.stdout.write(f"Created meal: {meal.name}")
            else:
                self.stdout.write(f"Found existing meal: {meal.name}")
            self.download_image(meal, 'image', meal_data['image_url'])
            
            # Add components to meal
            for comp_name in meal_data['components']:
                try:
                    component = HallMealComponent.objects.get(name=comp_name, hall=hall)
                    HallMealComponentItem.objects.create(
                        meal=meal,
                        component=component,
                        quantity=1,
                        is_optional=False
                    )
                except HallMealComponent.DoesNotExist:
                    self.stdout.write(f"Component {comp_name} not found for meal {meal.name}")
            
            self.stdout.write(f"Created meal: {meal.name}")
        
        self.stdout.write(self.style.SUCCESS('Successfully populated database with sample meal data!'))
    
    def create_user(self, username, email, password, **extra_fields):
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                **extra_fields
            )
            self.stdout.write(f"Created user: {username}")
            return user
        return User.objects.get(username=username)
    
    def download_image(self, obj, field_name, image_url):
        try:
            response = requests.get(image_url, stream=True)
            response.raise_for_status()
            
            # Get the image filename from the URL
            img_name = os.path.basename(image_url).split('?')[0] or 'image.jpg'
            img_extension = os.path.splitext(img_name)[1].lower()
            
            # Ensure we have a valid extension
            if not img_extension or img_extension not in ['.jpg', '.jpeg', '.png', '.gif']:
                img_name = f"{obj._meta.model_name}_{obj.id}.jpg"
            
            # Save the image to the model field
            img_file = BytesIO(response.content)
            getattr(obj, field_name).save(img_name, ImageFile(img_file), save=False)
            obj.save()
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error downloading image from {image_url}: {str(e)}"))
            return False
