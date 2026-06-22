from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Profile, Interest, ReadingLog
from books.models import Library, Book, Holding
from .serializers import ProfileSerializer
from books.serializers import BookCardSerializer
from django.db.models import Prefetch

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

class InterestListView(APIView):
    def get(self, request):
        interests = Interest.objects.all()
        # You'll also need to import InterestSerializer from .serializers
        from .serializers import InterestSerializer
        serializer = InterestSerializer(interests, many=True)
        return Response(serializer.data)

class LibraryLogView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        logs = ReadingLog.objects.filter(user=request.user).select_related('book')
        
        try:
            library = request.user.profile.primary_library
        except Exception:
            library = None
            
        if library:
            prefetch = Prefetch('book__holdings', queryset=Holding.objects.filter(library=library), to_attr='user_holding')
            logs = logs.prefetch_related(prefetch)
            
        wish = []
        reading = []
        finished = []
        
        context = {'primary_library': library}
        
        for log in logs:
            card_data = BookCardSerializer(log.book, context=context).data
            if log.status == 'wish':
                wish.append(card_data)
            elif log.status == 'reading':
                reading.append(card_data)
            elif log.status == 'finished':
                card_data['rating'] = log.rating
                card_data['finished_at'] = log.created.isoformat()
                finished.append(card_data)
                
        return Response({
            "wish": wish,
            "reading": reading,
            "finished": finished
        })
        
class LibraryLogCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        isbn13 = request.data.get('isbn13')
        status = request.data.get('status')
        rating = request.data.get('rating')
        
        if not isbn13 or not status:
            return Response({"detail": "isbn13 and status are required"}, status=400)
            
        try:
            book = Book.objects.get(isbn13=isbn13)
        except Book.DoesNotExist:
            return Response({"detail": "Book not found"}, status=404)
            
        log, created = ReadingLog.objects.update_or_create(
            user=request.user,
            book=book,
            defaults={'status': status, 'rating': rating}
        )
        
        return Response({
            "isbn13": book.isbn13,
            "status": log.status,
            "rating": log.rating
        })

class LibraryToggleWishView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        isbn13 = request.data.get('isbn13')
        if not isbn13:
            return Response({"detail": "isbn13 is required"}, status=400)
            
        try:
            book = Book.objects.get(isbn13=isbn13)
        except Book.DoesNotExist:
            return Response({"detail": "Book not found"}, status=404)
            
        log = ReadingLog.objects.filter(user=request.user, book=book).first()
        
        if log:
            if log.status == 'wish':
                log.delete()
                wished = False
            else:
                log.status = 'wish'
                log.save()
                wished = True
        else:
            ReadingLog.objects.create(user=request.user, book=book, status='wish')
            wished = True
            
        return Response({
            "isbn13": book.isbn13,
            "wished": wished
        })
