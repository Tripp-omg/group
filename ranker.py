import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

ROBLOX_SECURITY_COOKIE = 'your_security_cookie_here'
GROUP_ID = 34681400
TARGET_ROLE_NAME = 'TargetRoleName'  
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

def get_users_in_group():
    users = []
    cursor = ""

    while True:
        response = requests.get(
            f'https://groups.roblox.com/v1/groups/{GROUP_ID}/users',
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

def update_user_role(user_id, target_role_id):
    try:
        response = requests.post(
            f'https://groups.roblox.com/v1/groups/{GROUP_ID}/users/{user_id}/roles/{target_role_id}',
            headers=HEADERS
        )
        response.raise_for_status()
        print(f"User with ID {user_id} assigned to role ID {target_role_id}.")
    except requests.RequestException as e:
        print(f"Failed to update user with ID {user_id}: {e}")

HEADERS['X-CSRF-TOKEN'] = get_csrf_token()

roles = get_group_roles()
target_role = next((role for role in roles if role['name'].lower() == TARGET_ROLE_NAME.lower()), None)

if not target_role:
    print(f"Role with name '{TARGET_ROLE_NAME}' not found. Please check the role name.")
else:
    target_role_id = target_role['id']
    users = get_users_in_group()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(update_user_role, user['userId'], target_role_id) for user in users]

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error ranking user: {e}")

print("Ranked everyone thats possible to rank lol.")
