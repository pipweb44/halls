from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    help = 'Creates a test admin user for development purposes'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Create test admin user if not exists
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write(self.style.SUCCESS('Created admin user: admin / admin123'))
        else:
            self.stdout.write('Admin user already exists')
            
        # Create a test hall manager user if not exists
        if not User.objects.filter(username='manager').exists():
            manager = User.objects.create_user(
                username='manager',
                email='manager@example.com',
                password='manager123',
                first_name='Hall',
                last_name='Manager'
            )
            # Add to hall managers group if it exists
            try:
                managers_group = Group.objects.get(name='Hall Managers')
                manager.groups.add(managers_group)
                self.stdout.write(self.style.SUCCESS('Added manager user to Hall Managers group'))
            except Group.DoesNotExist:
                self.stdout.write('Hall Managers group does not exist')
            
            self.stdout.write(self.style.SUCCESS('Created manager user: manager / manager123'))
        else:
            self.stdout.write('Manager user already exists')
