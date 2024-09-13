import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

ROBLOX_SECURITY_COOKIE = '_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items.|_EA1C42A7DC3183D9AB7CC3C93164BFF04B69FFE23AB5287A6D94665069826CD46007D77665EFFF8E4A3C9EB88102CECD0C697B0EE476CB018DBD8B602FEFDD545F7977B5370F6018CD3B5C52DB49B82E664CDF5BA18722A25221854716F874A8FDEA7ABC817837E010FDF9CE7AB1B503C9FCACAE83AA197788781B95CD24161E3564D7FFEDF90269037A2AB8AC1CA5543E020B807A3475756CC3FFA182F96803F677AA6D9767B8676A4110BADBE213842647E90FBA510059AA8EFDCB5E25F72EFBB790C41CA956DAE8A46D2E528D8E380CDE22183EA323EBA7A7190C99A4A45F1AD094B1057DE96AA5DA1035385530770E46DBC23D88B7A98D1551C869E009CAB058FDAD649C5336D00D5F9750EC831A913537FBC9F8AD6BDC9545D9729B8CF3502607B162B9BB42394BF614EA90E82FEDB7614AC7E29744E88BFC3595259829BD57A437672EFA91A44B546913C8700109CB436F671AB97E8B02E6527065253017AEC269F4DE412A0DB0F86DC2BFAE5022903057BA31A6C1A337B71CCEFDAB81D75FC122AD99A761F619C63414280739700A75B0B60E9007A84B6B022B5FD59979D9AA95265FD1D2D469BDE6246C16E837F6E82E1BFE301B189CDC6F6563A41939E68D14028A4E3C8F85ADE2F32FCAF440F73FCB8875807C0F93CA486D820366003F6212DD99B34419339B74AB7061DB70E024EB595AF155387219A5867CB3D8CAE82938FB946BF22ADD91A5411268E53E28C30DE96D384EBC262216251EFE8D784BE7DFCD6777488CB298BD79170916BB79ADEF5EDF772E9949AC02409F260760B964A8145B1A9901B3FCF8BD6ED6485A7D2457E2C09F1F50F5E5C2A96B322D5844EBBE98DDC86F3A966425D5039F42C2DB50DE027C876F8CA6271EBB56B9C952753734CF4A4B35204570C1B0C4C4AC1DFD2302DAE45A30FF2AEC61EE846F53CF643E6119C8CCF941296A617FC98A341FA42AA029B77A5F1DC1231BE176803FE1C55FC286D119F31F0A69561F920A066A7B339EEAA373C5161DB0DA78198D6A2BD7E945C8368154597CF281CF38F9206003F8A8'
GROUP_ID = 5306497
TARGET_ROLE_NAME = 'The People'
MAX_WORKERS = 5

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
