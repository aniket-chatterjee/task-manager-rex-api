from django.core import exceptions


class InvalidOperation(Exception):
    pass


class PermissionDenied(PermissionError):
    pass
