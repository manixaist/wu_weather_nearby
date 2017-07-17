# weather_nearby
### Summary:
This project shows how to use the REST API from [WeatherUnderground](https://www.wunderground.com/api) to collect weather data from nearby personal weather stations (pws) and store information about both the pws used and the weather observations made into a MySQL database.  It then uses the tables created to show weather data for specific stations.

### Setup
---
In order to run this locally, there are a few dependencies.  I've listed what I used.  You can subsititute if you know what you're doing.  Though it might look long, most of it is fairly easy.

#### WeatherUnderground API KEY
You need to [sign up](https://www.wunderground.com/api) for one.  The developer version was free at the time I made this, but limits your calls (10/min 500/day IIRC).  For this reason, the script limits the amount of calls it makes per run, but still don't spam it or you may go over.  Unless you are abusive about, you will very likely be fine.

#### Settings
Have a look in the weather_conf.py script to see all of the settings you can tweak, but at a minimum, you should change the location searched to somewhere near you to make the data meaningful.  However, leaving it won't break anything.

```Python
    # LAT/LON to search for PWS - could replace with ZIP or other accepted formats
    # see https://www.wunderground.com/weather/api/
    # This location is Mountainview, CA (I picked it randomly)
    self.values['lat_lon'] = '37.392089,-122.083347'
```

Other values to consider might be the database or table names if you want them more specific (e.g. weather_near_podunk_anywhere_usa).

#### Python
I ran everything under Python 3.6 (both vanilla via IDLE/shell and Anaconda via VS Code).  There is nothing I know of that ties anything to these specific versions, it's just for reference.  The only issue I had (as a newbie to Python) was realizing/remembering I had 2 environments installed, and making sure I was running the correct version of pip to install the packages.  So, check that if it works in one but not the other.

However, **lxml** only worked for me with this specfic version (in both environments).  YMMV, but this was a requirement for me.
```python
from lxml import html #3.7.2 worked and 3.8 did not (IDLE vs ANACONDA for VSCODE)
```

**mysqlclient** is also needed (and pulls in **MySQLdb**).  I had no version problems, but for reference, my version is...
```
mysqlclient-1.3.10.dist-info
```

#### MySql
You will also need an instance of MySQL.  If you have one available, by all means use it.  You just need to add a file with the connection information (see below) and you're good.

Otherwise, you can do what I did and install a free version [here](https://dev.mysql.com/downloads/mysql/)

My version at the time was...
```
5.7.18.1
```
If you do install your own instance, I recommend creating a specific user with limited rights.  These scripts worked with the following access (under "Users and Priviledges"->Select your user-> "Administrative Roles").  

* DBManager
* DBDesigner
* BackupAdmin
* Custom (add REFERENCES from "Global Priviledges")

If you just create or use the admin account it will work, but then why have different account types...

#### Re-add .gitignored files
Two key files are not part of the repo.  Create them yourself under the ./src/ folder.  The reason they're not part of the repo is I don't want to give you my API key, and you won't want to share yours either.  The sql info is actually what I used, but it was a test instance long gone, so feel free to have them.
* wu_api_key.py - holds your WeatherUmderground API key
* mysql_user_info.py - holds your MySQL instance logon info

Here are samples that will **NOT** work as-is - just to be replaced with your values
**wu_api_key.py**

```python
"""This module has my WeatherUnderground API KEY"""
# WU API KEY - PROTECT THIS
# {INSERT YOUR KEY HERE}
```

**mysql_user_info.py**
```python
"""This module has MYSQL user and password data for a test database"""
MYSQL_DB_USER = "py_user"
MYSQL_DB_PASS = "P@ssw0rd!"
MYSQL_HOST = "localhost"
```

### Running
---
Just run the top-level script weather_nearby.py.  

### Sample Output and Tables
There is sample output in the [Example Output](./sample_output.txt)file.

Here is a screenshot of the PWS SQL table (from workbench)
![](/images/pws_table_sample.PNG)

Here is a screenshot of the OBSERVATION SQL table (from workbench)
![](/images/observation_table_sample.PNG)
