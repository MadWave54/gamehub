import secrets

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Genre(models.Model):
    """Жанр игры (аналог тега в «Фудграме»)."""

    name = models.CharField('Название', max_length=64, unique=True)
    slug = models.SlugField('Слаг', max_length=64, unique=True)

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Platform(models.Model):
    """Игровая платформа: ПК, PlayStation, Xbox, Switch, мобильные."""

    name = models.CharField('Название', max_length=64, unique=True)
    slug = models.SlugField('Слаг', max_length=64, unique=True)

    class Meta:
        verbose_name = 'Платформа'
        verbose_name_plural = 'Платформы'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Game(models.Model):
    """Игра из справочника (аналог ингредиента; загружается из data/games.json)."""

    title = models.CharField('Название', max_length=200)
    developer = models.CharField('Разработчик', max_length=200)
    release_year = models.PositiveSmallIntegerField(
        'Год выхода', validators=[MinValueValidator(1970), MaxValueValidator(2100)],
    )
    genres = models.ManyToManyField(Genre, related_name='games', verbose_name='Жанры')
    platforms = models.ManyToManyField(
        Platform, related_name='games', verbose_name='Платформы',
    )

    class Meta:
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'
        ordering = ('title',)
        constraints = [
            models.UniqueConstraint(fields=('title', 'release_year'), name='unique_game'),
        ]

    def __str__(self):
        return f'{self.title} ({self.release_year})'


def generate_short_code():
    return secrets.token_urlsafe(4)[:6]


class Post(models.Model):
    """Публикация-обзор игры (аналог рецепта)."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts',
        verbose_name='Автор',
    )
    game = models.ForeignKey(
        Game, on_delete=models.PROTECT, related_name='posts', verbose_name='Игра',
    )
    title = models.CharField('Заголовок', max_length=256)
    text = models.TextField('Текст обзора')
    image = models.ImageField('Скриншот', upload_to='posts/')
    rating = models.PositiveSmallIntegerField(
        'Оценка (1–10)', validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    hours_played = models.PositiveIntegerField(
        'Наиграно часов', validators=[MinValueValidator(1)],
    )
    platforms = models.ManyToManyField(
        Platform, related_name='posts', verbose_name='Платформы, на которых играл автор',
    )
    short_code = models.CharField(
        'Код короткой ссылки', max_length=8, unique=True, default=generate_short_code,
        editable=False,
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'Публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('-pub_date',)
        default_related_name = 'posts'

    def __str__(self):
        return self.title


class Comment(models.Model):
    """Комментарий к публикации — основной канал общения пользователей."""

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comments', verbose_name='Публикация',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments',
        verbose_name='Автор',
    )
    text = models.TextField('Текст комментария', max_length=2000)
    created = models.DateTimeField('Дата', auto_now_add=True)

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('created',)

    def __str__(self):
        return f'{self.author}: {self.text[:30]}'


class UserPostRelation(models.Model):
    """Базовая связь «пользователь — публикация»."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Пользователь',
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, verbose_name='Публикация')

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'post'), name='unique_%(class)s',
            ),
        ]

    def __str__(self):
        return f'{self.user} — {self.post}'


class Favorite(UserPostRelation):
    class Meta(UserPostRelation.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorites'


class WishlistItem(models.Model):
    """Игра в списке желаемого пользователя (аналог списка покупок)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist',
        verbose_name='Пользователь',
    )
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name='in_wishlists', verbose_name='Игра',
    )
    added = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        verbose_name = 'Список желаемого'
        verbose_name_plural = 'Списки желаемого'
        constraints = [
            models.UniqueConstraint(fields=('user', 'game'), name='unique_wishlist_item'),
        ]

    def __str__(self):
        return f'{self.user} хочет {self.game}'
