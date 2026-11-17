from django.db.models import Avg, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from games.models import Comment, Favorite, Game, Genre, Platform, Post, WishlistItem
from users.models import Subscription, User

from .filters import GameFilter, PostFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, CommentSerializer, GameSerializer,
                          GenreSerializer, PlatformSerializer, PostReadSerializer,
                          PostWriteSerializer, ShortPostSerializer,
                          SubscriptionAuthorSerializer)


class UserViewSet(DjoserUserViewSet):
    """Пользователи: регистрация и профиль (Djoser) + аватар и подписки."""

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def avatar(self, request):
        user = request.user
        if request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        authors = User.objects.filter(subscribers__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = SubscriptionAuthorSerializer(
            page, many=True, context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, pk=id)
        if request.method == 'DELETE':
            deleted, _ = Subscription.objects.filter(
                user=request.user, author=author,
            ).delete()
            if not deleted:
                return Response({'errors': 'Подписки не было.'},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)
        if author == request.user:
            return Response({'errors': 'Нельзя подписаться на себя.'},
                            status=status.HTTP_400_BAD_REQUEST)
        _, created = Subscription.objects.get_or_create(user=request.user, author=author)
        if not created:
            return Response({'errors': 'Вы уже подписаны.'},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = SubscriptionAuthorSerializer(author, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class PlatformViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class GameViewSet(viewsets.ReadOnlyModelViewSet):
    """Справочник игр + список желаемого."""

    serializer_class = GameSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = GameFilter
    search_fields = ('title', 'developer')

    def get_queryset(self):
        return (
            Game.objects.prefetch_related('genres', 'platforms')
            .annotate(posts_count=Count('posts', distinct=True), avg_rating=Avg('posts__rating'))
            .order_by('title')
        )

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def wishlist(self, request, pk=None):
        game = get_object_or_404(Game, pk=pk)
        if request.method == 'DELETE':
            deleted, _ = WishlistItem.objects.filter(user=request.user, game=game).delete()
            if not deleted:
                return Response({'errors': 'Игры нет в списке желаемого.'},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)
        _, created = WishlistItem.objects.get_or_create(user=request.user, game=game)
        if not created:
            return Response({'errors': 'Игра уже в списке желаемого.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({'id': game.id, 'title': game.title}, status=status.HTTP_201_CREATED)

    @action(detail=False, permission_classes=[IsAuthenticated], url_path='download_wishlist')
    def download_wishlist(self, request):
        items = (
            WishlistItem.objects.filter(user=request.user)
            .select_related('game').prefetch_related('game__platforms')
            .order_by('game__title')
        )
        lines = [
            f'Список желаемого пользователя {request.user.username}',
            f'Сформирован {timezone.localtime():%d.%m.%Y %H:%M}', '',
        ]
        for number, item in enumerate(items, 1):
            platforms = ', '.join(p.name for p in item.game.platforms.all())
            lines.append(
                f'{number}. {item.game.title} ({item.game.release_year}), '
                f'{item.game.developer} — {platforms}'
            )
        lines += ['', f'Всего игр: {len(items)}']
        response = HttpResponse('\n'.join(lines), content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="wishlist.txt"'
        return response


class PostViewSet(viewsets.ModelViewSet):
    """Публикации-обзоры: CRUD, фильтры, избранное, короткая ссылка."""

    permission_classes = (IsAuthorOrReadOnly,)
    filterset_class = PostFilter

    def get_queryset(self):
        return (
            Post.objects.select_related('author', 'game')
            .prefetch_related('platforms')
            .annotate(comments_count=Count('comments'))
            .order_by('-pub_date')
        )

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return PostWriteSerializer
        return PostReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        post = get_object_or_404(Post, pk=pk)
        if request.method == 'DELETE':
            deleted, _ = Favorite.objects.filter(user=request.user, post=post).delete()
            if not deleted:
                return Response({'errors': 'Публикации нет в избранном.'},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)
        _, created = Favorite.objects.get_or_create(user=request.user, post=post)
        if not created:
            return Response({'errors': 'Публикация уже в избранном.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(ShortPostSerializer(post, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, url_path='get-link', permission_classes=[AllowAny])
    def get_link(self, request, pk=None):
        post = get_object_or_404(Post, pk=pk)
        url = request.build_absolute_uri(reverse('short-link', args=[post.short_code]))
        return Response({'short-link': url})

    @action(detail=False, permission_classes=[IsAuthenticated])
    def feed(self, request):
        """Лента: публикации авторов, на которых подписан пользователь."""
        queryset = self.get_queryset().filter(author__subscribers__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = PostReadSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    """Комментарии к публикации: /api/posts/{post_id}/comments/."""

    serializer_class = CommentSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = None

    def get_post(self):
        return get_object_or_404(Post, pk=self.kwargs['post_id'])

    def get_queryset(self):
        return Comment.objects.filter(post=self.get_post()).select_related('author')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, post=self.get_post())


def short_link_redirect(request, code):
    post = get_object_or_404(Post, short_code=code)
    return redirect(f'/api/posts/{post.pk}/')
