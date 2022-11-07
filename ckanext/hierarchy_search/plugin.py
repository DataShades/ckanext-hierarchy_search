import re

import ckan.model as model
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckan.common import g

RE_ORG_FQ = re.compile(r'owner_org:(\'|")?([^\s\'"]+)(?(1)\1)')
RE_GRP_FQ = re.compile(r'groups:(\'|")?([^\s\'"]+)(?(1)\1)')

def _id_expander(match):
    org = model.Group.get(match.group(2))
    disable_sub_search = toolkit.asbool(
        org.extras.get('disable_hierarchy_search')
    )

    if disable_sub_search:
        return match.group(0)
    if toolkit.get_endpoint()[0] == 'organization':
        fq = ' OR '.join(
            '"{}"'.format(org.id)
            for org in org.get_children_groups('organization') + [org]
        )
        return 'owner_org:({})'.format(fq)
    elif toolkit.get_endpoint()[0] == 'group':
        fq = ' OR '.join(
            '"{}"'.format(grp.name)
            for grp in org.get_children_groups('group') + [org]
        )
        return 'groups:({})'.format(fq)


class Hierarchy_SearchPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IPackageController

    def before_search(self, data_dict):
        if toolkit.get_endpoint() == ('organization', 'read'):

            data_dict['fq'] = RE_ORG_FQ.sub(
                _id_expander,
                data_dict.get('fq', ''),
            )

        if toolkit.get_endpoint() == ('group', 'read'):
            data_dict['fq'] = RE_GRP_FQ.sub(
                _id_expander,
                data_dict.get('fq', ''),
            )

        return data_dict

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'hierarchy_search')
