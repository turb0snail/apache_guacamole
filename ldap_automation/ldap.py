import ldap
from guacamole import Guacamole

# connect to LDAP and Guacamole API
ldap_connection = ldap.initialize(LDAP_SERVER)
ldap_connection.simple_bind_s(USERNAME, PASSWORD)
guacamole = Guacamole(GUACAMOLE_SERVER)

# mappings of groups to connections
group_to_connections = {
    "guacamole_users": ["rdp1", "rdp2"],
    # add more groups and connections as needed
}

# get all users in 'guacamole_users' group
group_dn = "CN=guacamole_users,OU=groups,OU=sentrium,DC=ad,DC=sentrium,DC=io"
guacamole_users = ldap_connection.search_s(
    group_dn, ldap.SCOPE_SUBTREE, "(objectClass=*)", ["member"]
)

# loop through each user
for user_dn in guacamole_users[0][1]["member"]:
    # check if user already exists in Guacamole
    if not guacamole.user_exists(user_dn):
        # create user in Guacamole
        guacamole.create_user(user_dn)

    # get all groups for this user
    user_groups = ldap_connection.search_s(
        user_dn, ldap.SCOPE_SUBTREE, "(objectClass=*)", ["memberOf"]
    )

    # loop through each group
    for group_dn in user_groups[0][1]["memberOf"]:
        # check if group is in our mappings
        if group_dn in group_to_connections:
            # get connections for this group
            connections = group_to_connections[group_dn]

            # loop through each connection
            for connection in connections:
                # create connection for this user
                guacamole.create_connection(user_dn, connection)
