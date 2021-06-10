# (C) Copyright 2019-2020 Hewlett Packard Enterprise Development LP.
# Apache License 2.0

from pyaoscx.utils.connection import connected
from pyaoscx.exceptions.request_error import HttpRequestError
from pyaoscx.exceptions.generic_op_error import GenericOperationError

from pyaoscx.pyaoscx_module import PyaoscxModule

import json
import logging
import pyaoscx.utils.util as utils


class PoEInterface(PyaoscxModule):
    '''
    Provide configuration management for PoE Interface on AOS-CX devices.
    '''

    resource_uri_name = 'poe_interface'

    def __init__(self, session, parent_interface, uri=None, **kwargs):
        """
        Create an instance of PoEInterface Class
        :param session: pyaoscx.Session object used to represent a logical
            connection to the device
        :param parent_interface: parent Inferface object where PoE is stored
        :param uri: String with the PoE URI
        :param kwargs:
            keyword s: requests.session object with loaded cookie jar
            keyword url: URL in main() function
        """

        self.session = session
        # Assign parent Interface object
        self.__set_interface(parent_interface)
        self._uri = uri
        # List used to determine attributes related to the PoEInterface
        # configuration
        self.config_attrs = []
        # Attribute dictionary used to manage the original data
        # obtained from the GET
        self.__original_attributes = {}
        self.materialized = False
        # Set arguments needed for correct creation
        utils.set_creation_attrs(self, **kwargs)
        # Attribute used to know if object was changed recently
        self.__modified = False

    def __set_interface(self, parent_interface):
        """
        Set parent Interface object as an attribute for the PoEInterface class
        :param parent_interface: an Interface object
        """
        # Self parent Interface object
        self.__parent_interface = parent_interface

        # Set URI
        self.base_uri = '{base_int_uri}/{interface_name}/{resource}'.format(
            base_int_uri=self.__parent_interface.base_uri,
            interface_name=self.__parent_interface.percents_name,
            resource=self.resource_uri_name
        )

    @connected
    def get(self, depth=None, selector=None):
        """
        Perform a GET call to retrieve data for a PoE Interface table entry and
            fill the object with the incoming attributes

        :param depth: Integer deciding how many levels into the API JSON that
            references will be returned.
        :param selector: Alphanumeric option to select specific information to
            return.
        :return: Returns True if there is not an exception raised
        """
        logging.info("Retrieving the switch PoE Interface")

        depth = self.session.api_version.default_depth\
            if depth is None else depth

        selector = self.session.api_version.default_selector\
            if selector is None else selector

        if not self.session.api_version.valid_depth(depth):
            depths = self.session.api_version.valid_depths
            raise ValueError("ERROR: Depth should be {}".format(depths))

        if selector not in self.session.api_version.valid_selectors:
            selectors = ' '.join(self.session.api_version.valid_selectors)
            raise ValueError(
                "ERROR: Selector should be one of {}".format(selectors))

        # Set payload
        payload = {
            "depth": depth,
            "selector": selector
        }

        # Set URI
        uri = "{base_url}{class_uri}".format(
            base_url=self.session.base_url,
            class_uri=self.base_uri
        )

        # Try to get a response to use its data
        try:
            response = self.session.s.get(
                uri, verify=False, params=payload, proxies=self.session.proxy)

        except Exception as e:
            raise HttpRequestError('GET', e)

        if not utils._response_ok(response, "GET"):
            raise GenericOperationError(response.text, response.status_code)

        data = json.loads(response.text)

        # Add dictionary as attributes for the object
        utils.create_attrs(self, data)

        # Determines if the PoE Interface is configurable
        if selector in self.session.api_version.configurable_selectors:
            # Set self.config_attrs
            utils.set_config_attrs(
                self, data, 'config_attrs')

        # Set original attributes
        self.__original_attributes = data

        # Set object as materialized
        self.materialized = True

        return True

    @connected
    def apply(self):
        """
        Apply an update of values of this PoE Interface.
        Calls self.update() to apply changes to an existing PoE Interface table entry.
        """
        if not self.__parent_interface.materialized:
            self.__parent_interface.apply()

        modified = False
        if self.materialized:
            modified = self.update()

        # Set internal attribute
        self.__modified = modified
        return modified

    @connected
    def update(self):
        """
        Perform a PUT call to apply changes to an existing PoE Interface table entry

        :return modified: True if Object was modified and a PUT request was made.
            False otherwise
        """
        # Variable returned
        modified = False

        poe_interface_data = {}

        poe_interface_data = utils.get_attrs(self, self.config_attrs)

        # Set URI
        uri = "{base_url}{class_uri}".format(
            base_url=self.session.base_url,
            class_uri=self.base_uri
        )

        # Compare dictionaries
        if poe_interface_data == self.__original_attributes:
            # Object was not modified
            modified = False

        else:
            post_data = json.dumps(
                poe_interface_data, sort_keys=True, indent=4)
            try:
                response = self.session.s.put(
                    uri, verify=False, data=post_data, proxies=self.session.proxy)

            except Exception as e:
                raise HttpRequestError('PUT', e)

            if not utils._response_ok(response, "PUT"):
                raise GenericOperationError(
                    response.text, response.status_code)
            else:
                logging.info(
                    "SUCCESS: Update PoE Interface entry {} succeeded".format(
                        self))

            # Set new original attributes
            self.__original_attributes = poe_interface_data

            # Object was modified
            modified = True

        return modified

    @connected
    def create(self):
        pass

    @connected
    def delete(self):
        pass

    @connected
    def get_all(self):
        pass

    @classmethod
    def from_uri(cls):
        pass

    def __str__(self):
        return "PoE Interface {}".format(self.__parent_interface.name)

    def get_uri(self):
        """
        Method used to obtain the specific PoE Interface URI
        return: Object's URI
        """
        if self._uri is None:
            self._uri = "{base_url}{class_uri}".format(
                base_url=self.session.base_url,
                class_uri=self.base_uri
            )

        return self._uri

    def get_info_format(self):
        pass

    def was_modified(self):
        """
        Getter method for the __modified attribute
        :return: Boolean True if the object was recently modified, False otherwise.
        """

        return self.__modified

    ####################################################################
    # IMPERATIVES FUNCTIONS
    ####################################################################

    def set_criticality(self, level):
        """
        Set the criticality level for the PoE Interface.

        :param level: String containing criticality level for the related PoE Interface.
            Valid criticality levels: 'low', 'high', and 'critical'.
        :return: Returns True if there is not an exception raised
        """
        valid_criticalities = ['low', 'high', 'critical']
        if level not in valid_criticalities:
            raise ValueError(
                "ERROR: Criticality level should be one of {}".format(valid_criticalities))

        # Set power level
        self.config['priority'] = level

        # Update changes
        return self.apply()

    def set_power(self, state):
        """
        Perform a PUT call to set a configurable flag to control PoE power delivery on
        this Interface. A value of True would enable PoE power delivery on this Interface,
        and a value of False would disable PoE power delivery on this Interface.

        :return: True if Object was modified and a PUT request was made.
        """

        # Switches the state to a coherent value for the API documentation
        self.config['admin_disable'] = not state

        # Update changes
        return self.apply()