"""
WSGI config for jucha_ERP project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os
import sys
import site
from os.path import dirname, abspath

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jucha_ERP.settings')
python_home = '/home/jucha/django'
python_version = '.'.join(map(str, sys.version_info[:2]))
site_packages = python_home + '/lib/python%s/site-packages' % python_version
PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)
site.addsitedir(site_packages)

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "travel_record.settings")
os.environ["DJANGO_SETTINGS_MODULE"] = "jucha_ERP.settings"
print(sys.path)
print(sys.version)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
