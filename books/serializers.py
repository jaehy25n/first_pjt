from rest_framework import serializers
from .models import Library

class LibrarySearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Library
        fields = ['lib_code', 'name', 'region']
