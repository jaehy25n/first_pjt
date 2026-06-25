from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Article, Comment, ArticleLike
from .serializers import ArticleListSerializer, ArticleSerializer, CommentSerializer


# ── 게시글 목록 / 작성 ─────────────────────────────────────────────────
@api_view(['GET', 'POST'])
def article_list(request):
    if request.method == 'GET':
        articles = Article.objects.select_related('user', 'book').prefetch_related('comments', 'likes')
        serializer = ArticleListSerializer(articles, many=True, context={'request': request})
        return Response(serializer.data)

    # POST — 로그인 필요
    if not request.user.is_authenticated:
        return Response({'detail': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
    serializer = ArticleSerializer(data=request.data, context={'request': request})
    if serializer.is_valid(raise_exception=True):
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ── 게시글 상세 / 수정 / 삭제 ─────────────────────────────────────────
@api_view(['GET', 'PUT', 'DELETE'])
def article_detail(request, article_id):
    article = get_object_or_404(
        Article.objects.select_related('user', 'book').prefetch_related('comments__user', 'likes'),
        pk=article_id
    )

    if request.method == 'GET':
        serializer = ArticleSerializer(article, context={'request': request})
        return Response(serializer.data)

    # 수정 / 삭제 — 본인만
    if not request.user.is_authenticated or article.user != request.user:
        return Response({'detail': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PUT':
        serializer = ArticleSerializer(article, data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)

    if request.method == 'DELETE':
        article.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── 좋아요 토글 ────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def article_like(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    like, created = ArticleLike.objects.get_or_create(user=request.user, article=article)
    if not created:
        like.delete()
        return Response({'liked': False, 'like_count': article.likes.count()})
    return Response({'liked': True, 'like_count': article.likes.count()})


# ── 댓글 작성 ─────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def comment_create(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    serializer = CommentSerializer(data=request.data, context={'request': request})
    if serializer.is_valid(raise_exception=True):
        serializer.save(article=article, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ── 댓글 삭제 ─────────────────────────────────────────────────────────
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def comment_delete(request, article_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, article_id=article_id)
    if comment.user != request.user:
        return Response({'detail': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
    comment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── 내 게시글 목록 ─────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_articles(request):
    articles = Article.objects.filter(user=request.user).select_related('book').prefetch_related('comments', 'likes')
    serializer = ArticleListSerializer(articles, many=True, context={'request': request})
    return Response(serializer.data)
