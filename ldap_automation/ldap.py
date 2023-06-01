import requests
import ldap

# Setup LDAP connection
conn = ldap.initialize('ldap://your_ad_server')
conn.simple_bind_s('user_dn', 'password')

# Get AD users and groups
ad_users = conn.search_s('ou=users,dc=example,dc=com', ldap.SCOPE_SUBTREE, 'objectclass=user')

# Setup Guacamole API session
s = requests.Session()
s.post('http://guacamole-server/api/tokens', json={'username': 'admin', 'password': 'admin'})

# Get Guacamole users
guacamole_users = s.get('http://guacamole-server/api/session/data/ldap/users').json()

# Iterate over AD users
for user in ad_users:
    # Fetch the corresponding user in Guacamole
    guacamole_user = next((u for u in guacamole_users if u['username'] == user[1]['uid'][0].decode()), None)
    
    # If user exists in Guacamole, update their group membership
    if guacamole_user:
        # Fetch AD groups for user
        ad_groups = [group.decode().split(',')[0][3:] for group in user[1].get('memberOf', [])]
        
        # Fetch Guacamole groups for user
        guacamole_groups = s.get(f'http://guacamole-server/api/session/data/ldap/users/{guacamole_user["username"]}/groups').json()
        
        # Find any AD groups the user is a member of that they're not a member of in Guacamole
        groups_to_add = [group for group in ad_groups if group not in guacamole_groups]
        
        # Add user to those groups in Guacamole
        for group in groups_to_add:
            s.put(f'http://guacamole-server/api/session/data/ldap/users/{guacamole_user["username"]}/groups/{group}')
            
        # Find any Guacamole groups the user is a member of that they're not a member of in AD
        groups_to_remove = [group for group in guacamole_groups if group not in ad_groups]
        
        # Remove user from those groups in Guacamole
        for group in groups_to_remove:
            s.delete(f'http://guacamole-server/api/session/data/ldap/users/{guacamole_user["username"]}/groups/{group}')

conn.unbind_s()

