import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

ROBLOX_SECURITY_COOKIE = 'your_security_cookie_here'
GROUP_ID = 34681400
MAX_WORKERS = 5

HEADERS = {
    'Cookie': f'.ROBLOSECURITY={ROBLOX_SECURITY_COOKIE}',
    'Content-Type': 'application/json',
    'X-CSRF-TOKEN': ''
}

def get_csrf_token():
    response = requests.post('https://auth.roblox.com/v2/logout', headers=HEADERS)
    if response.status_code == 403:
        return response.headers.get('x-csrf-token')
    raise Exception("Unable to retrieve CSRF token")

def get_group_roles():
    response = requests.get(f'https://groups.roblox.com/v1/groups/{GROUP_ID}/roles', headers=HEADERS)
    response.raise_for_status()
    return response.json().get('roles', [])

def get_users_in_role(role_id):
    users = []
    cursor = ""

    while True:
        response = requests.get(
            f'https://groups.roblox.com/v1/groups/{GROUP_ID}/roles/{role_id}/users',
            headers=HEADERS,
            params={"cursor": cursor}
        )
        response.raise_for_status()
        data = response.json()
        users.extend(data.get('data', []))
        cursor = data.get('nextPageCursor', '')

        if not cursor:
            break

    return users

def exile_user(user_id):
    try:
        response = requests.delete(
            f'https://groups.roblox.com/v1/groups/{GROUP_ID}/users/{user_id}',
            headers=HEADERS
        )
        response.raise_for_status()
        print(f"User with ID {user_id} exiled.")
    except requests.RequestException as e:
        print(f"Failed to exile user with ID {user_id}: {e}")

HEADERS['X-CSRF-TOKEN'] = get_csrf_token()

roles = get_group_roles()
roles_sorted = sorted(roles, key=lambda r: r['rank'])

bot_role = roles_sorted[0]

manageable_roles = [role for role in roles_sorted if role['rank'] > bot_role['rank']]

if not manageable_roles:
    print("No roles available to manage.")
else:
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for role in manageable_roles:
            users = get_users_in_role(role['id'])
            for user in users:
                futures.append(executor.submit(exile_user, user['userId']))

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error processing user: {e}")

print("All users from manageable roles have been exiled.")
