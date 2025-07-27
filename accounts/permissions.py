from rest_framework.permissions import BasePermission


class IsSuperAdminPermission(BasePermission):
    def has_permission(self, request, view):
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Django superusers have super admin permissions
        if request.user.is_superuser:
            return True
        
        try:
            return request.user.role and request.user.role.name == 'SuperAdmin'
        except AttributeError:
            return False
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsAdminOrSuperAdminPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Django superusers have admin or super admin permissions
        if request.user.is_superuser:
            return True
        
        try:
            return request.user.role and request.user.role.name in ['Admin', 'SuperAdmin']
        except AttributeError:
            return False
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsTeacherOrAbovePermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Django superusers have teacher or above permissions
        if request.user.is_superuser:
            return True
        
        try:
            return request.user.role and request.user.role.name in ['Teacher', 'Admin', 'SuperAdmin']
        except AttributeError:
            return False
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsOwnerOrAdminPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Django superusers have admin permissions
        if request.user.is_superuser:
            return True
            
        try:
            if request.user.role and request.user.role.name in ['Admin', 'SuperAdmin']:
                return True
        except AttributeError:
            pass
        
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False


# class IsGuestOrAbovePermission(BasePermission):
#     def has_permission(self, request, view):
#         return request.user and request.user.is_authenticated
    
#     def has_object_permission(self, request, view, obj):
#         return self.has_permission(request, view)

class CanViewDashboardPermission(BasePermission):
    """
    Grants permission to any authenticated user to view the dashboard.
    If a user has a role, it can be used to check for a specific 
    'can_view_dashboard' permission if needed for more granular control.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Any authenticated user (with or without a role) can view the dashboard.
        return True


# Dynamic role-based permissions
class HasRolePermission(BasePermission):
    """
    Base class for role-based permissions that check specific permission keys.
    """
    permission_key = None
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not self.permission_key:
            return False
            
        return request.user.has_role_permission(self.permission_key)
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class CanViewNoticePermission(HasRolePermission):
    permission_key = 'can_view_notice'


class CanAddNoticePermission(HasRolePermission):
    permission_key = 'can_add_notice'


class CanUpdateNoticePermission(HasRolePermission):
    permission_key = 'can_update_notice'


class CanDeleteNoticePermission(HasRolePermission):
    permission_key = 'can_delete_notice'


class CanViewApplicationPermission(HasRolePermission):
    permission_key = 'can_view_application'


class CanAddApplicationPermission(HasRolePermission):
    permission_key = 'can_add_application'


class CanUpdateApplicationPermission(HasRolePermission):
    permission_key = 'can_update_application'


class CanDeleteApplicationPermission(HasRolePermission):
    permission_key = 'can_delete_application'


class CanViewUserPermission(HasRolePermission):
    permission_key = 'can_view_user'


class CanAddUserPermission(HasRolePermission):
    permission_key = 'can_add_user'


class CanUpdateUserPermission(HasRolePermission):
    permission_key = 'can_update_user'


class CanDeleteUserPermission(HasRolePermission):
    permission_key = 'can_delete_user'


class CanViewRolePermission(HasRolePermission):
    permission_key = 'can_view_role'


class CanAddRolePermission(HasRolePermission):
    permission_key = 'can_add_role'


class CanUpdateRolePermission(HasRolePermission):
    permission_key = 'can_update_role'


class CanDeleteRolePermission(HasRolePermission):
    permission_key = 'can_delete_role'


class CanExportDataPermission(HasRolePermission):
    permission_key = 'can_export_data'


# Combined permissions for common use cases
class NoticeManagementPermission(BasePermission):
    """
    Permission for notice management operations.
    Checks appropriate permissions based on the HTTP method.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.method == 'GET':
            return request.user.has_role_permission('can_view_notice')
        elif request.method == 'POST':
            return request.user.has_role_permission('can_add_notice')
        elif request.method in ['PUT', 'PATCH']:
            return request.user.has_role_permission('can_update_notice')
        elif request.method == 'DELETE':
            return request.user.has_role_permission('can_delete_notice')
        
        return False
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class ApplicationManagementPermission(BasePermission):
    """
    Permission for application management operations.
    Checks appropriate permissions based on the HTTP method.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.method == 'GET':
            return request.user.has_role_permission('can_view_application')
        elif request.method == 'POST':
            return request.user.has_role_permission('can_add_application')
        elif request.method in ['PUT', 'PATCH']:
            return request.user.has_role_permission('can_update_application')
        elif request.method == 'DELETE':
            return request.user.has_role_permission('can_delete_application')
        
        return False
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)