"""This module implements a thin wrapper for MySQLdb for the WeatherUnderground scripts"""
import MySQLdb

class WeatherUpdateDatabase():
    """Thin wrapper class for MySQLdb for use with weather data.  The goal is to have
    this as generic as possible, so it could be resused"""

    def __init__(self):
        """Initialize the SQL wrapper"""
        self.db = None
        self.cursor = None
        self.dbname = None
        self.verbose = True

    def connect(self, hostname, username, password):
        """Connect to an instance of MySQL"""
        if self.verbose:
            print(str("CONNECTING TO SQL HOST {0}, User:{1}, Pass:*****").format(hostname, username))

        # Pass through to MySQLdb
        self.db = MySQLdb.connect(host=hostname, user=username, passwd=password)
        # Save our cursor
        self.cursor = self.db.cursor()

    def close_connection(self):
        """Close the current connection"""
        if self.verbose:
            print('CLOSING DATABASE...')
        self.db.close()

    def execute(self, sql):
        """Execute the given SQL statement"""
        # This is extremely useful when debugging constructed SQL statements that are failing
        if self.verbose:
            print('SQL: ' + sql)
        self.cursor.execute(sql)

    def commit(self):
        """Attempt to commit the database, exceptions are rolled back"""

        try:
            self.db.commit()
            if self.verbose:
                print('COMMITTED.')
        except (MySQLdb.Error) as e:
            print(e)
            self.db.rollback()
            if self.verbose:
                print('ROLLED BACK.')

    def open_or_create_database(self, database_name):
        """Check if the database exists, and if it does not, create it.
        Either way, select the database for use"""

        # Save the name, later when checking for tables, restrict to just this
        # database name, otherwise we'll find tables in the schema for other
        # databases (if they exist that is)
        self.dbname = database_name

        # Check the schema for the existance of the database, should only be one by name
        db_exists = False
        sql = str('SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = \'{0}\'').format(database_name)
        self.execute(sql)
        if self.cursor.rowcount == 1:
            self.cursor.fetchall()
            db_exists = True
            if self.verbose:
                print('OPENING DATABASE...')
            
        if not db_exists:
            sql = str('CREATE DATABASE {0}').format(database_name)
            if self.verbose:
                print('CREATING DATABASE...')
            self.execute(sql)

        # Either way we want to use it
        self.execute('USE ' + database_name)
        return not db_exists

    def drop_table(self, table_name):
        """Deletes the table from the database if it exists"""
        sql = 'DROP TABLE IF EXISTS ' + table_name
        self.execute(sql)

    def open_or_create_table(self, table_name, autokey_name, *args):
        """Create or open a table
        table_name: name of the table
        autokey_name: Table must have an integer autokey, use this name for it
        *args: list of column definitions
        """
        if not self.table_exists(table_name): 
            sql = str('CREATE TABLE {0} ({1} integer primary key auto_increment').format(table_name, autokey_name)
            for arg in args:
                sql += ', ' + arg
            sql += ') ENGINE=InnoDB'
            self.execute(sql)
            return True
        return False
    
    def add_foreign_key_constraint(self, table_name, key_name, refs_table_name, refs_col_id):
        """Adds a foreign key constraint for a table.  This is used to prevent deletions on data
        that references the key
        table_name: name of the table
        key_name: foreign key name
        refs_table_name: table key is referencing
        refs_col_id: col in referenced table for foreign key
        """
        sql = str("ALTER TABLE {0} ADD CONSTRAINT {1}_ref FOREIGN KEY ({1}) REFERENCES {2} ({3})").format(table_name, key_name, refs_table_name, refs_col_id)
        self.execute(sql)

    def table_exists(self, table_name):
        """True if the table exists in the current database"""
        # It's possible to have the same table name in another database, like when you switch
        # the name to test changes w/o destroying the old data.  Without the database name
        # this query will find those tables (and we don't care if they exist here)
        sql = str("SELECT * FROM information_schema.tables WHERE table_name ='{0}' AND table_schema='{1}'").format(table_name, self.dbname)
        self.execute(sql)
        
        if self.cursor.rowcount > 0:
            self.cursor.fetchall()
            return True
        return False

    def row_exists_in_table(self, table_name, column_id, column_value):
        """True if the row exists in table"""
        sql = str("SELECT * FROM {0} WHERE {1}='{2}'").format(table_name, column_id, column_value)
        self.execute(sql)
        
        if self.cursor.rowcount > 0:
            self.cursor.fetchall()
            return True
        return False

    def get_row_in_table(self, table_name, column_id, column_value):
        """Gets a single row in the table by column id.  This works only when the column id is
        unique, which in our case it always will be (likely the station_id)"""
        sql = str("SELECT * FROM {0} WHERE {1}='{2}'").format(table_name, column_id, column_value)
        self.execute(sql)
        
        # If a row with the given column_id exists in the table, it will be fetched here
        values = []
        if self.cursor.rowcount > 0:
            cols = self.cursor.fetchall()
            values.extend(cols)

        # fetchall returns a list of rows, however, there should only ever be 1 row here
        # so we could use fetchone instead above, or just return the first item in fetchall
        return values[0]
    
    def get_column_values_by_id(self, table_name, column_id):
        """Gets all column values with the matching column id"""
        sql = str('SELECT {0} FROM {1}').format(column_id, table_name)
        self.execute(sql)

        return self.cursor.fetchall()

    # SELECT col_id0 [, col_id1, cold_id2, ...] FROM table_id WHERE pk_id=pk_val)
    # SELECT weather, temp_f, relative_humidity, city, time FROM {0} WHERE station_id = \'{1}\'').format('weather_nearby', station_id)
    def get_rows_by_column_id(self, table_name, query_key_name, query_key_value, col_data):
        """Gets a list of rows of the specified columns given a column id
        table_name: name of the table
        query_key_name: col id that is the pivot
        query_key_value: value to pivot on
        col_data: list of column ids to return
        """
        # Used to look up weather data for a given station id
        sql = "SELECT "
        for col_id in col_data:
            sql += col_id + ','

        # Strip off that last ,
        sql = sql[:-1]

        sql += ' FROM ' + table_name + ' WHERE ' + query_key_name + '=\'' + str(query_key_value) + '\''
        self.execute(sql)
        return self.cursor.fetchall()

    # "INSERT INTO table_id(col0_name[, col1_name...]) VALUES(val_0 [, val_1, ...])"
    def add_row_to_table(self, table_name, col_data):
        """Add a new row into the table
        table_name: name of the table
        col_data: list of tuples that contain column (id, val, quote?)"""

        arg_count = len(col_data)
        tups = col_data
        
        # The trick here is building the INSERT and VALUE portions of the SQL
        # separately, then joining them
        sqlfront = str("INSERT INTO {0}(").format(table_name)
        sqlvalues = str("VALUES(")

        for value_index in range(arg_count):
            sqlfront += str("{0}").format(tups[value_index][0])
            if tups[value_index][2]: # Quote enclosed
                sqlvalues += "'" +  tups[value_index][1] + "'"
            else:
                sqlvalues += str("{0}").format(tups[value_index][1])

            # Next in sequence, or cap off the end of the strings
            if value_index != arg_count-1:
                sqlfront += ", "
                sqlvalues += ", "
            else:
                sqlfront += ") "
                sqlvalues += ")"

        # Now join the INSERT and VALUE strings and execute
        sql = sqlfront + sqlvalues
        self.execute(sql)

    # "UPDATE table_name SET col0_name=val_0 [, col1_name=val_1, ...] WHERE primary_key_name=primary_key_value"
    def update_row_by_primary_key(self, table_name, primary_key_name, primary_key_value, col_data):
        """Update an existing row, specified by its primary key
        table_name: name of the table
        col_data: list of tuples that contain column (id, val, quote?)"""
        # Slightly easier than the insert case, since we set the values as we go in the SQL
        arg_count = len(col_data)
        tups = col_data
        
        sql = str("UPDATE {0} SET ").format(table_name)
        
        for value_index in range(arg_count):
            if tups[value_index][2]: # Quote enclosed
                sql += str("{0}='{1}'").format(tups[value_index][0], tups[value_index][1])
            else:
                sql += str("{0}={1}").format(tups[value_index][0], tups[value_index][1])
            
            if value_index != arg_count-1:
                sql += ", "
            else:
                sql += " "

        # Add the conditional to restrict to the row with the matching primary key value
        sql += str("WHERE {0}='{1}'").format(primary_key_name, primary_key_value)
        self.execute(sql)
