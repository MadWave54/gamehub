import base64
import uuid

from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer as DjoserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from games.models import Comment, Game, Genre, Platform, Post
from users.models import User


class Base64ImageField(serializers.ImageField):
    """Изображение, переданное строкой data:image/...;base64,... (как в «Фудграме»)."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            header, encoded = data.split(';base64,')
            ext = header.split('/')[-1]
            data = ContentFile(base64.b64decode(encoded), name=f'{uuid.uuid4().hex}.{ext}')
        return super().to_internal_value(data)


class UserCreateSerializer(DjoserCreateSerializer):
    class Meta(DjoserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password')


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(read_only=True)

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'bio',
            'is_subscribed', 'avatar',
        )
        read_only_fields = ('email',)

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        return bool(
            request and request.user.is_authenticated
            and request.user.subscriptions.filter(author=author).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('id', 'name', 'slug')


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform
        fields = ('id', 'name', 'slug')


class GameSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    platforms = PlatformSerializer(many=True, read_only=True)
    posts_count = serializers.IntegerField(read_only=True)
    avg_rating = serializers.FloatField(read_only=True)
    in_wishlist = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = (
            'id', 'title', 'developer', 'release_year', 'genres', 'platforms',
            'posts_count', 'avg_rating', 'in_wishlist',
        )

    def get_in_wishlist(self, game):
        request = self.context.get('request')
        return bool(
            request and request.user.is_authenticated
            and request.user.wishlist.filter(game=game).exists()
        )


class ShortGameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ('id', 'title', 'release_year')


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'author', 'text', 'created')


class PostReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    game = ShortGameSerializer(read_only=True)
    platforms = PlatformSerializer(many=True, read_only=True)
    image = serializers.ImageField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            'id', 'author', 'game', 'title', 'text', 'image', 'rating',
            'hours_played', 'platforms', 'comments_count', 'is_favorited', 'pub_date',
        )

    def get_is_favorited(self, post):
        request = self.context.get('request')
        return bool(
            request and request.user.is_authenticated
            and post.favorites.filter(user=request.user).exists()
        )


class PostWriteSerializer(serializers.ModelSerializer):
    game = serializers.PrimaryKeyRelatedField(queryset=Game.objects.all())
    platforms = serializers.PrimaryKeyRelatedField(
        queryset=Platform.objects.all(), many=True,
    )
    image = Base64ImageField()

    class Meta:
        model = Post
        fields = ('game', 'title', 'text', 'image', 'rating', 'hours_played', 'platforms')

    def validate_platforms(self, platforms):
        if not platforms:
            raise serializers.ValidationError('Укажите хотя бы одну платформу.')
        if len(platforms) != len(set(platforms)):
            raise serializers.ValidationError('Платформы не должны повторяться.')
        return platforms

    def validate(self, attrs):
        game = attrs.get('game') or getattr(self.instance, 'game', None)
        platforms = attrs.get('platforms')
        if game and platforms:
            wrong = [p.name for p in platforms if not game.platforms.filter(pk=p.pk).exists()]
            if wrong:
                raise serializers.ValidationError(
                    {'platforms': f'Игра не выходила на: {", ".join(wrong)}.'}
                )
        return attrs

    def to_representation(self, instance):
        return PostReadSerializer(instance, context=self.context).data


class ShortPostSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Post
        fields = ('id', 'title', 'image', 'rating')


class SubscriptionAuthorSerializer(UserSerializer):
    posts = serializers.SerializerMethodField()
    posts_count = serializers.IntegerField(source='posts.count', read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('posts', 'posts_count')

    def get_posts(self, author):
        limit = self.context['request'].query_params.get('posts_limit')
        posts = author.posts.all()
        if limit and limit.isdigit():
            posts = posts[:int(limit)]
        return ShortPostSerializer(posts, many=True, context=self.context).data
