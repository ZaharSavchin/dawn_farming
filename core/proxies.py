from core.utils import load_file_lines

def fetch_proxies():
    """Загрузка списка прокси из файла."""
    proxies = []
    lines = load_file_lines('data/proxies.txt')
    for line in lines:
        try:
            ip, port, user, password = line.split(':')
            proxy_url = f"http://{user}:{password}@{ip}:{port}"
            proxies.append({'http': proxy_url, 'https': proxy_url})
        except ValueError:
            print(f"Неверный формат прокси: {line}")
    return proxies


def fetch_proxies_farm():
    """Загрузка списка прокси из файла."""
    proxies = []
    lines = load_file_lines('data/proxies.txt')
    for line in lines:
        try:
            ip, port, user, password = line.split(':')
            proxy_url = f"http://{user}:{password}@{ip}:{port}"
            proxies.append({'http://': proxy_url, 'https://': proxy_url})
        except ValueError:
            print(f"Неверный формат прокси: {line}")
    return proxies


