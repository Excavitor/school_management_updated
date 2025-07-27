from django.core.management.base import BaseCommand
from accounts.models import CustomUser, Role


class Command(BaseCommand):
    help = "Assign SuperAdmin role to Django superusers who don't have a role assigned"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force assign SuperAdmin role even if user already has a role",
        )

    def handle(self, *args, **options):
        """Assign SuperAdmin role to Django superusers."""

        try:
            # Get or create SuperAdmin role
            superadmin_role, created = Role.objects.get_or_create(
                name="SuperAdmin",
                defaults={
                    "description": "Full system access with all permissions",
                    "permissions": {
                        "can_view_dashboard": True,
                        # Notice permissions
                        "can_view_notice": True,
                        "can_add_notice": True,
                        "can_update_notice": True,
                        "can_delete_notice": True,
                        # Application permissions
                        "can_view_application": True,
                        "can_add_application": True,
                        "can_update_application": True,
                        "can_delete_application": True,
                        # User permissions
                        "can_view_user": True,
                        "can_add_user": True,
                        "can_update_user": True,
                        "can_delete_user": True,
                        # Role permissions
                        "can_view_role": True,
                        "can_add_role": True,
                        "can_update_role": True,
                        "can_delete_role": True,
                        # Other permissions
                        "can_export_data": True,
                        "can_view_reports": True,
                        "can_moderate_content": True,
                        "can_access_settings": True,
                    },
                },
            )

            if created:
                self.stdout.write(self.style.SUCCESS("Created SuperAdmin role"))

            # Find Django superusers
            if options["force"]:
                superusers = CustomUser.objects.filter(is_superuser=True)
                filter_msg = "all Django superusers"
            else:
                superusers = CustomUser.objects.filter(
                    is_superuser=True, role__isnull=True
                )
                filter_msg = "Django superusers without a role"

            if not superusers.exists():
                self.stdout.write(self.style.WARNING(f"No {filter_msg} found."))
                return

            updated_count = 0
            for user in superusers:
                old_role = user.role.name if user.role else "None"
                user.role = superadmin_role
                user.save()
                updated_count += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Assigned SuperAdmin role to {user.username} (was: {old_role})"
                    )
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully assigned SuperAdmin role to {updated_count} user(s)."
                )
            )

            # Show note about Django superuser functionality
            self.stdout.write(
                self.style.WARNING(
                    "\nNote: Django superusers automatically have all permissions "
                    "even without a role assigned. This command is optional and only "
                    "needed if you prefer explicit role assignment."
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
