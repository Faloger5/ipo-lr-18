from rest_framework import permissions

class IsAdminOrManager(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if hasattr(request.user, 'profile'):
            return request.user.profile.role in ['admin', 'manager']
        
        return request.user.is_superuser
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        if hasattr(request.user, 'profile') and request.user.profile.role == 'admin':
            return True
        
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False