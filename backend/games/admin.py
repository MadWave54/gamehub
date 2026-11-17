from django.contrib import admin

from .models import Comment, Favorite, Game, Genre, Platform, Post, WishlistItem


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('title', 'developer', 'release_year')
    search_fields = ('title', 'developer')
    list_filter = ('genres', 'platforms')


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'game', 'rating', 'pub_date')
    search_fields = ('title', 'author__username', 'game__title')
    list_filter = ('game__genres',)
    readonly_fields = ('favorites_total', 'short_code')
    inlines = (CommentInline,)

    @admin.display(description='В избранном у пользователей')
    def favorites_total(self, post):
        return post.favorites.count()


admin.site.register((Comment, Favorite, WishlistItem))
