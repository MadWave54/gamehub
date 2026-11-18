import base64
import io
from pathlib import Path

from django.core.management import call_command
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from games.models import Game, Platform, Post
from users.models import User


def tiny_png():
    buffer = io.BytesIO()
    Image.new('RGB', (8, 8), (40, 120, 200)).save(buffer, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode()


class GameHubApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        data_dir = Path(__file__).resolve().parents[1] / 'data'
        if not data_dir.exists():
            data_dir = Path(__file__).resolve().parents[2] / 'data'
        call_command('load_data', path=str(data_dir / 'games.json'), verbosity=0)
        cls.author = User.objects.create_user(
            email='author@example.com', username='author', password='StrongPass123',
            first_name='Анна', last_name='Автор',
        )
        cls.reader = User.objects.create_user(
            email='reader@example.com', username='reader', password='StrongPass123',
            first_name='Иван', last_name='Читатель',
        )
        cls.game = Game.objects.get(title='Hades')
        cls.pc = Platform.objects.get(slug='pc')

    def post_payload(self, **extra):
        payload = {
            'game': self.game.id, 'title': 'Лучший рогалик', 'text': 'Отличная боёвка.',
            'image': tiny_png(), 'rating': 9, 'hours_played': 60, 'platforms': [self.pc.id],
        }
        payload.update(extra)
        return payload

    def test_registration_and_token_login(self):
        response = self.client.post('/api/users/', {
            'email': 'new@example.com', 'username': 'newbie', 'first_name': 'Пётр',
            'last_name': 'Новый', 'password': 'StrongPass123',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post('/api/auth/token/login/', {
            'email': 'new@example.com', 'password': 'StrongPass123',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('auth_token', response.data)

    def test_guest_can_read_but_not_write(self):
        self.assertEqual(self.client.get('/api/games/').status_code, status.HTTP_200_OK)
        response = self.client.post('/api/posts/', self.post_payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_post_and_only_author_edits(self):
        self.client.force_authenticate(self.author)
        response = self.client.post('/api/posts/', self.post_payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        post_id = response.data['id']
        self.client.force_authenticate(self.reader)
        response = self.client.patch(f'/api/posts/{post_id}/', {'rating': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_wrong_platform_rejected(self):
        self.client.force_authenticate(self.author)
        switch_only = Game.objects.get(title__startswith='The Legend of Zelda')
        response = self.client.post(
            '/api/posts/', self.post_payload(game=switch_only.id), format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_subscribe_favorite_comment_wishlist(self):
        self.client.force_authenticate(self.author)
        post_id = self.client.post('/api/posts/', self.post_payload(), format='json').data['id']
        self.client.force_authenticate(self.reader)
        self.assertEqual(
            self.client.post(f'/api/users/{self.author.id}/subscribe/').status_code, 201,
        )
        self.assertEqual(self.client.get('/api/posts/feed/').data['count'], 1)
        self.assertEqual(self.client.post(f'/api/posts/{post_id}/favorite/').status_code, 201)
        self.assertEqual(self.client.post(f'/api/posts/{post_id}/favorite/').status_code, 400)
        response = self.client.post(
            f'/api/posts/{post_id}/comments/', {'text': 'Согласен!'}, format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.client.post(f'/api/games/{self.game.id}/wishlist/').status_code, 201)
        response = self.client.get('/api/games/download_wishlist/')
        self.assertIn('Hades', response.content.decode())
        self.assertEqual(Post.objects.get(pk=post_id).comments.count(), 1)
