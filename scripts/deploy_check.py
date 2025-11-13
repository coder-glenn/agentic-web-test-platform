import os
import time
import requests

FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
AGENT_URL = os.environ.get('AGENT_URL', 'http://localhost:8000')
EXECUTOR_URL = os.environ.get('EXECUTOR_URL', 'http://localhost:3000')

SERVICES = {
    'Frontend': FRONTEND_URL,
    'Agent API': AGENT_URL,
    'Executor API': EXECUTOR_URL
}

def check_service(name, url):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code < 400:
            print(f'✅ {name} reachable at {url}')
        else:
            print(f'⚠️ {name} returned status {r.status_code}')
    except Exception as e:
        print(f'❌ {name} unreachable at {url} ({e})')

if __name__ == '__main__':
    print('Checking AI Test Platform services...')
    time.sleep(3)  # wait a bit for containers to start
    for name, url in SERVICES.items():
        check_service(name, url)

    print('\nManual check:')
    print(f'1. Open frontend: {FRONTEND_URL}')
    print(f'2. Open Agent docs: {AGENT_URL}/docs')
    print(f'3. Check Executor: {EXECUTOR_URL}/docs')
