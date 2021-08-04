# (C) Copyright 2019-2021 Hewlett Packard Enterprise Development LP.
# Apache License 2.0

import json
import logging
import re

from netaddr import EUI as MacAddress
from netaddr import mac_eui48

from pyaoscx.exceptions.response_error import ResponseError
from pyaoscx.exceptions.generic_op_error import GenericOperationError

from pyaoscx.utils.connection import connected
from pyaoscx.pyaoscx_module import PyaoscxModule

import pyaoscx.utils.util as utils


class Mac(PyaoscxModule):
    """
    Provide configuration management for vlans/<id>/macs on AOS-CX devices.
    """

    indices = ["from", "mac_addr"]
    resource_uri_name = "macs"

    def __init__(self, session, from_id, mac_addr, parent_vlan,
                 uri=None):
        """
        :param session: pyaoscx.Session object used to represent a logical
            connection to the device
        :param from_id: String source of the MAC address.
            Must be "dynamic", "VSX", "static", "VRRP",
            "port-access-security", "evpn", or "hsc"
        :param mac_addr: String MAC address, or netaddr EUI object.
            Example:
                '01:02:03:04:05:06'
        :param parent_vlan: Vlan object to which this MAC belongs
        :param uri: Optional string containing the uri of the MAC object
        """
        self.session = session

        # Set the MAC address format
        self.mac_format = mac_eui48
        self.mac_format.word_sep = ":"

        # Assign ID
        self.from_id = from_id
        self.mac_address = MacAddress(mac_addr, dialect=self.mac_format)
        # Assign parent VLAN
        self._set_vlan(parent_vlan)
        self._uri = uri
        # List used to determine attributes related to the MAC
        # configuration
        self.config_attrs = []
        self.materialized = False
        # Attribute dictionary used to manage the original data
        # obtained from the GET
        self._original_attributes = {}
        # Attribute used to know if object was changed recently
        self.__modified = False
        self.display_name = "Mac"

        self.path = self._mac_path()


    def _set_vlan(self, parent_vlan):
        """
        Set parent Vlan object as an attribute for the MAC class. It is
        a private method because the user shouldn't be able to change
        the parent vlan.

        :param parent_vlan a Vlan object
        """

        # Set parent VLAN
        self._parent_vlan = parent_vlan

        # Set URI
        self.base_uri = \
            "{0}/{1}/{2}".format(
                self._parent_vlan.base_uri,
                self._parent_vlan.id,
                self.resource_uri_name)

        macs = getattr(self._parent_vlan, self.resource_uri_name)
        found = False
        for mac in macs:
            if mac.mac_address == self.mac_address:
                found = True
                # Make list element point to current object
                mac = self
        if not found:
            macs.append(self)

    def _mac_path(self):
        """
        Get the path for internal purposes
        """
        return "{0}/{1}{2}{3}".format(
            self.base_uri,
            self.from_id,
            self.session.api.compound_index_separator,
            utils._replace_special_characters(str(self.mac_address)))

    def _set_configuration_items(self, selector):
        # Determines if the MAC is configurable
        if selector in self.session.api.configurable_selectors:
            # Sets self.config_attrs and delete ID from it
            utils.set_config_attrs(
                self, data, "config_attrs", ["from", "mac_addr"])

    @PyaoscxModule.connected
    def get(self, depth=None, selector=None):
        """
        Perform a GET call to retrieve data for a MAC table entry and fill
        the object with the incoming attributes

        :param depth: Integer deciding how many levels into the API JSON that
            references will be returned.
        :param selector: Alphanumeric option to select specific information to
            return.
        :return: Returns True if there is not an exception raised
        """
        logging.info("Retrieving the switch {}".format(self.display_name))

        data = self._get_data(depth, selector)

        # Add dictionary as attributes for the object
        utils.create_attrs(self, data)

        self._set_configuration_items(selector)

        # Set original attributes
        self._original_attributes = data
        # Remove both parts of the ID
        if "from" in self._original_attributes:
            self._original_attributes.pop("from")
        if "mac_addr" in self._original_attributes:
            self._original_attributes.pop("mac_addr")

        # Set port as an Interface Object
        if hasattr(self, "port") and self.port is not None:
            port_response = self.port
            # Instantiate empty object to use static method correctly
            interface_cls = self.session.api.get_module(
                self.session, "Interface", "")
            # Set port as a Interface Object
            self.port = interface_cls.from_response(
                self.session, port_response)
            self.port.get()

        # Sets object as materialized
        # Information is loaded from the Device
        self.materialized = True
        return True

    @classmethod
    def get_all(cls, session, parent_vlan):
        """
        Perform a GET call to retrieve all system MACs inside a
        BGP Router,
        and create a dictionary containing them
        :param cls: Object's class
        :param session: pyaoscx.Session object used to represent a logical
            connection to the device
        :param parent_vlan: parent bgp_router object where MAC is stored
        :return: Dictionary containing MACs IDs as keys and a
            Mac objects as values
        """

        logging.info("Retrieving the switch {}".format(cls.resource_uri_name))

        path = "{0}/{1}/{2}".format(
            parent_vlan.base_uri,
            parent_vlan.id,
            cls.resource_uri_name)

        try:
            response = session.request("GET", path)
        except Exception as e:
            raise ResponseError("GET", e)

        if not utils._response_ok(response, "GET"):
            raise GenericOperationError(response.text, response.status_code)

        data = json.loads(response.text)

        mac_dict = {}
        # Get all URI elements in the form of a list
        uri_list = session.api.get_uri_from_data(data)

        for uri in uri_list:
            # Create a Mac object
            indices, mac = cls.from_uri(
                session, parent_vlan, uri)
            mac.get()
            mac_dict[indices] = mac

        return mac_dict

    @PyaoscxModule.connected
    def apply(self):
        """
        Not applicable for MAC.
        As HTTP Request method is not implemented inside REST API

        """
        pass

    @PyaoscxModule.connected
    def update(self):
        """
        Not applicable for MAC.
        As HTTP Request method is not implemented inside REST API

        """
        pass

    @PyaoscxModule.connected
    def create(self):
        """
        Not applicable for MAC.
        As HTTP Request method is not implemented inside REST API

        """
        pass

    @PyaoscxModule.connected
    def delete(self):
        """
        Not applicable for MAC.
        As HTTP Request method is not implemented inside REST API

        """
        pass

    @classmethod
    def from_response(cls, session, parent_vlan, response_data):
        """
        Create a Mac object given a response_data related to the MAC
            ID object
        :param cls: Object's class
        :param session: pyaoscx.Session object used to represent a logical
            connection to the device
        :param parent_vlan: parent VLAN class where MAC is stored
        :param response_data: The response can be either a
            dictionary: {
                    id: "/rest/v10.04/system/vlans/id
                        /macs/id1,id2"
                }
            or a
            string: "/rest/v10.04/system/vlans/id/macs
                    /from_id/from/mac_addr"
        :return: Mac object
        """
        mac_format = mac_eui48
        mac_format.word_sep = ":"
        mac_pair = session.api.get_keys(
            response_data, cls.resource_uri_name)
        mac_addr = mac_pair[1]
        from_id = mac_pair[0]

        mac_address = MacAddress(utils._replace_percents(mac_addr),
                                 dialect=mac_format)

        return Mac(
            session, from_id, mac_address, parent_vlan)

    @classmethod
    def from_uri(cls, session, parent_vlan, uri):
        """
        Create a Mac object
        :param session: pyaoscx.Session object used to represent a logical
            connection to the device
        :param parent_vlan: parent VLAN class where MAC is stored
        :param uri: a String with a URI

        :return indices, mac: tuple containing both the Mac object and
            the MAC' ID
        """
        mac_format = mac_eui48
        mac_format.word_sep = ":"
        # Get ID from URI. Note that using a uri object here is of no
        # benefit because we are dealing with the path
        index_pattern = \
            re.compile(
                r"(.*)macs/(?P<index1>.+)[,./-](?P<index2>.+)")
        from_id = index_pattern.match(uri).group("index1")
        reference_mac_addr = index_pattern.match(uri).group("index2")

        mac_addr = MacAddress(utils._replace_percents(
            reference_mac_addr), dialect=mac_format)

        mac = Mac(session, from_id, mac_addr,
                  parent_vlan)
        indices = "{0}{1}{2}".format(
            from_id,
            session.api.compound_index_separator,
            reference_mac_addr)

        return indices, mac

    def __str__(self):
        return str(self.mac_address)

    def get_uri(self):
        """
        Method used to obtain the specific MAC URI
        return: Object's URI
        """
        # TODO: remove this method in favor of uri_path once all
        # modules have been translated to the "properties" style
        return self.uri_path

    @property
    def uri_path(self):
        """
        Method used to obtain the specific MAC URI
        return: Object's URI
        """
        if self._uri is None:
            self._uri = (
                "{0}{1}/{2}{3}{4}"
            ).format(
                self.session.resource_prefix,
                self.base_uri,
                self.from_id,
                self.session.api.compound_index_separator,
                utils._replace_special_characters(str(self.mac_address))
            )

        return self._uri

    def get_info_format(self):
        """
        Method used to obtain correct object format for referencing inside
        other objects
        return: Object format depending on the API Version
        """
        # TODO: remove in favor of info_format when all modules are translated
        # to "properties" style
        return self.info_format

    @property
    def info_format(self):
        """
        Method used to obtain correct object format for referencing inside
        other objects
        return: Object format depending on the API Version
        """

        return self.session.api.get_index(self)

    def was_modified(self):
        """
        Getter method for the __modified attribute
        :return: Boolean. True if the object was recently modified.
        """

        return self.__modified

    ####################################################################
    # IMPERATIVE FUNCTIONS
    ####################################################################

    def get_info(self):
        """
        Perform a GET call to retrieve data for a MAC table entry and
        return info as a dictionary. Do not apply the configuration

        :return info_dict: Returns a dictionary containing the current
            MAC Address information
        """
        logging.info("Retrieving the switch MAC info")

        return self._get_data(None, None)