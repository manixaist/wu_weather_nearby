"""This module shows how to get weather info from WeatherUnderground REST API and store it in a MySQLdb"""
import src.wu_api_wrapper
import src.mysql_user_info #.GITIGNORED
import src.wu_mysql_wrapper

# Helper
def round_float_and_check(a, b):
    """Helper for checking if the LAT or LON have changed.  This will clamp a float to 
    a specific number of total digits and then compare them
    
    a: float to compare against
    b: float to round after clamping to the total number of digits in 'a'
    returns: True if b once clamped and rounded is equal to a

    Remarks:  The reason for this function is the LAT/LON values stored into SQL get
    truncated as floats to some total digit length.  As floats in python and as returned
    by the REST API they are much longer.  So just comparing stored values to those
    on the wire is not enough.  If you don't care about limiting writes (UPDATES) you could
    just drop this check, but limiting database writes is almost always a good thing
    """
    parts = str(a).split('.')
    int_len = len(parts[0])
    dec_len = len(parts[1])
    float_len = int_len + dec_len
    return a == round(b, float_len - int_len)

###############################################################################
# START OF REST CODE - FETCHING AND PARSING DATA FROM THE CLOUD
###############################################################################
# Configuration dictionary - this holds all sorts of values, like the database
# and table names, the REST API queries, and diagnostic flags
conf = src.weather_conf.WeatherConfig()

# Wrapper for the Weather Underdrgound API calls
wu = src.wu_api_wrapper.WeatherUnderground()

# This call goes to the cloud to get/parse/return data about nearby weather 
# stations and conditions.  Look in here for the REST code
weather_info = wu.get_weather_and_pws_info()

# Print returned PWS/Weather data for console
print('_'*80)
print()
print(str('PWS FOUND NEARBY (MAX:{0:^2})').format(conf.values['pws_max_extract']))
for pws_info in weather_info[0]:
    print('_'*80)
    wu.print_pws_info(pws_info)
    
    
print()
print('_'*80)
print()
print('OBSERVATION DATA FOR THE PWS LISTED ABOVE')
for observation in weather_info[1]:
    print('_'*80)
    wu.print_weather_observation(observation)

###############################################################################
# START OF MYSQL SECTION - STORING PARSED DATA IN A LOCAL DATABASE
###############################################################################
# This is where you'll find the code specific to this instance of the MySQLdb
# The wrapper is generic as possible, so all table, column names, definitions,
# etc are all at this layer.
print()
print('_'*80)
print()
print('ADD DATA TO MYSQL DATABASE')
print('_'*80)
# MySQLdb wrapper for weather data
dbw = src.wu_mysql_wrapper.WeatherUpdateDatabase()

# Connect to the host using the config information
dbw.connect(src.mysql_user_info.MYSQL_HOST, src.mysql_user_info.MYSQL_DB_USER, src.mysql_user_info.MYSQL_DB_PASS)

# Open the database (or create it if the first time)
created = dbw.open_or_create_database(conf.values['database_name'])

# Testing and schema changes only (should normally be False)
if conf.values['drop_all_tables']:
    # Deletes both tables from the database
    dbw.drop_table(conf.values['observation_table_name'])
    dbw.drop_table(conf.values['pws_table_name'])

# Create Table for the PWS data
pws_cols = ['id VARCHAR(20) UNIQUE KEY', 'latitude FLOAT', 'longitude FLOAT', 'city TEXT', 'neighborhood TEXT']
dbw.open_or_create_table(conf.values['pws_table_name'], 'autoid', *pws_cols)

# Create Table for OBSERVATION data
observation_cols = ['station_id VARCHAR(20)', 'time DATETIME', 'weather TEXT', 'temp_f FLOAT', 'temp_c FLOAT', 'relative_humidity TINYINT', 'uv_index FLOAT', 'precip_in FLOAT', 'pressure_in FLOAT', 'pressure_mb FLOAT', 'latitude FLOAT', 'longitude FLOAT', 'elevation INT', 'city TEXT', 'zip TEXT']
table_created = dbw.open_or_create_table(conf.values['observation_table_name'], 'id', *observation_cols)
if table_created:
    # Add our constraint.  This will prevent deletion of PWS data so long as OBSERVATION data references it
    dbw.add_foreign_key_constraint(conf.values['observation_table_name'], 'station_id', 'pws_nearby', 'id')

