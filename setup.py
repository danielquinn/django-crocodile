import os
import crocodile
from setuptools import setup

# Allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="django-crocodile",
    version=crocodile.__version__,
    packages=["crocodile"],
    include_package_data=True,
    license="GPLv3",
    description="A simple CSS and Javascript aggregator for Django",
    long_description=open(os.path.join(os.path.dirname(__file__), "README.md")).read(),
    url="https://github.com/danielquinn/django-crocodile",
    download_url="https://github.com/danielquinn/django-crocodile",
    author="Daniel Quinn",
    author_email="code@danielquinn.org",
    maintainer="Daniel Quinn",
    maintainer_email="code@danielquinn.org",
    install_requires=[
        "cssmin>=0.1.4",
    ],
    classifiers=[
    	"Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
)
