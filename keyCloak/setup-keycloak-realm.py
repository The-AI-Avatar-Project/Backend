import requests
import json
import time
import random

KEYCLOAK_URL = "http://keycloak:8080"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "woommokence"

REALM_FILE = "/app/realm-setup.json"
USER_FILE = "/app/user-setup.json"
ROOM_FILE = "/app/room-setup.json"


# ----------------------------------------
# Utility: ConfigLoader
# ----------------------------------------

class ConfigLoader:
    @staticmethod
    def load(path):
        with open(path, "r") as f:
            return json.load(f)


# ----------------------------------------
# Utility: Keycloak API Wrapper
# ----------------------------------------

class KeycloakAdminClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.token = None
        self.wait_for_keycloak()
        self.token = self.get_admin_token()

    def wait_for_keycloak(self, timeout=120):
        print(f"Waiting for Keycloak at {self.base_url} ...")
        start = time.time()
        while time.time() - start < timeout:
            try:
                r = requests.get(self.base_url)
                if r.status_code in (200, 401):
                    print("Keycloak is up!")
                    return
            except Exception as e:
                print("Still waiting:", e)
            time.sleep(3)
        raise RuntimeError("Keycloak did not become available in time")

    def get_admin_token(self):
        url = f"{self.base_url}/realms/master/protocol/openid-connect/token"
        data = {
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": self.username,
            "password": self.password
        }
        resp = requests.post(url, data=data)
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _headers(self, extra=None):
        headers = {"Authorization": f"Bearer {self.token}"}
        if extra:
            headers.update(extra)
        return headers

    def request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"
        resp = requests.request(method, url, **kwargs)
        try:
            resp.raise_for_status()
        except requests.RequestException as e:
            #print(f"Request failed: {e}\nResponse: {resp.text}")
            raise
        return resp


# ----------------------------------------
# Realm, Client, Role Setup
# ----------------------------------------

