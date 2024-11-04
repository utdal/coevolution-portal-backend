from django.utils import timezone
from rest_framework import viewsets, mixins, permissions


def get_request_user(request):
    return request.user if request.user.is_authenticated else None

def get_request_session(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


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
    # permission_classes = [IsAuthenticatedToList]
    user_field = "user"
    session_field = "session_key"

    def get_queryset(self):
        filters = {}

        if self.request.user.is_authenticated:
            filters = {self.user_field: self.request.user}
        else:
            session_key = get_request_session(self.request)
            filters = {self.session_field: session_key}
        
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
