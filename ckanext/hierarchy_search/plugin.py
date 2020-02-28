import re

import ckan.model as model
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckan.common import g

RE_ORG_FQ = re.compile(r'owner_org:(\'|")?([^\s\'"]+)(?(1)\1)')


def _id_expander(match):
    org = model.Group.get(match.group(2))
    disable_sub_search = toolkit.asbool(
        org.extras.get('disable_hierarchy_search')
    )

    if disable_sub_search:
        return match.group(0)
    fq = ' OR '.join(
        '"{}"'.format(org.id)
        for org in org.get_children_groups('organization') + [org]
    )

    return 'owner_org:({})'.format(fq)


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

        return data_dict

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'hierarchy_search')
