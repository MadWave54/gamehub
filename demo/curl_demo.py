"""Демонстрация запросов к API через curl.exe (входит в Windows 10/11).

Запуск: python demo/curl_demo.py [http://127.0.0.1:8000]
Печатает каждую команду и реальный ответ сервера.
"""
import json
import os
import subprocess
import sys

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8000'
HERE = os.path.dirname(os.path.abspath(__file__))
seed = json.load(open(os.path.join(HERE, 'seed.json'), encoding='utf-8'))
token = seed['tokens']['matvey_k']
me = seed['ids']['matvey_k']
auth = ['-H', f'Authorization: Token {token}']
short = token[:6] + '…'


def run(shown, args):
    print(f'> {shown}')
    res = subprocess.run(['curl.exe', '-s', '-w', '  [HTTP %{http_code}]'] + args,
                         capture_output=True)
    print(res.stdout.decode('utf-8', 'replace').strip())
    print()


run('curl -X POST /api/auth/token/login/ -d "email=matvey@gamehub.ru&password=***"',
    ['-X', 'POST', f'{BASE}/api/auth/token/login/',
     '-d', 'email=matvey@gamehub.ru&password=Pixel-Quest-77'])
run(f'curl -X POST /api/users/{me}/subscribe/ -H "Authorization: Token {short}"',
    ['-X', 'POST', f'{BASE}/api/users/{me}/subscribe/'] + auth)
zelda = 16
body = json.dumps({'game': zelda, 'title': 'Zelda на ПК?', 'text': 'тест', 'rating': 8,
                   'hours_played': 5, 'platforms': [1],
                   'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAf'
                            'FcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='})
run('curl -X POST /api/posts/ -H "Authorization: …" -d "{game: 16 (Zelda, только Switch), platforms: [ПК]}"',
    ['-X', 'POST', f'{BASE}/api/posts/', '-H', 'Content-Type: application/json',
     '--data-binary', body] + auth)
run('curl -X POST /api/posts/   (без токена)', ['-X', 'POST', f'{BASE}/api/posts/'])
print('> curl /api/games/download_wishlist/ -H "Authorization: …"')
res = subprocess.run(['curl.exe', '-s', f'{BASE}/api/games/download_wishlist/'] + auth,
                     capture_output=True)
print(res.stdout.decode('utf-8', 'replace'))
print()
link = json.loads(subprocess.run(['curl.exe', '-s', f'{BASE}/api/posts/{seed["posts"][0]}/get-link/'],
                                 capture_output=True).stdout)['short-link']
print(f'> curl -I {link}')
res = subprocess.run(['curl.exe', '-sI', link], capture_output=True).stdout.decode()
print('\n'.join(l for l in res.splitlines() if l.startswith(('HTTP', 'Location'))))
