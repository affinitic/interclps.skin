from setuptools import setup, find_packages
import os

version = '1.0'

setup(name='interclps.skin',
      version=version,
      description="interclps skin by Affinitic",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='',
      author='Affinitic sprl',
      author_email='info@affinitic.be',
      url='http://svn.plone.org/svn/collective/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['interclps'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
            'setuptools',
            'Products.AddRemoveWidget',
            'plone.app.theming',
            'plone.app.themingplugins',
            'collective.js.jqueryui',
            'simplejson',
            'plone.resource',
            'lxml',
            'reportlab',
            'BeautifulSoup',
            'ghdiff',
            'affinitic.imageuploader'],
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      setup_requires=["PasteScript"],
      paster_plugins=["ZopeSkel"],
      )
