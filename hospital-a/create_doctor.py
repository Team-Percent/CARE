
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
django.setup()

from care.users.models import User

def create_doctor(username, password, first_name, last_name):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "user_type": "doctor",
            "first_name": first_name,
            "last_name": last_name,
            "email": f"{username}@example.com",
            "phone_number": "+919999999999",
            "gender": "male",
            "verified": True,
        }
    )
    user.set_password(password)
    user.is_active = True
    user.save()
    if created:
        print(f"Created doctor: {username}")
    else:
        print(f"Updated doctor: {username}")

def reset_admin():
    admin = User.objects.filter(username="admin").first()
    if admin:
        admin.set_password("admin")
        admin.user_type = "administrator"
        admin.is_superuser = True
        admin.is_staff = True
        admin.is_active = True
        admin.save()
        print("Reset admin password to 'admin'")
    else:
        User.objects.create_superuser("admin", "admin@example.com", "admin")
        print("Created superuser 'admin' with password 'admin'")

if __name__ == "__main__":
    reset_admin()
    # For Hospital A
    if os.environ.get("HOSPITAL_ID") == "HOSP-CITYCARE-A":
        create_doctor("doctor_a", "doctor_a", "CityCare", "Doctor")
    # For Hospital B
    elif os.environ.get("HOSPITAL_ID") == "HOSP-METRO-B":
        create_doctor("doctor_b", "doctor_b", "Metro", "Doctor")
    else:
        # Generic fallback if env not set correctly in exec
        create_doctor("doctor", "doctor", "Generic", "Doctor")
