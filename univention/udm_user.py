#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Copyright (c) 2016, Adfinis SyGroup AG
# Tobias Rueetschi <tobias.ruetschi@adfinis-sygroup.ch>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.univention_umc import (
    umc_module_for_add,
    umc_module_for_edit,
    ldap_search,
    base_dn,
)
from datetime import date
from dateutil.relativedelta import relativedelta
import crypt


DOCUMENTATION = '''
---
module: udm_user
version_added: "2.2"
author: "Tobias Rueetschi (@2-B)"
short_description: Manage posix users on a univention corporate server
description:
    - "This module allows to manage posix users on a univention corporate server (UCS).
       It uses the python API of the UCS to create a new object or edit it."
requirements:
    - Python >= 2.6
options:
    state:
        required: false
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the user is present or not.
    username:
        required: true
        description:
            - User name
        aliases: ['name']
    firstname:
        required: false
        description:
            - First name. Required if C(state=present).
    lastname:
        required: false
        description:
            - Last name. Required if C(state=present).
    password:
        required: false
        default: None
        description:
            - Password. Required if C(state=present).
    birthday:
        required: false
        default: None
        description:
            - Birthday
    city:
        required: false
        default: None
        description:
            - City of users business address.
    country:
        required: false
        default: None
        description:
            - Country of users business address.
    departmentNumber:
        required: false
        default: None
        description:
            - Department number of users business address.
    description:
        required: false
        default: None
        description:
            - Description (not gecos)
    displayName:
        required: false
        default: None
        description:
            - Display name (not gecos)
    email:
        required: false
        default: ['']
        description:
            - A list of e-mail addresses.
    employeeNumber:
        required: false
        default: None
        description:
            - Employee number
    employeeType:
        required: false
        default: None
        description:
            - Employee type
    gecos:
        required: false
        default: None
        description:
            - GECOS
    groups:
        required: false
        default: []
        description:
            - "POSIX groups, the LDAP DNs of the groups will be found with the
               LDAP filter for each group as $GROUP:
               C((&(objectClass=posixGroup)(cn=$GROUP)))."
    homeShare:
        required: false
        default: None
        description:
            - "Home NFS share. Must be a LDAP DN, e.g.
               C(cn=home,cn=shares,ou=school,dc=example,dc=com)."
    homeSharePath:
        required: false
        default: None
        description:
            - Path to home NFS share, inside the homeShare.
    homeTelephoneNumber:
        required: false
        default: []
        description:
            - List of private telephone numbers.
    homedrive:
        required: false
        default: None
        description:
            - Windows home drive, e.g. C("H:").
    mailAlternativeAddress:
        required: false
        default: []
        description:
            - List of alternative e-mail addresses.
    mailHomeServer:
        required: false
        default: None
        description:
            - FQDN of mail server
    mailPrimaryAddress:
        required: false
        default: None
        description:
            - Primary e-mail address
    mobileTelephoneNumber:
        required: false
        default: []
        description:
            - Mobile phone number
    organisation:
        required: false
        default: None
        description:
            - Organisation
    pagerTelephonenumber:
        required: false
        default: []
        description:
            - List of pager telephone numbers.
    phone:
        required: false
        default: []
        description:
            - List of telephone numbers.
    postcode:
        required: false
        default: None
        description:
            - Postal code of users business address.
    primaryGroup:
        required: false
        default: cn=Domain Users,cn=groups,$LDAP_BASE_DN
        description:
            - Primary group. This must be the group LDAP DN.
    profilepath:
        required: false
        default: None
        description:
            - Windows profile directory
    pwdChangeNextLogin:
        required: false
        default: None
        choices: [ '0', '1' ]
        description:
            - Change password on next login.
    roomNumber:
        required: false
        default: None
        description:
            - Room number of users business address.
    sambaPrivileges:
        required: false
        default: []
        description:
            - "Samba privilege, like allow printer administration, do domain
               join."
    sambaUserWorkstations:
        required: false
        default: []
        description:
            - Allow the authentication only on this Microsoft Windows host.
    sambahome:
        required: false
        default: None
        description:
            - Windows home path, e.g. C('\\\\$FQDN\\$USERNAME').
    scriptpath:
        required: false
        default: None
        description:
            - Windows logon script.
    secretary:
        required: false
        default: []
        description:
            - A list of superiors as LDAP DNs.
    serviceprovider:
        required: false
        default: ['']
        description:
            - Enable user for the following service providers.
    shell:
        required: false
        default: '/bin/bash'
        description:
            - Login shell
    street:
        required: false
        default: None
        description:
            - Street of users business address.
    title:
        required: false
        default: None
        description:
            - Title, e.g. C(Prof.).
    unixhome:
        required: false
        default: '/home/$USERNAME'
        description:
            - Unix home directory
    userexpiry:
        required: false
        default: Today + 1 year
        description:
            - Account expiry date, e.g. C(1999-12-31).
    position:
        required: false
        default: ''
        description:
            - "Define the whole position of users object inside the LDAP tree, e.g.
               C(cn=employee,cn=users,ou=school,dc=example,dc=com)."
    ou:
        required: false
        default: ''
        description:
            - "Organizational Unit inside the LDAP Base DN, e.g. C(school) for
               LDAP OU C(ou=school,dc=example,dc=com)."
    subpath:
        required: false
        default: 'cn=users'
        description:
            - "LDAP subpath inside the organizational unit, e.g.
               C(cn=teachers,cn=users) for LDAP container
               C(cn=teachers,cn=users,dc=example,dc=com)."
'''


