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