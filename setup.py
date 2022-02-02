#!/usr/bin/env python
from setuptools import setup, find_packages
from entangled import __version__


with open('README.md') as fh:
    long_description = fh.read()


CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Framework :: Django :: 3.2',
    'Framework :: Django :: 4.0',
]

setup(
    name='django-entangled',
    version=__version__,
    description='Edit JSON field using Django Model Form',
    author='Jacob Rief',
    author_email='jacob.rief@gmail.com',
    url='https://github.com/jrief/django-entangled',
    packages=find_packages(),
    install_requires=[
        'django>=2.1',
    ],
    license='MIT',
    platforms=['OS Independent'],
    keywords=['Django Forms', 'JSON'],
    classifiers=CLASSIFIERS,
    long_description=long_description,
    long_description_content_type='text/markdown',
    include_package_data=True,
    zip_safe=False
)
