#!/usr/bin/env python

import sys
import json
import requests

from herepy.here_api import HEREApi
from herepy.utils import Utils
from herepy.error import HEREError, UnauthorizedError, InvalidRequestError
from herepy.models import TrafficIncidentResponse
from herepy.here_enum import IncidentsCriticalityStr, IncidentsCriticalityInt

from typing import List, Optional


class TrafficApi(HEREApi):
    """A python interface into the HERE Traffic API"""

    def __init__(self,
                 api_key: str=None,
                 timeout: int=None):
        """Returns a TrafficApi instance.
        Args:
          api_key (str):
            API key taken from HERE Developer Portal.
          timeout (int):
            Timeout limit for requests.
        """

        super(TrafficApi, self).__init__(api_key, timeout)
        self._base_url = 'https://traffic.ls.hereapi.com/traffic/6.0/'


    def __get(self, url, data):
        url = Utils.build_url(url, extra_params=data)
        response = requests.get(url, timeout=self._timeout)
        json_data = json.loads(response.content.decode('utf8'))
        if json_data.get('TRAFFICITEMS') != None:
            return TrafficIncidentResponse.new_from_jsondict(
                json_data, param_defaults={'TRAFFICITEMS': None}
            )
        else:
            error = self.__get_error_from_response(json_data)
            raise error


    def __get_error_from_response(self, json_data):
        if "error" in json_data:
            if json_data["error"] == "Unauthorized":
                return UnauthorizedError(json_data["error_description"])
        error_type = json_data.get("Type")
        error_message = json_data.get(
            "Message", "Error occured on " + sys._getframe(1).f_code.co_name
        )
        if error_type == "Invalid Request":
            return InvalidRequestError(error_message)
        else:
            return HEREError(error_message)


    def __prepare_criticality_str_values(self, criticality_enums: [IncidentsCriticalityStr]):
        criticality_values = ""
        for criticality in criticality_enums:
            criticality_values += criticality.__str__() + ','
        criticality_values = criticality_values[:-1]
        return criticality_values


    def __prepare_criticality_int_values(self, criticality_enums: [IncidentsCriticalityInt]):
        criticality_values = ''
        for criticality in criticality_enums:
            criticality_values += str(criticality.__int__()) + ','
        criticality_values = criticality_values[:-1]
        return criticality_values


    def __prepare_corridor_value(self, points: List[List[float]], width: int):
        corridor_str = ''
        for lat_long_pair in points:
            corridor_str += str.format('{0},{1};', lat_long_pair[0], lat_long_pair[1])
        corridor_str += str(width)
        return corridor_str


    def incidents_in_bounding_box(self, top_left: List[float],
                    bottom_right: List[float], criticality: [IncidentsCriticalityStr]) -> Optional[TrafficIncidentResponse]:
        """Request traffic incident information within specified area.
        Args:
          top_left (array):
            Array including latitude and longitude in order.
          bottom_right (array):
            Array including latitude and longitude in order.
          criticality (array):
            List of IncidentsCriticalityStr.
        Returns:
          TrafficIncidentResponse
        Raises:
          HEREError"""

        data = {'bbox': str.format('{0},{1};{2},{3}', top_left[0], top_left[1], bottom_right[0], bottom_right[1]),
                'apiKey': self._api_key,
                'criticality': self.__prepare_criticality_str_values(criticality_enums=criticality)}
        return self.__get(self._base_url + 'incidents.json', data)


    def incidents_in_corridor(self, points: List[List[float]], width: int) -> Optional[TrafficIncidentResponse]:
        """Request traffic incidents for a defined route.
        Args:
          points (array):
            Array including array of latitude and longitude pairs in order.
          width (int):
            Width of corridor.
        Returns:
          TrafficIncidentResponse
        Raises:
          HEREError"""

        data = {'corridor': self.__prepare_corridor_value(points=points, width=width),
                'apiKey': self._api_key}
        return self.__get(self._base_url + 'incidents.json', data)


    def incidents_via_proximity(self, latitude: float, longitude: float,
                  radius: int, criticality: [IncidentsCriticalityInt]) -> Optional[TrafficIncidentResponse]:
        """Request traffic incident information within specified area.
        Args:
          latitude (float):
            Latitude of specified area.
          longitude (float):
            Longitude of specified area.
          radius (int):
            Radius of area in meters.
          criticality (array):
            List of IncidentsCriticalityInt.
        Returns:
          TrafficIncidentResponse
        Raises:
          HEREError"""

        data = {'prox': str.format('{0},{1},{2}', latitude, longitude, radius),
                'criticality': self.__prepare_criticality_int_values(criticality_enums=criticality),
                'apiKey': self._api_key}
        return self.__get(self._base_url + 'incidents.json', data)
