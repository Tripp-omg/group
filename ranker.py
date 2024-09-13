import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

ROBLOX_SECURITY_COOKIE = ''
GROUP_ID = 123456
TARGET_ROLE_NAME = 'name goes here'
MAX_WORKERS = 5 # increase if group is big, make sure u don't make it too much else ur computer will crash

HEADERS = {
    'Cookie': f'.ROBLOSECURITY={ROBLOX_SECURITY_COOKIE}',
    'Content-Type': 'application/json',
    'X-CSRF-TOKEN': ''
}

def get_csrf_token():
    response = requests.post('https://auth.roblox.com/v2/logout', headers=HEADERS)
    if response.status_code == 403:
        return response.headers['x-csrf-token']
    raise Exception("can't get csrf token")

def get_group_roles():
    response = requests.get(f'https://groups.roblox.com/v1/groups/{GROUP_ID}/roles', headers=HEADERS)
    response.raise_for_status()
    return response.json()['roles']

def get_role_id_by_name(role_name):
    roles = get_group_roles()
    for role in roles:
        if role['name'].lower() == role_name.lower():
            return role['id']
    raise ValueError(f"the '{role_name}' was not found")

def get_all_users():
    users = []
    cursor = None
    limit = 100

    while True:
        params = {'limit': limit}
        if cursor:
            params['cursor'] = cursor
        
        response = requests.get(
            f'https://groups.roblox.com/v1/groups/{GROUP_ID}/users',
            headers=HEADERS,
            params=params
        )
        response.raise_for_status()
        data = response.json()
        users.extend(data['data'])
        cursor = data.get('nextPageCursor')

        if not cursor:
            break

    return users

def change_user_role(user, role_id):
    user_id = user['user']['userId']
    try:
        response = requests.patch(
            f'https://groups.roblox.com/v1/groups/{GROUP_ID}/users/{user_id}',
            headers=HEADERS,
            json={'roleId': role_id}
        )
        response.raise_for_status()
        print(f"User with ID {user_id} promoted to {TARGET_ROLE_NAME}")
    except requests.RequestException as e:
        print(f"Failed to promote user with ID {user_id}: {e}. Response: {response.text if response else 'No response'}")

HEADERS['X-CSRF-TOKEN'] = get_csrf_token()

try:
    TARGET_ROLE_ID = get_role_id_by_name(TARGET_ROLE_NAME)
    print(f"Target role ID for '{TARGET_ROLE_NAME}' is {TARGET_ROLE_ID}")
except ValueError as e:
    print(e)
    exit(1)

all_users = get_all_users()

if all_users:
    print(f"loaded users")

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [executor.submit(change_user_role, user, TARGET_ROLE_ID) for user in all_users]
    
    for future in as_completed(futures):
        try:
            future.result()
        except Exception as e:
            print(f"Error ranking user: {e}")

print("All users have been ranked.")
