#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2021 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.
from hashlib import sha256

from ldap.filter import filter_format

import univention.admin.handlers
import univention.admin.localization
import univention.admin.syntax
import univention.admin.uexceptions
from univention.admin.layout import Tab

translation = univention.admin.localization.translation("univention.admin.handlers.bildungslogin")
_ = translation.translate

module = "bildungslogin/metadata"
childs = True
object_name = _("Metadata")
object_name_plural = _("Metadata")
short_description = _("Metadata")
long_description = _("Metadata for a product from Bildungslogin")
operations = ["add", "edit", "remove", "search"]  # TODO: Do we want a remove operation or not?
default_containers = ["cn=metadata,cn=bildungslogin,cn=vbm,cn=univention"]

options = {
    "default": univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=["top", "bildungsloginMetaData"],
    )
}

property_descriptions = {
    "cn": univention.admin.property(
        short_description=_("CN"),
        long_description=_("CN of the metadata"),
        syntax=univention.admin.syntax.string,
        required=True,
        identifies=True,
        may_change=False,
    ),
    "product_id": univention.admin.property(
        short_description=_("Product ID"),
        long_description=_("The product ID"),
        syntax=univention.admin.syntax.string,
        required=True,
        may_change=False,
    ),
    "title": univention.admin.property(
        short_description=_("Title"),
        long_description=_("The title product described by the metadata"),
        syntax=univention.admin.syntax.string,
        required=False,
        may_change=True,
    ),
    "description": univention.admin.property(
        short_description=_("Description"),
        long_description=_("The description of the product described by the metadata"),
        syntax=univention.admin.syntax.string,
        required=False,
        may_change=True,
    ),
    "author": univention.admin.property(
        short_description=_("Author"),
        long_description=_("The author of the product described by the metadata"),
        syntax=univention.admin.syntax.string,
        required=False,
        may_change=True,
    ),
    "publisher": univention.admin.property(
        short_description=_("Publisher"),
        long_description=_("The publisher of the product described by the metadata"),
        syntax=univention.admin.syntax.string,
        required=False,
        may_change=True,
    ),
    "cover": univention.admin.property(
        short_description=_("Cover"),
        long_description=_("The url for the cover of the product described by the metadata"),
        syntax=univention.admin.syntax.string,  # TODO URL?
        required=False,
        may_change=True,
    ),
    "cover_small": univention.admin.property(
        short_description=_("CoverSmall"),
        long_description=_("The url for the thumbnail of the product described by the metadata"),
        syntax=univention.admin.syntax.string,  # TODO URL?
        required=False,
        may_change=True,
    ),
    "modified": univention.admin.property(
        short_description=_("Modified"),
        long_description=_("Last modification as 2021-07-27"),
        syntax=univention.admin.syntax.iso8601Date,  # TODO URL?
        required=True,
        may_change=True,
    ),
}

layout = [
    Tab(
        _("General"),
        _("Basic Settings"),
        layout=[
            [
                "title",
            ],
            ["product_id"],
            ["description"],
            ["author", "publisher"],
            ["cover", "cover_small"],
            ["modified"],
        ],
    )
]

mapping = univention.admin.mapping.mapping()
for udm_name, ldap_name in [
    ("cn", "cn"),
    ("product_id", "bildungsloginProductId"),
    ("title", "bildungsloginMetaDataTitle"),
    ("description", "bildungsloginMetaDataDescription"),
    ("author", "bildungsloginMetaDataAuthor"),
    ("publisher", "bildungsloginMetaDataPublisher"),
    ("cover", "bildungsloginMetaDataCover"),
    ("cover_small", "bildungsloginMetaDataCoverSmall"),
    ("modified", "bildungsloginMetaDataModified"),
]:
    mapping.register(udm_name, ldap_name, None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):

    module = module

    def _ldap_pre_ready(self):
        super(object, self)._ldap_pre_ready()
        if self["product_id"] and not self["cn"]:
            self["cn"] = sha256(self["product_id"]).hexdigest()

    def _ldap_pre_create(self):
        super(object, self)._ldap_pre_create()
        # The code, and thus the vbmProductId of any license must be unique in the domain
        if self.lo.searchDn(
            filter_format(
                "(&(objectClass=bildungsloginMetadata)(bildungsloginProductId=%s))",
                [self["product_id"]],
            )
        ):
            raise univention.admin.uexceptions.valueError(
                _("A metadata object with that product_id already exists")
            )
        super(object, self)._ldap_pre_create()


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