class RealmManager:
    def __init__(self, client, realm_config):
        self.client = client
        self.config = realm_config
        self.realm = realm_config["realm"]

    def create_realm(self):
        data = {"realm": self.realm, "enabled": True}
        path = "/admin/realms"
        resp = self.client.request("POST", path, headers=self.client._headers({"Content-Type": "application/json"}), json=data)
        if resp.status_code in (201, 409):
            print(f"Realm '{self.realm}' created or already exists.")

    def create_clients(self):
        for client in self.config.get("clients", []):
            self.create_client(client)
            self.add_group_mapper(client["clientId"])
            self.add_language_mapper(client["clientId"])

    def create_client(self, data):
        path = f"/admin/realms/{self.realm}/clients"
        resp = self.client.request(
            "POST",
            path,
            headers=self.client._headers({"Content-Type": "application/json"}),
            json=data
        )
        if resp.status_code in (201, 409):
            print(f"Client '{data['clientId']}' created or already exists.")


    def assign_service_account_roles(self, client_id: str, role_names):
        headers=self.client._headers({"Content-Type": "application/json"}) 
        client_resp = self.client.request("GET", f"/admin/realms/{self.realm}/clients?clientId={client_id}", headers=headers)
        client = client_resp.json()[0]
        client_uuid = client["id"]

        sa_user_resp = self.client.request("GET", f"/admin/realms/{self.realm}/clients/{client_uuid}/service-account-user", headers=headers)
        service_account_id = sa_user_resp.json()["id"]

        mgmt_resp = self.client.request("GET", f"/admin/realms/{self.realm}/clients?clientId=realm-management", headers=headers)
        realm_mgmt_id = mgmt_resp.json()[0]["id"]

        roles_resp = self.client.request("GET", f"/admin/realms/{self.realm}/clients/{realm_mgmt_id}/roles", headers=headers)
        all_roles = roles_resp.json()

        desired_roles = [role for role in all_roles if role["name"] in role_names]
        if not desired_roles:
            raise ValueError(f"No matching roles found in realm-management for: {role_names}")

        assign_url = f"{KEYCLOAK_URL}/admin/realms/{self.realm}/users/{service_account_id}/role-mappings/clients/{realm_mgmt_id}"
        assign_resp = requests.post(assign_url, headers=headers, json=desired_roles)
        if assign_resp.status_code in (204, 409):
            print(f"Assigned admin API roles {role_names} to service account of client '{client_id}'.")
        else:
            raise RuntimeError(f"Failed to assign roles to service account: {assign_resp.text}")

    def add_group_mapper(self, client_id):
        client_resp = self.client.request("GET", f"/admin/realms/{self.realm}/clients?clientId={client_id}", headers=self.client._headers())
        client_uuid = client_resp.json()[0]["id"]

        mapper = {
            "name": "groups",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-group-membership-mapper",
            "consentRequired": False,
            "config": {
                "full.path": "true",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "userinfo.token.claim": "true",
                "claim.name": "groups",
                "jsonType.label": "String"
            }
        }

        url = f"/admin/realms/{self.realm}/clients/{client_uuid}/protocol-mappers/models"
        resp = self.client.request("POST", url, headers=self.client._headers({"Content-Type": "application/json"}), json=mapper)
        if resp.status_code in (201, 409):
            print("Group membership mapper created or already exists.")
    
    def add_language_mapper(self, client_id):
        client_resp = self.client.request("GET", f"/admin/realms/{self.realm}/clients?clientId={client_id}", headers=self.client._headers())
        client_uuid = client_resp.json()[0]["id"]

        mapper = {
            "name": "language",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-attribute-mapper",
            "consentRequired": False,
            "config": {
                "userinfo.token.claim": "true",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "claim.name": "language",
                "jsonType.label": "String",
                "user.attribute": "language"
            }
        }

        url = f"/admin/realms/{self.realm}/clients/{client_uuid}/protocol-mappers/models"
        resp = self.client.request("POST", url, headers=self.client._headers({"Content-Type": "application/json"}), json=mapper)
        if resp.status_code in (201, 409):
            print("Language mapper created or already exists.")


    def create_roles(self):
        for role in self.config.get("roles", []):
            self.create_role(role["name"])

    def create_role(self, name):
        url = f"/admin/realms/{self.realm}/roles"
        data = {"name": name}
        resp = self.client.request("POST", url, headers=self.client._headers({"Content-Type": "application/json"}), json=data)
        if resp.status_code in (201, 409):
            print(f"Role '{name}' created or already exists.")

    def set_user_profile_config(self):
        print("Setting user profile configuration ...")
        profile_config = {
            "attributes": [
                {
                    "name": "username",
                    "displayName": "${username}",
                    "required": {
                        "roles": ["user"]
                    },
                    "permissions": {
                        "view": ["admin", "user"],
                        "edit": ["admin", "user"]
                    },
                    "validations": {
                        "length": {"min": 3, "max": 255},
                        "username-prohibited-characters": {},
                        "up-username-not-idn-homograph": {}
                    },
                    "multivalued": False
                },
                {
                    "name": "email",
                    "displayName": "${email}",
                    "required": {
                        "roles": ["user"]
                    },
                    "permissions": {
                        "view": ["admin", "user"],
                        "edit": ["admin", "user"]
                    },
                    "validations": {
                        "email": {},
                        "length": {"max": 255}
                    },
                    "multivalued": False
                },
                {
                    "name": "firstName",
                    "displayName": "${firstName}",
                    "required": {
                        "roles": ["user"]
                    },
                    "permissions": {
                        "view": ["admin", "user"],
                        "edit": ["admin", "user"]
                    },
                    "validations": {
                        "length": {"max": 255},
                        "person-name-prohibited-characters": {}
                    },
                    "multivalued": False
                },
                {
                    "name": "lastName",
                    "displayName": "${lastName}",
                    "required": {
                        "roles": ["user"]
                    },
                    "permissions": {
                        "view": ["admin", "user"],
                        "edit": ["admin", "user"]
                    },
                    "validations": {
                        "length": {"max": 255},
                        "person-name-prohibited-characters": {}
                    },
                    "multivalued": False
                },
                {
                    "name": "language",
                    "displayName": "${language}",
                    "required": {
                        "roles": ["user"]
                    },
                    "permissions": {
                        "edit": ["admin"],
                        "view": ["admin", "user"]
                    },
                    "validations": {
                        "options": {
                            "options": ["de", "en", "fr"]
                        }
                    },
                    "multivalued": False
                }
            ],
            "groups": [
                {
                    "name": "user-metadata",
                    "displayHeader": "User metadata",
                    "displayDescription": "Attributes, which refer to user metadata"
                }
            ]
        }

        path = f"/admin/realms/{self.realm}/users/profile"
        self.client.request(
            "PUT",
            path,
            headers=self.client._headers({"Content-Type": "application/json"}),
            json=profile_config
        )
        print("User profile config set.")


# ----------------------------------------
# User Management
# ----------------------------------------

