#!/usr/bin/env python
from setuptools import setup, find_packages
from entangled import __version__


with open('README.md') as fh:
    long_description = fh.read()


CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Framework :: Django :: 1.11',
    'Framework :: Django :: 2.0',
    'Framework :: Django :: 2.1',
    'Framework :: Django :: 2.2',
]

setup(
    name='django-entangled',
    version=__version__,
    description='Edit JSON field using Django Model Form',
    author='Jacob Rief',
    author_email='jacob.rief@gmail.com',
    url='https://github.com/jrief/django-entangled',
    packages=find_packages(),
    license='MIT',
    platforms=['OS Independent'],
    keywords=['Django Forms', 'JSON'],
    classifiers=CLASSIFIERS,
    long_description=long_description,
    long_description_content_type='text/markdown',
    include_package_data=True,
    zip_safe=False
)
