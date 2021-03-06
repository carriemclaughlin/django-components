import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-components',
    version='0.1',
    packages=['components'],
    include_package_data=True,
    license='BSD License',
    description='A simple Django app to conduct Web-based polls.',
    long_description=README,
    url='https://github.com/brilliantorg/django-components',
    author='Sam Solomon',
    author_email='sam@brilliant.org',
    install_requires=['Django >= 1.4'],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
