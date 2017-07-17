"""This module encapsulates the api calls to weather underground and the data returned"""
import src.weather_conf
import json
from lxml import html #3.7.2 worked and 3.8 did not (IDLE vs ANACONDA for VSCODE)
from datetime import datetime
import random

# Only pull this in for live, otherwise the script is much faster
conf = src.weather_conf.WeatherConfig()
if conf.values['use_live_server']:
    import requests

class WeatherUnderground():
    """Wrapper for the REST calls and processing for WeatherUnderground"""

    def __init__(self):
        """Initialize the API wrapper"""
        self.conf = src.weather_conf.WeatherConfig()
        self.live = self.conf.values['use_live_server']
        self.primary_url = self.conf.values['endpoint_url']
        self.station_url_format = self.conf.values['endpoint_url_stationid']
        self.save_response = self.conf.values['save_live_response']
        self.pws_max_distance = self.conf.values['pws_max_distance_km']
        self.pws_max = self.conf.values['pws_max_extract']

    def get_weather_and_pws_info(self):
        """Finds nearby pws, queries them for conditions and returns both sets of results"""
        # Find the nearby personal weather stations
        nearby_pws = self.get_nearby_pws_info()
        
        # Go through the list and query each pws for their current conditions
        observations = []
        for pws_info in nearby_pws:
            pws_weather = self.get_pws_weather_response(pws_info['id'])
            observations.append(pws_weather)

        # Return both lists of dictionaries
        return (nearby_pws, observations)

    def get_server_response(self, query):
        """Generic server query - returns the json response"""
        json_bytes = None

        if self.live:
            print('REST QUERY: ' + query)
            json_bytes = requests.get(query)
            parsed_json = json.loads(json_bytes.content)
            if self.save_response:
                with open("RESPONSE_PARSED.txt", "wb") as bin_file:
                    bin_file.write(json_bytes.content)
        else:
            # Read a previous response for testing
            with open("RESPONSE_PARSED.txt", "rb") as bin_file:
                json_bytes = bin_file.read()
                parsed_json = json.loads(json_bytes)

        return parsed_json

    def get_nearby_pws_info(self):
        """Query the server for a list of pws (personal weather stations)"""
        # return a list of dictionaries holding the pws_info data

        # Look in weather_conf.py for settings on location, search radius, number returned
        parsed_json = self.get_server_response(self.primary_url)

        # Extract relevant info from the server response and return it
        nearyby_pws_info = self.function_to_extract_nearby_pws(parsed_json)
        return nearyby_pws_info

    def get_pws_weather_response(self, pws_id):
        pws_query = self.station_url_format.format(pws_id)
        server_response = self.get_server_response(pws_query)
        # Extract the observation data from this specific pws request
        ob_info = self.function_to_extract_observation_data(server_response)
        return ob_info

    def function_to_extract_nearby_pws(self, response):
        # Find the list of dicts that enclose the nearvy stations info
        response_dicts = response['location']['nearby_weather_stations']['pws']['station']

        # just so we don't always get the same X ones
        random.shuffle(response_dicts)

        # Find stations within DISTANCE_MAX_KM km of the returned station
        eligible_pws_stations = []
        for response_dict in response_dicts:
            if response_dict['distance_km'] <= self.pws_max_distance:
                eligible_pws_stations.append(response_dict)

        # Trim down stations - we could also just stop after adding 
        # but right now I like to be able to see the full list before it's trimmed
        return eligible_pws_stations[:self.pws_max]

    def function_to_extract_observation_data(self, response):
        
        CURRENT_OBS = response['current_observation']
        ob_data = {}
        
        OB_TIME = datetime.strptime(CURRENT_OBS['observation_time_rfc822'], '%a, %d %b %Y %H:%M:%S %z')
        OB_TIME = OB_TIME.strftime('%Y-%m-%d %H:%M:%S')
        
        ob_data['station_id'] = str(CURRENT_OBS['station_id'])
        ob_data['time'] = OB_TIME
        ob_data['weather'] = str(CURRENT_OBS['weather'])
        ob_data['temp_f'] = float(CURRENT_OBS['temp_f'])
        ob_data['temp_c'] = float(CURRENT_OBS['temp_c'])
        ob_data['relative_humidity'] = int(CURRENT_OBS['relative_humidity'].replace('%', ''))
        ob_data['uv_index'] = float(CURRENT_OBS['UV'].strip())
    
        # Precip might be '--' instead of blank or 0, so convert it to 0
        # it can also be -999.00 or 999 so there's that to deal with
        ob_data['precip_in'] = float(CURRENT_OBS['precip_today_in'].replace('-', '').strip())
        if ob_data['precip_in'] == 999:
            ob_data['precip_in'] = 0.0
    
        ob_data['pressure_in'] = float(CURRENT_OBS['pressure_in'].strip())
        ob_data['pressure_mb'] = float(CURRENT_OBS['pressure_mb'].strip())
        ob_data['latitude'] = float(CURRENT_OBS['observation_location']['latitude'].strip())
        ob_data['longitude'] = float(CURRENT_OBS['observation_location']['longitude'].strip())
        ob_data['elevation'] = int(str(CURRENT_OBS['observation_location']['elevation']).replace('ft', '').strip())
        ob_data['city'] = str(CURRENT_OBS['observation_location']['city'])
        ob_data['zip'] = str(CURRENT_OBS['display_location']['zip'])
        
        return ob_data

    def print_pws_info(self, pws_info):
        """Helper to dump PWS data"""
        # print some info on them
        print()
        print('ID: ' + str(pws_info['id']))
        print('KM: ' + str(pws_info['distance_km']))
        print('NEIGHBORHOOD: ' + str(pws_info['neighborhood']))


    def print_weather_observation(self, observation_record):
        """Helper to dump OBSERVATION data"""
        record = observation_record

        print()
        print('STATION ID: ' + record['station_id'])
        print('TIME: ' + str(record['time']))
        print('WEATHER: ' + record['weather'])
        print('T(F): ' + str(record['temp_f']))
        print('T(C): ' + str(record['temp_c']))
        print('REL HUM: ' + str(record['relative_humidity']) + '%')
        print('UV: ' + str(record['uv_index']))
        print('PRECIP(IN): ' + str(record['precip_in']))
        print('PRESSURE(IN): ' + str(record['pressure_in']))
        print('PRESSURE(MB): ' + str(record['pressure_mb']))
        print('LATITUDE: ' + str(record['latitude']))
        print('LONGITUDE: ' + str(record['longitude']))
        print('ELEVATION(ft): ' + str(record['elevation']))
        print('CITY: ' + record['city'])
        print('ZIPCODE: ' + record['zip'])

    
    