try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'A project for create, open, refine, and reuse conference data.',
    'author': 'Li Ding',
    'url': 'https://github.com/lidingpku/open-conference-data',
    'download_url': 'https://github.com/lidingpku/open-conference-data',
    'author_email': 'My email.',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['libconfdata'],
    'package_data':{'': ['*.jsont','*.sparql']},
    'scripts': [],
    'name': 'Open Conference Data'
}

setup(**config)
