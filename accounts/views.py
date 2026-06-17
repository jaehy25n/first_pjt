from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Profile, Interest
from books.models import Library
from .serializers import ProfileSerializer

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, created = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

class ProfileOnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        profile, created = Profile.objects.get_or_create(user=request.user)
        
        interest_ids = request.data.get('interest_ids')
        primary_library_code = request.data.get('primary_library_code')
        
        if interest_ids is not None:
            interests = Interest.objects.filter(id__in=interest_ids)
            profile.interests.set(interests)
            
        if primary_library_code is not None:
            try:
                library = Library.objects.get(lib_code=primary_library_code)
                profile.primary_library = library
            except Library.DoesNotExist:
                # If the library doesn't exist, we can ignore or return 400. 
                # For robustness, we just ignore invalid codes in this MVP.
                pass
                
        profile.save()
        
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
