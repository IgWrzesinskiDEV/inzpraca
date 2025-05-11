from rest_framework import permissions


class IsAdminOrManagerCanEditDepartments(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user

        if view.action in ['update', 'partial_update']:
            if user.role == 'admin':
                return True
            elif user.role == 'kierownik':
                return obj.role == 'pracownik'
            else:
                return False

        return True
