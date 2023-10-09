#!/bin/bash
while true; do

    # Your LDAP and Guacamole server details
    LDAP_SERVER="xxx"
    LDAP_PORT=389
    LDAP_USER="xxx"
    LDAP_PASS="xxx"
    GUACAMOLE_SERVER="xxx"
    GUACAMOLE_USER="xxx"
    GUACAMOLE_PASS="xxx"

    # Mappings of groups to connections
    declare -A group_to_connections=(["guacamole_users"]="rdp1 rdp2")

    # List of all groups in the Active Directory
    groups=("xxx" "xxx" "xxx" "xxx")

    # Loop through each group
    for group in ${groups[@]}
    do
        group_dn="CN=${group},OU=xxx,OU=xxx,DC=xxx,DC=xxx,DC=xxx"
        
        # Check if group exists in Guacamole
        response=$(curl -u ${GUACAMOLE_USER}:${GUACAMOLE_PASS} -s "${GUACAMOLE_SERVER}/api/session/data/mysql/groups/${group}")

        # If group doesn't exist, create it
        if [[ "$response" != *"name"* ]]; then
            curl -u ${GUACAMOLE_USER}:${GUACAMOLE_PASS} -s -X POST -H "Content-Type: application/json" -d '{"name": "'${group}'"}' "${GUACAMOLE_SERVER}/api/session/data/mysql/groups"
        fi

        # Get all users in this group
        users=$(ldapsearch -H ldap://${LDAP_SERVER}:${LDAP_PORT} -D ${LDAP_USER} -w ${LDAP_PASS} -b "${group_dn}" "(objectClass=*)" member | grep 'member: ' | cut -d' ' -f2-)

        # Loop through each user
        for user_dn in ${users[@]}
        do
            # Check if user exists in Guacamole
            response=$(curl -u ${GUACAMOLE_USER}:${GUACAMOLE_PASS} -s "${GUACAMOLE_SERVER}/api/session/data/mysql/users/${user_dn}")

            # If user doesn't exist, create it
            if [[ "$response" != *"username"* ]]; then
                curl -u ${GUACAMOLE_USER}:${GUACAMOLE_PASS} -s -X POST -H "Content-Type: application/json" -d '{"username": "'${user_dn}'"}' "${GUACAMOLE_SERVER}/api/session/data/mysql/users"
            fi

            # Check if user is a member of the group in Guacamole
            response=$(curl -u ${GUACAMOLE_USER}:${GUACAMOLE_PASS} -s "${GUACAMOLE_SERVER}/api/session/data/mysql/groups/${group}/members/${user_dn}")

            # If user is not a member of the group, add the user to the group
            if [[ "$response" != *"username"* ]]; then
                curl -u ${GUACAMOLE_USER}:${GUACAMOLE_PASS} -s -X PUT "${GUACAMOLE_SERVER}/api/session/data/mysql/groups/${group}/members/${user_dn}"
            fi
        done
    done

    # Wait for 20 minutes before running again
    sleep 20m
done
