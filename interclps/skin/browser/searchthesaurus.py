from lxml import etree
from zope.component import getUtility
from plone.memoize.forever import memoize
from Products.Five.browser import BrowserView
from z3c.json.interfaces import IJSONWriter



class SearchThesaurusAutoCompleteJSON(BrowserView):

    def __call__(self):
        searchString = self.request.form.get('name_startsWith')
        terms = self.getThesaurusByLeffeSearch(searchString)
        writer = getUtility(IJSONWriter)
        self.request.response.setHeader('content-type', 'application/json')
        return writer.write(terms)

    def getThesaurusByLeffeSearch(self, searchString):
        searchString = searchString.lower()
        values = self.getThesaurusXMLValues()
        filteredValues = [v for v in values if searchString in v.lower()]
        return filteredValues

    @memoize
    def getThesaurusXMLValues(self):
        xmlDoc = etree.parse('/home/alain/buildouts/interclps/src/interclps.skin/interclps/skin/browser/thesaurus_xml/thesaurus.xml')
        valueTags = xmlDoc.findall("//valeur")
        values = [tag.text.lower() for tag in valueTags]
        return values

    def render(self):
        pass