# Check each PWS returned from the cloud against the table
for pws_info in weather_info[0]:
    STATION_ID = str(pws_info['id'])
    LAT = float(pws_info['lat'])
    LON = float(pws_info['lon'])
    NEIGHBORHOOD = str(pws_info['neighborhood']).replace("'", "\\'")
    CITY = str(pws_info['city']).replace("'", "\\'")

    # The column definitions are the same in either INSERT or UPDATE cases
    params = [('id', STATION_ID, True), ('latitude', LAT, False), ('longitude', LON, False), ('city', CITY, True), ('neighborhood', NEIGHBORHOOD, True)]
    
    # Check if an entry exists (only 1 can exist per station_id)
    row_exists = dbw.row_exists_in_table(conf.values['pws_table_name'], 'id', STATION_ID)

    need_commit = False
    if row_exists:
        # UPDATE
        print('FOUND AN EXISTING PWS...')
        cols = dbw.get_row_in_table(conf.values['pws_table_name'], 'id', STATION_ID)
        AUTOID = cols[0]
    
        # LAT and LON get truncated to a total fixed length when written to the table.
        # So we need to simulate that before checking, otherwise it will appear to be 
        # updating all the time, but each write will re-truncate.  This avoids writes
        # that are not needed
        lat_diff = round_float_and_check(LAT, cols[2])
        lon_diff = round_float_and_check(LON, cols[3])
        
        # These checks are more straightforward
        id_diff = cols[1] != STATION_ID
        city_dif = str(cols[4]).replace("'", "\\'") != CITY
        neighborhood_diff = str(cols[5]).replace("'", "\\'") != NEIGHBORHOOD

        # If anything changed, update all of the columns with the new values
        if id_diff or lat_diff or lon_diff or city_dif or neighborhood_diff:
            need_commit = True
            dbw.update_row_by_primary_key(conf.values['pws_table_name'], 'autoid', AUTOID, params)
    else:
        # INSERT a new row for the PWS
        dbw.add_row_to_table(conf.values['pws_table_name'], params)
        need_commit = True
    
    if need_commit:
        dbw.commit()
    else:
        # The entry exists in the table, but it did not appear to be any different
        print('...IT DID NOT CHANGE')

# ADD NEW OBSERVATIONS TO TABLE
for observation in weather_info[1]:
    STATION_ID = str(observation['station_id'])
    TIME = observation['time']
    WEATHER = str(observation['weather']).replace("'", "\\'")
    TEMP_F = observation['temp_f']
    TEMP_C = observation['temp_c']
    REL_HUM = observation['relative_humidity']
    UV = observation['uv_index']
    PRECIP_IN = observation['precip_in']
    PRESSURE_IN = observation['pressure_in']
    PRESSURE_MB = observation['pressure_mb']
    LAT = observation['latitude']
    LON = observation['longitude']
    ELEVATION = observation['elevation']
    CITY = str(observation['city']).replace("'", "\\'")
    ZIP = observation['zip']

    # Every entry is unique by default thanks to a hidden auto-incrementing primary key
    # So just add each observation as a new row, no need to worry about updates
    params = [('station_id', STATION_ID, True), ('time', TIME, True), ('weather', WEATHER, True), 
              ('temp_f', TEMP_F, False), ('temp_c', TEMP_C, False), ('relative_humidity', REL_HUM, False), 
              ('uv_index', UV, False), ('precip_in', PRECIP_IN, False), ('pressure_in', PRESSURE_IN, False), 
              ('pressure_mb', PRESSURE_MB, False), ('latitude', LAT, False), ('longitude', LON, False), 
              ('elevation', ELEVATION, False), ('city', CITY, True), ('zip', ZIP, True)]

    dbw.add_row_to_table(conf.values['observation_table_name'], params)
    dbw.commit()

###############################################################################
# START OF VISUALIZATION EXAMPLE - DUMPING DATA BY STATION ID
###############################################################################
print()
print('PRINT THE OBSERVATION DATA FOR EACH STORED STATION')
print('_'*80)
print()
if conf.values['print_db']:
    rows = dbw.get_column_values_by_id(conf.values['pws_table_name'], 'id')

    for row in rows:
        # First column in the row (only one as well in this case)
        station_id = row[0]

        print()
        print('_'*80)
        print(str('QUERYING OBSERVATION TABLE FOR SUBSET OF DATA FOR PWS = "{0}"...').format(station_id))
        print('_'*80)
        # Get a subset of the data stored to print, note not everything stored is fetched here
        column_names = ['weather', 'temp_f', 'relative_humidity', 'city', 'time', 'id']
        weather_rows = dbw.get_rows_by_column_id(conf.values['observation_table_name'], 'station_id', station_id, column_names)

        for weather_row in weather_rows:
            print('_'*40)
            print('ENTRYID: ' + str(weather_row[5]))
            print('WEATHER: ' + str(weather_row[0]))
            print('TEMP(F): ' + str(weather_row[1]))
            print('HUM(%): ' + str(weather_row[2]))
            print('CITY: ' + str(weather_row[3]))
            print('TIME: ' + str(weather_row[4]))
            print()
else:
    print('PRINT DATABASE DISABLED BY SETTINGS...')

print('_'*80)

# Close the connection
dbw.close_connection()
