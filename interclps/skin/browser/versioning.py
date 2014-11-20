# -*- coding: utf-8 -*-

from ghdiff import diff
from BeautifulSoup import BeautifulSoup
from Products.Five import BrowserView


class Versioning(BrowserView):

    def getDiff(self, oldValue, newValue):
        """
        Renvoie un diff formaté entre deux valeurs
        Si le champs contient des tags html, ceux-ci sont ignorés
        """
        if oldValue == newValue:
            return None
        oldValue = self.stripHTML(oldValue)
        newValue = self.stripHTML(newValue)
        return diff(oldValue, newValue)

    def stripHTML(self, text):
        return ''.join(BeautifulSoup(text).findAll(text=True))
