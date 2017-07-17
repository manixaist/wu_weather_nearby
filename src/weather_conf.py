"""This module holds configuration info for the WeatherUnderground scripts"""
from src.wu_api_key import API_KEY # .GITIGNORED FILE

class WeatherConfig():
    """Holds the configuration data for the weather api parser"""

    def __init__(self):
        """Initialize configuration settings"""
        self.values = {}
        
        # SERVER VALUES
        # False will attempt to use a previously saved local response
        self.values['use_live_server'] = True
        # Saves the last response from the server
        self.values['save_live_response'] = True
        # Base URL for querying nearby PWS - placeholder is for API KEY
        self.values['endpoint_url_format'] = 'http://api.wunderground.com/api/{0}/geolookup/q/'
        # Base URL for querying conditions at a given PWS - placeholder is for API KEY
        self.values['endpoint_stationid_format'] = 'http://api.wunderground.com/api/{0}/conditions/q/'
        # API_KEY is defined in .gitignored module
        self.values['api_key'] = API_KEY
        # Add the API_KEY
        self.values['endpoint_url_base'] = self.values['endpoint_url_format'].format(self.values['api_key'])
        # LAT/LON to search for PWS - could replace with ZIP or other accepted formats
        # see https://www.wunderground.com/weather/api/
        self.values['lat_lon'] = '37.392089,-122.083347'
        # Final GEOLOOKUP URL with json extension
        self.values['endpoint_url'] = self.values['endpoint_url_base'] + self.values['lat_lon'] + '.json'
        # Final CONDITIONS URL with json extension
        self.values['endpoint_url_stationid'] = self.values['endpoint_stationid_format'].format(self.values['api_key']) + 'pws:{0}.json'

        # DATABASE VALUES
        # Only useful for debug or schema changes, otherwise the tables should remain untouched
        self.values['drop_all_tables'] = False
        # Flag to control dumping contents of database
        self.values['print_db'] = True

        # Database name (can change for testing to preserve old data)
        self.values['database_name'] = 'wu_weather_nearby_mountainview_ca'
        #self.values['database_name'] = 'wu_weather_nearby_test'
        # TABLE name for PWS data
        self.values['pws_table_name'] = 'pws_nearby'
        # TABLE name for OBSERVATION data
        self.values['observation_table_name'] = 'weather_nearby'

        # MISC VALUES
        # Maximum distance in km to search for PWS
        self.values['pws_max_distance_km'] = 3
        # Maximum number of PWS data to extract.  The API_KEY I'm using is a developer key
        # It's free, but has limits on calls per min and per day.  We could easily go over
        # that without some limits
        self.values['pws_max_extract'] = 2
