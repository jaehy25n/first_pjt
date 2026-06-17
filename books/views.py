from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Library
from .serializers import LibrarySearchSerializer

class LibraryListView(APIView):
    def get(self, request):
        queryset = Library.objects.all()
        q = request.query_params.get('q', None)
        if q:
            queryset = queryset.filter(name__icontains=q)
        serializer = LibrarySearchSerializer(queryset, many=True)
        return Response(serializer.data)
