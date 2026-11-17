import django_filters
from django_filters import rest_framework as filters

from games.models import Game, Post


class GameFilter(filters.FilterSet):
    title = filters.CharFilter(field_name='title', lookup_expr='istartswith')
    genre = filters.CharFilter(field_name='genres__slug')
    platform = filters.CharFilter(field_name='platforms__slug')

    class Meta:
        model = Game
        fields = ('title', 'genre', 'platform', 'release_year')


class PostFilter(filters.FilterSet):
    author = filters.NumberFilter(field_name='author__id')
    game = filters.NumberFilter(field_name='game__id')
    genre = filters.CharFilter(field_name='game__genres__slug')
    min_rating = filters.NumberFilter(field_name='rating', lookup_expr='gte')
    is_favorited = django_filters.BooleanFilter(method='filter_favorited')

    class Meta:
        model = Post
        fields = ('author', 'game', 'genre', 'min_rating', 'is_favorited')

    def filter_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset
