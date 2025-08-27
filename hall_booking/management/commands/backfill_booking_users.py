from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hall_booking.models import Booking


class Command(BaseCommand):
    help = "Link existing bookings to users by matching customer_email with User.email"

    def handle(self, *args, **options):
        updated = 0
        unmatched = 0
        total = 0
        qs = Booking.objects.filter(user__isnull=True).exclude(customer_email="")
        total = qs.count()
        self.stdout.write(self.style.NOTICE(f"Scanning {total} bookings without user..."))

        for booking in qs.iterator():
            email = (booking.customer_email or "").strip()
            if not email:
                unmatched += 1
                continue
            try:
                user = User.objects.get(email__iexact=email)
                booking.user = user
                # normalizecustomer_email to user's actual email casing
                booking.customer_email = user.email
                booking.save(update_fields=["user", "customer_email"])
                updated += 1
            except User.DoesNotExist:
                unmatched += 1

        self.stdout.write(self.style.SUCCESS(f"Updated {updated} bookings."))
        self.stdout.write(self.style.WARNING(f"Unmatched {unmatched} bookings."))
        self.stdout.write(self.style.SUCCESS("Done."))
