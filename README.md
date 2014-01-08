sms-fixer
=========

Simple recovery script and Web service to convert Google Voice HTML logs into the Android app [SMS Backup & Restore](https://play.google.com/store/apps/details?id=com.riteshsahu.SMSBackupRestore&hl=en).

Requirements
------------

For standalone script `src/fixer.py`:

* python 2.6+
* pip
* virtualenv

Additional for Web service:

* nginx
* supervisord

Installing
----------

Exact commands vary with OS.

1. Clone git repository. 
2. Create a virtual environment in the same directory, and source the `activate` script. 
3. Navigate into the directory and install the required Python packages with `pip install -r requirements.txt`.

For the Web service (CentOS-tested only):

1. Symlink or copy the file `conf/nginx.conf` into the nginx configuration directory (e.g. `/etc/nginx/conf.d/sms-fixer.conf` for CentOS).
2. Symlink or copy the file `conf/supervisord.conf` into the supervisord configuration directory.
3. Reload the config files of both nginx and supervisord, and ensure that both daemons are running.

Note that you probably need to edit the config files to point to the directory in which you cloned this repo as well as the `server_name` for nginx.

Using
-----

The standalone script can be used by activating the virtual environment and running `python src/fixer.py`. Instructions available via the `--help` flag. Timezones for the `--timezone` flag can be found on [Wikipedia](http://en.wikipedia.org/wiki/List_of_IANA_time_zones). 

The Web service should be accessed via the URL configured in the `conf/nginx.conf` file.

Updating
--------

To update, just run `git pull` in the repository. For the Web service, you may need to instruct supervisord to restart the daemons.

Disclaimers
-----------

"Google Voice" and "Android" are trademarks of Google Voice, Inc. 

"SMS Backup & Restore" is a trademark of Ritesh Sahu.

The `sms.xml` file used for styling the output XML is intellectual property of Ritesh Sahu.