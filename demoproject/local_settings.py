# ================
# LOCAL SETTINGS
# ================




DATABASES = {

    'default': {
	    'NAME': 'djfacet_demo',
	    'ENGINE': 'django.db.backends.mysql',
		'USER': 'root',
		# 'DATABASE_PORT' : '3306',
		'PASSWORD' : 'mikele' ,    # mikele or bea
		'HOST' : '127.0.0.1',
    }
}







# Make this unique and don't share it with anybody
SECRET_KEY = '*j%v!8#km*h#^llq58b_8!4w)5v42d%_h(9%ff72lc0r=_b)!w'


# set it if Apache is not handling python requests at the root level  
# PROD SERVER ==> "db/"
URL_PREFIX = ""


#  python -m smtpd -n -c DebuggingServer localhost:1025

EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = 'testing@example.com'


ACCOUNT_ACTIVATION_DAYS = 2








