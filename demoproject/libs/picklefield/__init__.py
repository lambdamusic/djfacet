"""Pickle field implementation for Django."""

DEFAULT_PROTOCOL = 2

from picklefield.fields import PickledObjectField # reexport





# 
# setup(name='django-picklefield',
#     version='0.1.9',
#     description='Pickled object field for Django',
#     long_description=open('README').read(),
#     author='Gintautas Miliauskas',
#     author_email='gintautas@miliauskas.lt',
#     url='http://github.com/gintas/django-picklefield',
#     packages=find_packages('src'),
#     package_dir={'' : 'src'},
#     classifiers=[
#         'Development Status :: 4 - Beta',
#         'Framework :: Django',
#         'License :: OSI Approved :: MIT License',
#     ]
# )