class UserManager:
    def __init__(self, client, realm, user_config):
        self.client = client
        self.realm = realm
        self.users = user_config.get("users", [])

    def create_users(self):
        for user in self.users:
            user_id = self.create_user(user)
            if "role" in user:
                self.assign_roles(user_id, user["role"])

    def create_user(self, user_data):
        first = user_data.get("firstName", "")
        last = user_data.get("lastName", "")
        role = user_data.get("role", [""])[0]
        domain = "stud.hs-ruhrwest.de" if role == "student" else "hs-ruhrwest.de"
        email = f"{first.lower()}.{last.lower()}@{domain}".replace(" ", "")

        user = {
            "username": user_data["username"],
            "enabled": user_data.get("enabled", True),
            "credentials": user_data.get("credentials", []),
            "firstName": first,
            "lastName": last,
            "email": email,
            "attributes": {
                "language": user_data.get("language", "de")
            }
        }

        path = f"/admin/realms/{self.realm}/users"
        resp = self.client.request("POST", path, headers=self.client._headers({"Content-Type": "application/json"}), json=user)
        if resp.status_code in (201, 409):
            print(f"User '{user['username']}' created or already exists.")

        get_url = f"/admin/realms/{self.realm}/users?username={user['username']}"
        resp = self.client.request("GET", get_url, headers=self.client._headers())
        return resp.json()[0]["id"]

    def assign_roles(self, user_id, role_names):
        roles = []
        for name in role_names:
            url = f"/admin/realms/{self.realm}/roles/{name}"
            resp = self.client.request("GET", url, headers=self.client._headers())
            roles.append({"id": resp.json()["id"], "name": name})

        url = f"/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm"
        self.client.request("POST", url, headers=self.client._headers({"Content-Type": "application/json"}), json=roles)
        print(f"Assigned roles {role_names} to user.")


# ----------------------------------------
# Group Management
# ----------------------------------------

class GroupManager:
    def __init__(self, client, realm, user_config, room_config):
        self.client = client
        self.realm = realm
        self.users = user_config["users"]
        self.rooms = room_config["classes"]

    def get_group_paths(self):
        paths = []
        for cls in self.rooms:
            if cls["year"] == 0:
                paths.append(cls["room_name"])
            else:
                paths.append(f"{cls['year']}/{cls['semester']}/{cls['roomowner']}/{cls['room_name']}")
        return paths

    def create_group_hierarchy(self, path):
        segments = path.strip("/").split("/")
        current_path = ""
        parent_id = None
        for seg in segments:
            current_path += f"/{seg}"
            group = self.get_group_by_path(current_path)
            if group:
                parent_id = group["id"]
            else:
                parent_id = self.create_group(seg, parent_id, current_path)

    def create_group(self, name, parent_id, full_path):
        url = f"/admin/realms/{self.realm}/groups"
        if parent_id:
            url += f"/{parent_id}/children"
        data = {"name": name}
        self.client.request("POST", url, headers=self.client._headers({"Content-Type": "application/json"}), json=data)
        print(f"Group '{full_path}' created or already exists.")
        return self.get_group_by_path(full_path)["id"]

    def get_group_by_path(self, path):
        path = "/" + path.strip("/")
        url = f"/admin/realms/{self.realm}/group-by-path{path}"
        try:
            resp = self.client.request("GET", url, headers=self.client._headers())
            return resp.json()
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def set_group_attributes(self):
        for cls in self.rooms:
            path = cls["room_name"] if cls["year"] == 0 else f"{cls['year']}/{cls['semester']}/{cls['roomowner']}/{cls['room_name']}"
            group = self.get_group_by_path(path)
            if not group:
                print(f"Group '{path}' not found.")
                continue
            group_id = group["id"]
            if "icon" in cls.get("attributes", {}):
                group.setdefault("attributes", {})["icon"] = [str(random.randint(1, 20))]
            owner_id = self.find_owner_id(cls["roomowner"])
            if owner_id:
                group["attributes"]["owner"] = [owner_id]

            self.client.request("PUT", f"/admin/realms/{self.realm}/groups/{group_id}", headers=self.client._headers({"Content-Type": "application/json"}), json=group)
            print(f"Updated attributes for group '{path}'.")

    def find_owner_id(self, last_name):
        for user in self.users:
            first = user.get("firstName", "")
            last = user.get("lastName", "")
            domain = "stud.hs-ruhrwest.de" if "student" in user.get("role", []) else "hs-ruhrwest.de"
            email = f"{first.lower()}.{last.lower()}@{domain}".replace(" ", "")
            if user.get("lastName") == last_name and "roomowner" in user.get("role", []):
                resp = self.client.request("GET", f"/admin/realms/{self.realm}/users", headers=self.client._headers(), params={"email": email})
                return resp.json()[0]["id"] if resp.json() else None
        return None

    def assign_students_to_random_classes(self, count_per_student=1):
        print(f"Assigning each student to {count_per_student} random classes...")
        group_paths = self.get_group_paths()

        for user in self.users:
            if "student" not in user.get("role", []):
                continue

            user_id = self.get_user_id(user)
            if not user_id:
                print(f"Could not find ID for student: {user.get('username')}")
                continue

            selected_paths = random.sample(group_paths, k=min(count_per_student, len(group_paths)))

            for path in selected_paths:
                group = self.get_group_by_path(path)
                if not group:
                    print(f"Group '{path}' not found, skipping.")
                    continue

                url = f"/admin/realms/{self.realm}/users/{user_id}/groups/{group['id']}"
                self.client.request("PUT", url, headers=self.client._headers())
                print(f"Added user '{user['username']}' to group '{path}'.")

    def get_user_id(self, user_obj):
        first = user_obj.get("firstName", "")
        last = user_obj.get("lastName", "")
        domain = "stud.hs-ruhrwest.de" if "student" in user_obj.get("role", []) else "hs-ruhrwest.de"
        email = f"{first.lower()}.{last.lower()}@{domain}".replace(" ", "")

        resp = self.client.request(
            "GET",
            f"/admin/realms/{self.realm}/users",
            headers=self.client._headers(),
            params={"email": email}
        )

        if resp.status_code == 200 and resp.json():
            return resp.json()[0]["id"]
        return None



