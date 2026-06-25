from rest_framework import serializers
from .models import Article, Comment, ArticleLike


class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ('id', 'username', 'content', 'created_at', 'is_mine')
        read_only_fields = ('article', 'user')

    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False


class ArticleListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    comment_count = serializers.IntegerField(source='comments.count', read_only=True)
    like_count = serializers.IntegerField(source='likes.count', read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True, default=None)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ('id', 'title', 'username', 'created_at', 'comment_count', 'like_count', 'book_title', 'is_liked')

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class ArticleSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    comment_count = serializers.IntegerField(source='comments.count', read_only=True)
    like_count = serializers.IntegerField(source='likes.count', read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True, default=None)
    book_cover = serializers.URLField(source='book.cover_url', read_only=True, default=None)
    book_isbn = serializers.CharField(source='book.isbn13', read_only=True, default=None)
    is_liked = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()
    book_isbn13 = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Article
        fields = (
            'id', 'title', 'content', 'username', 'created_at', 'updated_at',
            'comments', 'comment_count', 'like_count',
            'book_title', 'book_cover', 'book_isbn', 'book_isbn13',
            'is_liked', 'is_mine',
        )
        read_only_fields = ('user',)

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False

    def create(self, validated_data):
        isbn = validated_data.pop('book_isbn13', None)
        book = None
        if isbn:
            from books.models import Book
            book = Book.objects.filter(isbn13=isbn).first()
        return Article.objects.create(book=book, **validated_data)

    def update(self, instance, validated_data):
        isbn = validated_data.pop('book_isbn13', None)
        if isbn is not None:
            from books.models import Book
            instance.book = Book.objects.filter(isbn13=isbn).first()
        return super().update(instance, validated_data)