EXAMPLES = '''
# Create a user on a UCS
- udm_user: name=FooBar
            password=secure_password
            firstname=Foo
            lastname=Bar

# Create a user with the DN
# C(uid=foo,cn=teachers,cn=users,ou=school,dc=school,dc=example,dc=com)
- udm_user: name=foo
            password=secure_password
            firstname=Foo
            lastname=Bar
            ou=school
            subpath='cn=teachers,cn=users'
# or define the position
- udm_user: name=foo
            password=secure_password
            firstname=Foo
            lastname=Bar
            position='cn=teachers,cn=users,ou=school,dc=school,dc=example,dc=com'
'''


RETURN = '''# '''


def main():
    expiry = date.strftime(date.today()+relativedelta(years=1), "%Y-%m-%d")
    module = AnsibleModule(
        argument_spec = dict(
            birthday                = dict(default=None,
                                           type='str'),
            city                    = dict(default=None,
                                           type='str'),
            country                 = dict(default=None,
                                           type='str'),
            departmentNumber        = dict(default=None,
                                           type='str'),
            description             = dict(default=None,
                                           type='str'),
            displayName             = dict(default=None,
                                           type='str'),
            email                   = dict(default=[''],
                                           type='list'),
            employeeNumber          = dict(default=None,
                                           type='str'),
            employeeType            = dict(default=None,
                                           type='str'),
            firstname               = dict(default=None,
                                           type='str'),
            gecos                   = dict(default=None,
                                           type='str'),
            groups                  = dict(default=[],
                                           type='list'),
            homeShare               = dict(default=None,
                                           type='str'),
            homeSharePath           = dict(default=None,
                                           type='str'),
            homeTelephoneNumber     = dict(default=[],
                                           type='list'),
            homedrive               = dict(default=None,
                                           type='str'),
            lastname                = dict(default=None,
                                           type='str'),
            mailAlternativeAddress  = dict(default=[],
                                           type='list'),
            mailHomeServer          = dict(default=None,
                                           type='str'),
            mailPrimaryAddress      = dict(default=None,
                                           type='str'),
            mobileTelephoneNumber   = dict(default=[],
                                           type='list'),
            organisation            = dict(default=None,
                                           type='str'),
            pagerTelephonenumber    = dict(default=[],
                                           type='list'),
            password                = dict(default=None,
                                           type='str',
                                           no_log=True),
            phone                   = dict(default=[],
                                           type='list'),
            postcode                = dict(default=None,
                                           type='str'),
            primaryGroup            = dict(default=None,
                                           type='str'),
            profilepath             = dict(default=None,
                                           type='str'),
            pwdChangeNextLogin      = dict(default=None,
                                           type='str',
                                           choices=['0', '1']),
            roomNumber              = dict(default=None,
                                           type='str'),
            sambaPrivileges         = dict(default=[],
                                           type='list'),
            sambaUserWorkstations   = dict(default=[],
                                           type='list'),
            sambahome               = dict(default=None,
                                           type='str'),
            scriptpath              = dict(default=None,
                                           type='str'),
            secretary               = dict(default=[],
                                           type='list'),
            serviceprovider         = dict(default=[''],
                                           type='list'),
            shell                   = dict(default='/bin/bash',
                                           type='str'),
            street                  = dict(default=None,
                                           type='str'),
            title                   = dict(default=None,
                                           type='str'),
            unixhome                = dict(default=None,
                                           type='str'),
            userexpiry              = dict(default=expiry,
                                           type='str'),
            username                = dict(required=True,
                                           aliases=['name'],
                                           type='str'),
            position                = dict(default='',
                                           type='str'),
            ou                      = dict(default='',
                                           type='str'),
            subpath                 = dict(default='cn=users',
                                           type='str'),
            state                   = dict(default='present',
                                           choices=['present', 'absent'],
                                           type='str')
        ),
        supports_check_mode=True,
        required_if = ([
            ('state', 'present', ['firstname', 'lastname', 'password'])
        ])
    )
    username    = module.params['username']
    position    = module.params['position']
    ou          = module.params['ou']
    subpath     = module.params['subpath']
    state       = module.params['state']
    changed     = False

    users = list(ldap_search(
        '(&(objectClass=posixAccount)(uid={}))'.format(username),
        attr=['uid']
    ))
    if position != '':
        container = position
    else:
        if ou != '':
            ou = 'ou={},'.format(ou)
        if subpath != '':
            subpath = '{},'.format(subpath)
        container = '{}{}{}'.format(subpath, ou, base_dn())
    user_dn = 'uid={},{}'.format(username, container)

    exists = bool(len(users))

    if state == 'present':
        try:
            if not exists:
                obj = umc_module_for_add('users/user', container)
            else:
                obj = umc_module_for_edit('users/user', user_dn)

            if module.params['displayName'] == None:
                module.params['displayName'] = '{} {}'.format(
                    module.params['firstname'],
                    module.params['lastname']
                )
            if module.params['unixhome'] == None:
                module.params['unixhome'] = '/home/{}'.format(
                    module.params['username']
                )
            for k in obj.keys():
                if (k != 'password' and
                    k != 'groups' and
                    module.params.has_key(k) and
                    module.params[k] != None):
                    obj[k] = module.params[k]
            # handle some special values
            obj['e-mail'] = module.params['email']
            password = module.params['password']
            if obj['password'] == None:
                obj['password'] = password
            else:
                old_password = obj['password'].split('}', 2)[1]
                if crypt.crypt(password, old_password) != old_password:
                    obj['password'] = password

            diff = obj.diff()
            if exists:
                for k in obj.keys():
                    if obj.hasChanged(k):
                        changed = True
            else:
                changed = True
            if not module.check_mode:
                if not exists:
                    obj.create()
                elif changed:
                    obj.modify()
        except:
            module.fail_json(
                msg="Creating/editing user {} in {} failed".format(username, container)
            )
        try:
            groups = module.params['groups']
            if groups:
                filter = '(&(objectClass=posixGroup)(|(cn={})))'.format(')(cn='.join(groups))
                group_dns = list(ldap_search(filter, attr=['dn']))
                for dn in group_dns:
                    grp = umc_module_for_edit('groups/group', dn[0])
                    if user_dn not in grp['users']:
                        grp['users'].append(user_dn)
                        if not module.check_mode:
                            grp.modify()
                        changed = True
        except:
            module.fail_json(
                msg="Adding groups to user {} failed".format(username)
            )

    if state == 'absent' and exists:
        try:
            obj = umc_module_for_edit('users/user', user_dn)
            if not module.check_mode:
                obj.remove()
            changed = True
        except:
            module.fail_json(
                msg="Removing user {} failed".format(username)
            )

    module.exit_json(
        changed=changed,
        username=username,
        diff=diff,
        container=container
    )


if __name__ == '__main__':
    main()