# ----------------------------------------
# Runner / Main Setup Class
# ----------------------------------------

class KeycloakSetup:
    def __init__(self):
        self.client = KeycloakAdminClient(KEYCLOAK_URL, ADMIN_USERNAME, ADMIN_PASSWORD)
        self.realm_config = ConfigLoader.load(REALM_FILE)
        self.user_config = ConfigLoader.load(USER_FILE)
        self.room_config = ConfigLoader.load(ROOM_FILE)

        self.realm_mgr = RealmManager(self.client, self.realm_config)
        self.user_mgr = UserManager(self.client, self.realm_config["realm"], self.user_config)
        self.group_mgr = GroupManager(self.client, self.realm_config["realm"], self.user_config, self.room_config)

    def check_initialization(self):
        realm = self.realm_config["realm"]
        headers = {"Authorization": f"Bearer {self.client.token}"}

        realm_url = f"{KEYCLOAK_URL}/admin/realms/{realm}"
        realm_exists = requests.get(realm_url, headers=headers).status_code == 200

        all_paths = self.group_mgr.get_group_paths()
        missing_paths = []
        for path in all_paths:
            group_check_path = "/" + path.strip("/")
            url = f"{KEYCLOAK_URL}/admin/realms/{realm}/group-by-path{group_check_path}"
            resp = requests.get(url, headers=headers)
            if resp.status_code != 200:
                missing_paths.append(path)
        groups_exist = len(missing_paths) == 0

        users_url = f"{KEYCLOAK_URL}/admin/realms/{realm}/users"
        expected_usernames = set(u["username"] for u in self.user_config.get("users", []))
        users_resp = requests.get(users_url, headers=headers)
        actual_usernames = set(u["username"] for u in users_resp.json()) if users_resp.status_code == 200 else set()
        users_exist = expected_usernames.issubset(actual_usernames)

        checks = {"realm": realm_exists, "groups": groups_exist, "users": users_exist}
        missing = [k for k, v in checks.items() if not v]
        existing = [k for k, v in checks.items() if v]

        if all(checks.values()):
            print("Realm, users, and groups have already been initialized.")
            return "all_exists"
        if all(not v for v in checks.values()):
            return "none_exist"

        msg = (
            "Database is corrupted or was faulty installed.\n"
            f"Existing: {', '.join(existing)}\n"
            f"Missing: {', '.join(missing)}"
        )
        raise RuntimeError(msg)


    def run(self):
        status = self.check_initialization()
        if status == "none_exist":
            self.realm_mgr.create_realm()
            self.realm_mgr.create_clients()
            self.realm_mgr.set_user_profile_config()
            self.realm_mgr.create_roles()
            self.realm_mgr.assign_service_account_roles(
                client_id="backend-client",
                role_names=["view-realm", "view-users", "query-groups", "realm-admin"]
            )
            for path in self.group_mgr.get_group_paths():
                self.group_mgr.create_group_hierarchy(path)
            self.user_mgr.create_users()
            self.group_mgr.set_group_attributes()
            self.group_mgr.assign_students_to_random_classes()
            
            print("Keycloak setup completed.")


if __name__ == "__main__":
    KeycloakSetup().run()
