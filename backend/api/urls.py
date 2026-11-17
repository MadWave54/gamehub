from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CommentViewSet, GameViewSet, GenreViewSet, PlatformViewSet,
                    PostViewSet, UserViewSet)

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('genres', GenreViewSet, basename='genres')
router.register('platforms', PlatformViewSet, basename='platforms')
router.register('games', GameViewSet, basename='games')
router.register('posts', PostViewSet, basename='posts')
router.register(r'posts/(?P<post_id>\d+)/comments', CommentViewSet, basename='comments')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
