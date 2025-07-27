from django.core.management.base import BaseCommand
from accounts.models import Role, CustomUser


class Command(BaseCommand):
    help = "Migrate users from Guest role to null role and remove Guest role"

    def handle(self, *args, **options):
        """Migrate Guest role users to null role and remove Guest role."""

        try:
            # Find the Guest role
            guest_role = Role.objects.get(name="Guest")

            # Find all users with Guest role
            guest_users = CustomUser.objects.filter(role=guest_role)
            user_count = guest_users.count()

            if user_count > 0:
                # Update all Guest users to have null role
                guest_users.update(role=None)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Migrated {user_count} users from Guest role to null role"
                    )
                )
            else:
                self.stdout.write(self.style.WARNING("No users found with Guest role"))

            # Delete the Guest role
            guest_role.delete()
            self.stdout.write(self.style.SUCCESS("Successfully deleted Guest role"))

        except Role.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(
                    "Guest role not found - migration already complete or role never existed"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Migration complete! Users with null roles now have default Guest permissions."
            )
        )
