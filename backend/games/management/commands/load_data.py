"""Импорт справочников (жанры, платформы, игры) из JSON-файла.

Пример: python manage.py load_data --path ../data/games.json
Тот же формат может отдавать внешний каталог игр (интеграция данных).
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from games.models import Game, Genre, Platform


class Command(BaseCommand):
    help = 'Загружает жанры, платформы и игры из JSON'

    def add_arguments(self, parser):
        parser.add_argument('--path', default='data/games.json')

    @transaction.atomic
    def handle(self, *args, **options):
        data = json.loads(Path(options['path']).read_text(encoding='utf-8'))
        for item in data['genres']:
            Genre.objects.update_or_create(slug=item['slug'], defaults={'name': item['name']})
        for item in data['platforms']:
            Platform.objects.update_or_create(slug=item['slug'], defaults={'name': item['name']})
        for item in data['games']:
            game, _ = Game.objects.update_or_create(
                title=item['title'], release_year=item['release_year'],
                defaults={'developer': item['developer']},
            )
            game.genres.set(Genre.objects.filter(slug__in=item['genres']))
            game.platforms.set(Platform.objects.filter(slug__in=item['platforms']))
        self.stdout.write(self.style.SUCCESS(
            f'Загружено: жанров {Genre.objects.count()}, платформ '
            f'{Platform.objects.count()}, игр {Game.objects.count()}'
        ))
