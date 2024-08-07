from django.utils import timezone
from rest_framework import viewsets, mixins, permissions


def get_request_user(request):
    return request.user if request.user.is_authenticated else None


class IsAuthenticatedToList(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == "list":
            return request.user.is_authenticated
        return True


# Filters queryset based on "user" field
# Requires authentication to list
class UsersReadOnlyModelViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    permission_classes = [IsAuthenticatedToList]
    user_field = "user"

    def get_queryset(self):
        user = get_request_user(self.request)
        filters = {self.user_field: user}
        return super().get_queryset().filter(**filters)


class UsersUnexpiredReadOnlyModelViewSet(UsersReadOnlyModelViewSet):  # Better name?
    expires_field = "expires"

    def get_queryset(self):
        filters = {self.expires_field + "__gt": timezone.now()}
        return super().get_queryset().filter(**filters)


# Filters queryset based on "user" field
# Requires authentication to list
# Sets user field on create (or None for anonymous)
class UsersCreateModelMixin(mixins.CreateModelMixin):
    def perform_create(self, serializer):
        user = get_request_user(self.request)
        return serializer.save(user=user)
