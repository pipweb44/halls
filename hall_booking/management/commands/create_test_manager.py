from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from hall_booking.models import Hall, HallManager

class Command(BaseCommand):
    help = 'Create a test hall manager user for development'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Create or get test hall
        hall, created = Hall.objects.get_or_create(
            name='قاعة تجريبية',
            defaults={
                'capacity': 100,
                'price_per_hour': 500,
                'description': 'قاعة تجريبية للاختبار',
                'is_available': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created test hall: {hall.name}'))
        
        # Create or get test manager user
        username = 'manager1'
        email = 'manager1@example.com'
        password = 'manager123'
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': 'مدير',
                'last_name': 'القاعة',
                'is_staff': True
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created test manager user: {username}/{password}'))
        
        # Assign hall manager role
        manager, created = HallManager.objects.get_or_create(
            user=user,
            hall=hall,
            defaults={
                'is_active': True,
                'permissions': 'manage',
                'notes': 'Test manager account'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Assigned {username} as manager of {hall.name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'{username} is already a manager of {hall.name}'))
        
        self.stdout.write(self.style.SUCCESS('Test manager setup complete!'))
        self.stdout.write(self.style.SUCCESS(f'You can now log in at http://127.0.0.1:8000/login/ with:'))
        self.stdout.write(self.style.SUCCESS(f'Username: {username}'))
        self.stdout.write(self.style.SUCCESS(f'Password: {password}'))
