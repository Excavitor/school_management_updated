from django.core.management.base import BaseCommand
from accounts.models import Role


class Command(BaseCommand):
    help = 'Set up default roles with proper permissions'

    def handle(self, *args, **options):
        """Create or update default roles with their permissions."""
        
        # Define default roles and their permissions
        default_roles = {
            'SuperAdmin': {
                'description': 'Full system access with all permissions',
                'permissions': {
                    'can_view_dashboard': True,
                    # Notice permissions
                    'can_view_notice': True,
                    'can_add_notice': True,
                    'can_update_notice': True,
                    'can_delete_notice': True,
                    # Application permissions
                    'can_view_application': True,
                    'can_add_application': True,
                    'can_update_application': True,
                    'can_delete_application': True,
                    # User permissions
                    'can_view_user': True,
                    'can_add_user': True,
                    'can_update_user': True,
                    'can_delete_user': True,
                    # Role permissions
                    'can_view_role': True,
                    'can_add_role': True,
                    'can_update_role': True,
                    'can_delete_role': True,
                    # Other permissions
                    'can_export_data': True,
                    'can_view_reports': True,
                    'can_moderate_content': True,
                    'can_access_settings': True,
                }
            },
            'Admin': {
                'description': 'Administrative access with most permissions except user/role management',
                'permissions': {
                    'can_view_dashboard': True,
                    # Notice permissions
                    'can_view_notice': True,
                    'can_add_notice': True,
                    'can_update_notice': True,
                    'can_delete_notice': True,
                    # Application permissions
                    'can_view_application': True,
                    'can_add_application': True,
                    'can_update_application': True,
                    'can_delete_application': True,
                    # User permissions (limited)
                    'can_view_user': False,
                    'can_add_user': False,
                    'can_update_user': False,
                    'can_delete_user': False,
                    # Role permissions (limited)
                    'can_view_role': False,
                    'can_add_role': False,
                    'can_update_role': False,
                    'can_delete_role': False,
                    # Other permissions
                    'can_export_data': True,
                    'can_view_reports': True,
                    'can_moderate_content': True,
                    'can_access_settings': False,
                }
            },
            'Teacher': {
                'description': 'Teacher access with limited permissions',
                'permissions': {
                    'can_view_dashboard': True,
                    # Notice permissions (read-only)
                    'can_view_notice': True,
                    'can_add_notice': False,
                    'can_update_notice': False,
                    'can_delete_notice': False,
                    # Application permissions (read-only)
                    'can_view_application': True,
                    'can_add_application': False,
                    'can_update_application': False,
                    'can_delete_application': False,
                    # User permissions (none)
                    'can_view_user': False,
                    'can_add_user': False,
                    'can_update_user': False,
                    'can_delete_user': False,
                    # Role permissions (none)
                    'can_view_role': False,
                    'can_add_role': False,
                    'can_update_role': False,
                    'can_delete_role': False,
                    # Other permissions
                    'can_export_data': False,
                    'can_view_reports': True,
                    'can_moderate_content': False,
                    'can_access_settings': False,
                }
            },

        }

        created_count = 0
        updated_count = 0

        for role_name, role_data in default_roles.items():
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={
                    'description': role_data['description'],
                    'permissions': role_data['permissions']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created role: {role_name}')
                )
            else:
                # Update existing role permissions
                role.description = role_data['description']
                role.permissions = role_data['permissions']
                role.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated role: {role_name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Setup complete! Created {created_count} roles, updated {updated_count} roles.'
            )
        )