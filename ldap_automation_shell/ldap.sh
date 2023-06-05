#!/bin/bash
while true; do
# Your LDAP and Guacamole server details
LDAP_SERVER="ad.sentrium.io"
LDAP_PORT=389
LDAP_USER="guacamole"
LDAP_PASS="=VR'2~WHs)vG#l@bbr,h"
GUACAMOLE_SERVER="https://guacamole.sentrium.net"
GUACAMOLE_USER="sentrium"
GUACAMOLE_PASS="pR-zv;FO)~m%fDr2kt]J"

# Mappings of groups to connections
declare -A group_to_connections=(["guacamole_users"]="rdp1 rdp2")

# Base DN for 'guacamole_users' group
group_dn="CN=guacamole_users,OU=groups,OU=sentrium,DC=ad,DC=sentrium,DC=io"

# Get all users in 'guacamole_users' group
users=$(ldapsearch -H ldap://${LDAP_SERVER}:${LDAP_PORT} -D ${LDAP_USER} -w ${LDAP_PASS} -b "${group_dn}" "(objectClass=*)" member | grep 'member: ' | cut -d' ' -f2-)

# Loop through each user
for user_dn in ${users[@]}
do
    # Get user details from Guacamole API
    response=$(curl -u ${GUACAMOLE_USER}:${GUACAMOLE_PASS} -s "${GUACAMOLE_SERVER}/api/session/data/mysql/users/${user_dn}")

    # Check if user exists
    if [[ "$response" != *"username"* ]]; then
        # If user doesn't exist, create it
        curl -u ${GUACAMOLE_USER}:${GUACAMOLE_PASS} -s -X POST -H "Content-Type: application/json" -d '{"username": "'${user_dn}'", "password": "UserPassword"}' "${GUACAMOLE_SERVER}/api/session/data/mysql/users"
    fi

    # Get all groups for this user
    groups=$(ldapsearch -H ldap://${LDAP_SERVER}:${LDAP_PORT} -D ${LDAP_USER} -w ${LDAP_PASS} -b "${user_dn}" "(objectClass=*)" memberOf | grep 'memberOf: ' | cut -d' ' -f2-)

    # Loop through each group
    for group_dn in ${groups[@]}
    do
        # Check if group is in our mappings
        cn=$(ldapsearch -H ldap://${LDAP_SERVER}:${LDAP_PORT} -D ${LDAP_USER} -w ${LDAP_PASS} -b "${group_dn}" "(objectClass=*)" cn | grep 'cn: ' | cut -d' ' -f2-)
        if [[ -n "${group_to_connections[$cn]}" ]]; then
            # Get connections for this group
            connections=${group_to_connections[$cn]}

            # Loop through each connection
            for connection in ${connections[@]}
            do
                # Create connection for this user
                curl -u ${GUACAMOLE_USER}:${GUACAMOLE_PASS} -s -X POST -H "Content-Type: application/json" -d '{"identifier": "'${connection}'"}' "${GUACAMOLE_SERVER}/api/session/data/mysql/users/${user_dn}/connections"
            done
        fi
    done
    # Wait for a certain amount of time before running again.
    # For example, to wait for one hour, you would use 'sleep 1h'.
    sleep 20m   
done
