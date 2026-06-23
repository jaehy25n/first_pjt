from rest_framework import serializers
from .models import Profile, Interest
from books.models import Library

class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ['id', 'name']

class PrimaryLibrarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Library
        fields = ['lib_code', 'name']

class ProfileSerializer(serializers.ModelSerializer):
    primary_library = PrimaryLibrarySerializer(read_only=True)
    libraries = PrimaryLibrarySerializer(many=True, read_only=True)
    interests = InterestSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = ['reading_goal', 'primary_library', 'libraries', 'interests']
