import os
import shutil
from django.conf import settings

def reset_database():
    # Remove database file if exists
    db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed database file: {db_path}")
    
    # Remove all migration files except __init__.py
    migrations_dir = os.path.join(settings.BASE_DIR, 'hall_booking', 'migrations')
    if os.path.exists(migrations_dir):
        for filename in os.listdir(migrations_dir):
            file_path = os.path.join(migrations_dir, filename)
            if filename != '__init__.py' and filename != '__pycache__':
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Removed migration file: {file_path}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f"Removed migration directory: {file_path}")
    
    # Remove __pycache__ directories
    for root, dirs, files in os.walk(settings.BASE_DIR):
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            shutil.rmtree(cache_dir)
            print(f"Removed cache directory: {cache_dir}")

if __name__ == "__main__":
    import django
    import sys
    
    # Add the project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(project_root)
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'halls.settings')
    django.setup()
    reset_database()
    print("\nReset completed. Now run:")
    print("1. python3 manage.py makemigrations")
    print("2. python3 manage.py migrate")
    print("3. python3 manage.py createsuperuser")
