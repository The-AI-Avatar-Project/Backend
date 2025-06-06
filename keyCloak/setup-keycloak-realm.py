import requests
import json
import time

KEYCLOAK_URL = "http://keycloak:8080"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "secret"
JSON_FILE = "/app/ai-avatar-realm.json"


class KeycloakSetup:
    def __init__(self):
        self.wait_for_keycloak(KEYCLOAK_URL)
        self.config = self.load_config(JSON_FILE)
        self.token = self.get_admin_token()
        self.realm = self.config["realm"]

    # ---- HELPERS ----

    def _request(self, method, url, headers=None, **kwargs):
        resp = requests.request(method, url, headers=headers, **kwargs)
        try:
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"Error: {e}\nResponse: {resp.text}")
            raise
        return resp

    def load_config(self, filepath: str):
        with open(filepath, "r") as f:
            return json.load(f)

    def get_admin_token(self) -> str:
        url = f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"
        data = {
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }
        resp = requests.post(url, data=data)
        resp.raise_for_status()
        return resp.json()["access_token"]

    # ---- REALM MANAGEMENT ----

    def create_realm(self):
        url = f"{KEYCLOAK_URL}/admin/realms"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        data = {"realm": self.realm, "enabled": True}
        resp = requests.post(url, json=data, headers=headers)
        if resp.status_code in (201, 409):
            print(f"Realm '{self.realm}' created or already exists.")
        else:
            resp.raise_for_status()

    # ---- ROLE MANAGEMENT ----

    def create_roles(self, roles=None):
        if roles is None:
            roles = self.config.get("roles", [])
        for role in roles:
            self.create_role(role["name"])

    def create_role(self, role_name: str):
        url = f"{KEYCLOAK_URL}/admin/realms/{self.realm}/roles"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        data = {"name": role_name}
        resp = requests.post(url, json=data, headers=headers)
        if resp.status_code in (201, 409):
            print(f"Role '{role_name}' created or already exists.")
        else:
            raise RuntimeError(f"Failed to create role '{role_name}': {resp.text}")

    def assign_realm_roles(self, user_id: str, role_names):
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        roles = []
        for name in role_names:
            url = f"{KEYCLOAK_URL}/admin/realms/{self.realm}/roles/{name}"
            resp = self._request("GET", url, headers=headers)
            role = resp.json()
            roles.append({"id": role["id"], "name": role["name"]})
        url = f"{KEYCLOAK_URL}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm"
        resp = requests.post(url, json=roles, headers=headers)
        if resp.status_code in (204, 409):
            print(f"Assigned roles {role_names} to user '{user_id}'.")
        else:
            resp.raise_for_status()

    # ---- GROUP MANAGEMENT ----

    def create_groups(self, groups=None):
        if groups is None:
            groups = self.config.get("groups", [])
        for group_name in groups:
            self.create_group(group_name)

    def create_group(self, group_name: str):
        url = f"{KEYCLOAK_URL}/admin/realms/{self.realm}/groups"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        data = {"name": group_name}
        resp = requests.post(url, json=data, headers=headers)
        if resp.status_code in (201, 409):
            print(f"Group '{group_name}' created or already exists.")
        else:
            raise RuntimeError(f"Failed to create group '{group_name}': {resp.text}")

    
    def assign_group_owners(self, users=None):
        if users is None:
            users = self.config.get("users", [])
        for user in users:
            if "owns" in user:
                owner_username = user["username"]
                for group_name in user["owns"]:
                    try:
                        group_id = self.get_group_id(group_name)
                        self.set_group_owner(group_name, owner_username, group_id)
                    except ValueError as e:
                        raise ValueError(f"{e} (when setting owner for group '{group_name}' and user '{owner_username}')")
    
    def set_group_owner(self, group_name: str, owner_username: str, group_id: str):
        url = f"{KEYCLOAK_URL}/admin/realms/{self.realm}/groups/{group_id}"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        resp = self._request("GET", url, headers=headers)
        group_data = resp.json()
        attributes = group_data.get("attributes", {})
        attributes["owner"] = [owner_username]
        group_data["attributes"] = attributes
        resp = requests.put(url, headers=headers, json=group_data)
        if resp.status_code in (204, 200):
            print(f"Set '{owner_username}' as owner for group '{group_name}'.")
        else:
            raise RuntimeError(f"Failed to set owner for group '{group_name}': {resp.text}")



    def get_group_id(self, group_name: str) -> str:
        url = f"{KEYCLOAK_URL}/admin/realms/{self.realm}/groups"
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = self._request("GET", url, headers=headers)
        for group in resp.json():
            if group["name"] == group_name:
                return group["id"]
        raise ValueError(f"Group '{group_name}' not found.")

    def assign_user_to_group(self, user_id: str, group_id: str):
        url = f"{KEYCLOAK_URL}/admin/realms/{self.realm}/users/{user_id}/groups/{group_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.put(url, headers=headers)
        if resp.status_code in (204, 409):
            print(f"User '{user_id}' assigned to group '{group_id}'.")
        else:
            raise RuntimeError(f"Failed to assign user '{user_id}' to group '{group_id}': {resp.text}")


    # ---- CLIENT MANAGEMENT ----

    def create_clients(self, clients=None):
        if clients is None:
            clients = self.config.get("clients", [])
        for client in clients:
            self.create_client(client)
            self.add_group_membership_mapper(client["clientId"])

    def create_client(self, client_data):
        url = f"{KEYCLOAK_URL}/admin/realms/{self.realm}/clients"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        resp = requests.post(url, json=client_data, headers=headers)
        if resp.status_code in (201, 409):
            print(f"Client '{client_data['clientId']}' created or already exists.")
        else:
            print(resp.text)
            raise RuntimeError(f"Failed to create client '{client_data['clientId']}': {resp.text}")


    def add_group_membership_mapper(self, client_id: str):
        url = f"{KEYCLOAK_URL}/admin/realms/{self.realm}/clients?clientId={client_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = self._request("GET", url, headers=headers)
        clients = resp.json()
        if not clients:
            print(f"Client {client_id} not found!")
            raise ValueError(f"Client {client_id} not found for group membership mapper!")
        client_uuid = clients[0]["id"]
        url = f"{KEYCLOAK_URL}/admin/realms/{self.realm}/clients/{client_uuid}/protocol-mappers/models"
        headers["Content-Type"] = "application/json"
        data = {
            "name": "groups",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-group-membership-mapper",
            "consentRequired": False,
            "config": {
                "full.path": "false",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "userinfo.token.claim": "true",
                "claim.name": "groups",
                "jsonType.label": "String"
            }
        }
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code in (201, 409):
            print("Group Membership mapper created or already exists.")
        else:
            raise RuntimeError(f"Error creating Group Membership mapper for client '{client_id}': {resp.text}")


    # ---- USER MANAGEMENT ----

    def create_users(self, users=None):
        if users is None:
            users = self.config.get("users", [])
        for user in users:
            user_id = self.create_user(user)
            if "role" in user:
                self.assign_realm_roles(user_id, user["role"])
            for group_name in user.get("groups", []):
                try:
                    group_id = self.get_group_id(group_name)
                    self.assign_user_to_group(user_id, group_id)
                except ValueError as e:
                    raise ValueError(f"{e} (for user '{user['username']}')")

    def create_user(self, user_data) -> str:
        url = f"{KEYCLOAK_URL}/admin/realms/{self.realm}/users"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        user = {
            "username": user_data["username"],
            "enabled": user_data.get("enabled", True),
            "credentials": user_data.get("credentials", []),
        }
        resp = requests.post(url, json=user, headers=headers)
        if resp.status_code in (201, 409):
            print(f"User '{user['username']}' created or already exists.")
        else:
            print(resp.text)
            resp.raise_for_status()
        get_url = f"{KEYCLOAK_URL}/admin/realms/{self.realm}/users?username={user['username']}"
        resp = self._request("GET", get_url, headers=headers)
        return resp.json()[0]["id"]

    @staticmethod
    def wait_for_keycloak(url, timeout=120):
        print(f"Waiting for Keycloak at {url} ...")
        start = time.time()
        while True:
            try:
                r = requests.get(url)
                if r.status_code in (200, 401):
                    print("Keycloak is up!")
                    return
            except Exception as e:
                print("Still waiting for Keycloak:", e)
            if time.time() - start > timeout:
                raise RuntimeError("Keycloak did not become available in time")
            time.sleep(3)

    # ---- CHECK DB  ----

    def check_initialization(self):
        headers = {"Authorization": f"Bearer {self.token}"}

        realm_url = f"{KEYCLOAK_URL}/admin/realms/{self.realm}"
        realm_exists = requests.get(realm_url, headers=headers).status_code == 200

        groups_url = f"{KEYCLOAK_URL}/admin/realms/{self.realm}/groups"
        required_groups = set(self.config.get("groups", []))
        groups_resp = requests.get(groups_url, headers=headers)
        group_names = set(g["name"] for g in groups_resp.json()) if groups_resp.status_code == 200 else set()
        groups_exist = required_groups.issubset(group_names)

        users_url = f"{KEYCLOAK_URL}/admin/realms/{self.realm}/users"
        required_users = set(u["username"] for u in self.config.get("users", []))
        users_resp = requests.get(users_url, headers=headers)
        user_names = set(u["username"] for u in users_resp.json()) if users_resp.status_code == 200 else set()
        users_exist = required_users.issubset(user_names)

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

    # ---- MAIN SETUP ----

    def run(self):
        status = self.check_initialization()
        if status == "none_exist":
            self.create_realm()
            self.create_clients()
            self.create_roles()
            self.create_groups()
            self.create_users()
            self.assign_group_owners()
            print("Keycloak setup completed.")


if __name__ == "__main__":
    KeycloakSetup().run()
