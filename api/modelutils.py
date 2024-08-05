from django.db import models
from django.forms import ValidationError
from rest_framework import serializers
import io
import numpy as np
from pathlib import PurePath
import uuid


def get_user_spesific_path(filename, user, subfolder=None, suffix=None):
    if user and user.is_authenticated:
        path = PurePath("users", str(user.id))
    else:
        path = PurePath("anonymous", str(uuid.uuid4()))
    if subfolder is not None:
        path = path / subfolder
    path = path / filename
    if suffix is not None:
        path = path.with_suffix(suffix)
    return path


# Adapted from https://gist.github.com/fcoclavero/c6910eb18406afaf93e509f6342a0f37
class NdarrayField(models.BinaryField):
    description = "A field to store numpy ndarrays."

    # empty_array = (lambda f, a: (np.save(f, a), f)[1])(io.BytesIO(), np.array([])).getvalue()

    def get_db_prep_value(self, arr, *args, **kwargs):
        if arr is None:
            return None
        bytes_io = io.BytesIO()
        np.save(bytes_io, arr)
        return bytes_io.getvalue()

    def to_python(self, value):
        if value is None or isinstance(value, np.ndarray):
            return value
        try:
            return np.load(io.BytesIO(value))
        except (TypeError, ValueError):
            raise ValidationError("This value must be valid npy data.")

    def from_db_value(self, value, *args):
        return self.to_python(value)

    def to_representation(self, value):
        return value.to_list()


class NdarraySerializerField(serializers.Field):
    def to_representation(self, value):
        return value.tolist()

    def to_internal_value(self, data):
        return np.array(data)
