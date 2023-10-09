import ldap3
import requests

# Your LDAP and Guacamole server details
LDAP_SERVER = "xxx"
LDAP_PORT = 389
LDAP_USER = "xxx"
LDAP_PASS = "xxx"

# Guacamole server details
GUACAMOLE_SERVER = "xxx"
GUACAMOLE_USER = "xxx"
GUACAMOLE_PASS = "xxx"

# Connect to LDAP and Guacamole API
server = ldap3.Server(LDAP_SERVER, port=LDAP_PORT, get_info=ldap3.ALL)
conn = ldap3.Connection(server, LDAP_USER, LDAP_PASS, auto_bind=True)

# Bind to the LDAP server
if not conn.bind():
    print("Error in bind", conn.result)

# Mappings of groups to connections
group_to_connections = {
    "guacamole_users": ["rdp1", "rdp2"],
    # Add more groups and connections as needed
}

# Get all users in 'guacamole_users' group
group_dn = "CN=guacamole_users,OU=groups,OU=xxx,DC=xxx,DC=xxx,DC=xxx"
if not conn.search(
    search_base=group_dn, search_filter="(objectClass=*)", attributes=["member"]
):
    print("Error in search", conn.result)
guacamole_users = conn.entries

# Loop through each user
for user_entry in guacamole_users:
    user_dn = user_entry.entry_dn

    # Get user details from Guacamole API
    response = requests.get(
        f"{GUACAMOLE_SERVER}/api/session/data/mysql/users/{user_dn}",
        auth=(GUACAMOLE_USER, GUACAMOLE_PASS),
    )
    response.raise_for_status()

    # If user doesn't exist, create it
    if response.status_code != 200:
        user_data = {
            "username": user_dn,
            "password": "UserPassword",
        }  # Add other necessary user attributes here
        response = requests.post(
            f"{GUACAMOLE_SERVER}/api/session/data/mysql/users",
            data=user_data,
            auth=(GUACAMOLE_USER, GUACAMOLE_PASS),
        )
        response.raise_for_status()

    # Get all groups for this user
    if not conn.search(
        search_base=user_dn, search_filter="(objectClass=*)", attributes=["memberOf"]
    ):
        print("Error in search", conn.result)
    user_groups = conn.entries

    # Loop through each group
    for group_entry in user_groups:
        group_dn = group_entry.entry_dn

        # Check if group is in our mappings
        cn = ldap3.utils.dn.parse_dn(group_dn)[0][1]
        if cn in group_to_connections:
            # Get connections for this group
            connections = group_to_connections[cn]
            # Loop through each connection
            for connection in connections:
                # Create connection for this user
                connection_data = {
                    "identifier": connection
                }  # Add other necessary connection attributes here
                response = requests.post(
                    f"{GUACAMOLE_SERVER}/api/session/data/mysql/users/{user_dn}/connections",
                    data=connection_data,
                    auth=(GUACAMOLE_USER, GUACAMOLE_PASS),
                )
                response.raise_for_status()
