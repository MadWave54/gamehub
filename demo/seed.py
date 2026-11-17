"""Наполнение GameHub тестовыми данными через REST API (как это делал бы клиент)."""
import base64
import io
import json
import sys
import urllib.request

from PIL import Image, ImageDraw, ImageFont

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8080'
LOG = []


def call(method, path, data=None, token=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method)
    req.add_header('Content-Type', 'application/json')
    if token:
        req.add_header('Authorization', f'Token {token}')
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read().decode()
            code = r.status
    except urllib.error.HTTPError as e:
        raw, code = e.read().decode(), e.code
    LOG.append(f'{method} {path} -> {code}')
    try:
        return code, json.loads(raw) if raw else None
    except json.JSONDecodeError:
        return code, raw


def cover(title, color):
    img = Image.new('RGB', (960, 540), color)
    d = ImageDraw.Draw(img)
    for i in range(0, 540, 6):
        shade = tuple(max(0, c - i // 6) for c in color)
        d.line([(0, i), (960, i)], fill=shade, width=6)
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 54)
    except OSError:
        font = ImageFont.load_default()
    d.text((60, 220), title, fill='white', font=font)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


users = [
    ('matvey@gamehub.ru', 'matvey_k', 'Матвей', 'Карпенко'),
    ('alina@gamehub.ru', 'alina_rpg', 'Алина', 'Смирнова'),
    ('pavel@gamehub.ru', 'pavel_fps', 'Павел', 'Волков'),
    ('kira@gamehub.ru', 'kira_indie', 'Кира', 'Гетьман'),
]
tokens = {}
ids = {}
for email, username, first, last in users:
    code, data = call('POST', '/api/users/', {
        'email': email, 'username': username, 'first_name': first,
        'last_name': last, 'password': 'Pixel-Quest-77',
    })
    ids[username] = data['id']
    _, tok = call('POST', '/api/auth/token/login/', {'email': email, 'password': 'Pixel-Quest-77'})
    tokens[username] = tok['auth_token']

_, games = call('GET', '/api/games/?limit=100')
game = {g['title']: g for g in games['results']}
_, platforms = call('GET', '/api/platforms/')
plat = {p['slug']: p['id'] for p in platforms}

posts = [
    ('alina_rpg', "Baldur's Gate 3", 'Лучшая RPG десятилетия', 'Свобода выбора, живые компаньоны и пошаговые бои, в которых важна каждая клетка поля. Прохождение за друида заняло больше сотни часов.', 10, 140, ['pc'], (120, 60, 160)),
    ('alina_rpg', 'Disco Elysium', 'Детектив, который читается как роман', 'Диалоги вместо сражений, 24 навыка-голоса в голове героя и открытый финал. Советую проходить без гайдов.', 9, 35, ['pc'], (170, 90, 40)),
    ('pavel_fps', 'Doom Eternal', 'Адреналин без пауз', 'Динамика выше, чем у предшественницы 2016 года: рывки, менеджмент ресурсов и саундтрек, под который хочется ускоряться.', 9, 28, ['pc', 'ps5'], (170, 40, 40)),
    ('pavel_fps', 'Counter-Strike 2', 'Как переход на Source 2 изменил CS', 'Новая дымовая механика и пересобранные карты. Матчмейкинг стал стабильнее, но к отдаче придётся привыкать заново.', 8, 900, ['pc'], (40, 80, 140)),
    ('kira_indie', 'Hollow Knight', 'Метроидвания, в которой хочется потеряться', 'Огромный подземный мир, сложные боссы и рисованная графика. Самая честная сложность среди инди.', 10, 62, ['switch', 'pc'], (40, 60, 90)),
    ('kira_indie', 'Stardew Valley', 'Ферма как способ отдохнуть', 'Неспешный цикл посадок, рыбалки и дружбы с жителями. Кооператив на четверых превращает игру в общий проект.', 9, 210, ['switch'], (60, 140, 70)),
    ('matvey_k', 'Factorio', 'Конвейер, который не отпускает', 'Автоматизация производства от ручной добычи руды до запуска ракеты. Отличная тренировка системного мышления.', 10, 320, ['pc'], (150, 110, 40)),
]
post_ids = []
for author, title, head, text, rating, hours, pl, color in posts:
    code, data = call('POST', '/api/posts/', {
        'game': game[title]['id'], 'title': head, 'text': text, 'image': cover(title, color),
        'rating': rating, 'hours_played': hours, 'platforms': [plat[p] for p in pl],
    }, tokens[author])
    assert code == 201, data
    post_ids.append(data['id'])

for follower, author in [('matvey_k', 'alina_rpg'), ('matvey_k', 'kira_indie'),
                         ('pavel_fps', 'alina_rpg'), ('kira_indie', 'pavel_fps')]:
    call('POST', f'/api/users/{ids[author]}/subscribe/', None, tokens[follower])

for user, idx in [('matvey_k', 0), ('matvey_k', 4), ('pavel_fps', 0), ('kira_indie', 2)]:
    call('POST', f'/api/posts/{post_ids[idx]}/favorite/', None, tokens[user])

comments = [
    ('matvey_k', 0, 'Согласен, особенно третий акт. За кого проходила?'),
    ('alina_rpg', 0, 'Тёмный соблазн, второй раз — паладин. Совсем другие диалоги!'),
    ('kira_indie', 2, 'На кошмаре пробовал? Мне Мародёр снится до сих пор.'),
    ('pavel_fps', 4, 'Сколько часов ушло на Пути боли?'),
    ('kira_indie', 4, 'Около восьми часов попыток, но оно того стоило.'),
]
for user, idx, text in comments:
    call('POST', f'/api/posts/{post_ids[idx]}/comments/', {'text': text}, tokens[user])

for title in ['Elden Ring', 'Hades', 'Celeste', 'Cyberpunk 2077']:
    call('POST', f"/api/games/{game[title]['id']}/wishlist/", None, tokens['matvey_k'])

json.dump({'tokens': tokens, 'ids': ids, 'posts': post_ids}, open(__import__('os').path.join(__import__('os').path.dirname(__file__), 'seed.json'), 'w'))
print('\n'.join(LOG[-12:]))
print('requests:', len(LOG), 'non-2xx:', [l for l in LOG if not l.split()[-1].startswith('2')])
