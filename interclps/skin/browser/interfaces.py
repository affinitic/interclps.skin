# -*- coding: utf-8 -*-

from plone.theme.interfaces import IDefaultPloneLayer
from zope.interface import Interface


class IInterClpsTheme(IDefaultPloneLayer):
    """
    Theme for interclpsbw
    """


class IPdfGenerator(Interface):
    """
    generation d'un pdf
    """

    def printExperience(experiencePk):
        """
        genere le pdf d'une experience selon sa pk
        """

    def printInstitution(institutionPk):
        """
        genere le pdf d'une institution selon sa pk
        """


class IHomePageNews(Interface):
    """
    Gestion des news sur la homepage
    """

    def getNews():
        """
        liste les news
        """

    def getNewsIconURL(newsBrain):
        """
        récupère l'icône d'une news (ou celle par défaut)
        """


class IBannerView(Interface):
    """
    Gestion des banners
    """

    def getBanner():
        """
        return the banner regarding folder
        """


class IManageInterClps(Interface):
    """
    gestion plateforme
    """

    def getWysiwygField(name, value):
        """
        generates a WYSIWYG field containing value
        """

    def getAddRemoveField(name, title, values, nameKey='name', pkKey='pk', \
                          selectedPks=[]):
        """
        generates an Add / Remove from list field with already selected pks
        nameKey and pkKey are used for the display value and the record pk to
        save
        """

    def checkCaptchaDemandeInscription():
        """
        check le captcha
        """

    def getAuteurTypeByLogin():
        """
        table pg auteur
        recuperation du type d'auteur (experience - institution) selon son login
        """

    def getAllAuteurFromInstitution():
        """
        table pg auteur
        recuperation de toutes les auteurs d'institution
        """

    def isAuteurHadExperience(auteurPk):
        """
        check si un auteur a une experience
        """

    def isAuteurHadInstitution(auteurPk):
        """
        check si un auteur a une institution
        """

    def deleteAuteurByPk(auteurPk):
        """
        supprime un auteur selon sa pk
        """

    def getAllCommune():
        """
        select all commune
        """

    def getAllTheme():
        """
        select all theme
        """

    def getThemeByPk(theme_pk):
        """
        select theme by pk
        """

    def getAllMotCle():
        """
        select all mot-cle
        """

    def getMotCleByPk(motcle_pk):
        """
        select mot-cle by pk
        """

    def getAllInstance():
        """
        select all instance
        """

    def getInstitutionByPlateForme(plateForme):
        """
        recuperation d'un recit selon la plateForme
        """

    def getAllSupport():
        """
        select all support
        """

    def getSupportByPk():
        """
        select support by pk
        """

    def getAllRessource():
        """
        select all ressource
        """

    def getRessourceByPk():
        """
        select ressource selon pk
        """

    def getTranslationExperienceEtat(selef, etat):
        """
        traduction de l'état d'une experience
        """

    def getExperienceByPlateForme(plateForme):
        """
        recuperation d'un recit selon la plateForme
        """

    def getAllExperienceByEtat(etatExperience):
        """
        table pg experience
        recuperation d'un recit selon experience_pk
        private pending publish
        """

    def getExperienceByClpsByEtat(clpsPk):
        """
        table pg experience
        recuperation d'une experience selon experience_clps_proprio_fk et son etat
        """

    def getExperienceByRessource(ressourcePk):
        """
        recuperation d'une experience selon une ressource
        """

    def getLastExperience(limite=None):
        """
        table pg experience
        recuperation d'une experience selon
           la date de modification
           une limite de 5
           l'etat publish
        """

    def getCountExperienceByEtat(etatExperience):
        """
        table pg experience
        recuperation du nombre d'experience selon experience_etat
        private pending publish
        """

    def getCountAllExperience():
        """
        table pg experience
        recuperation du nombre d'experience
        """

    def getCountInstitutionByEtat(institutionEtat):
        """
        table pg institution
        recuperation du nombre d'institution selon institution_etat
        private publish
        """

    def getCountAllInstitution():
        """
        table pg institution
        recuperation du nombre total d'institution
        """

    def getMilieuDeVieByExperiencePk(experiencePk, retour):
        """
        recuperation des milieux de vie lies a une experience
        """

    def addOutil():
        """
        inset un outil
        """

    def addOuvrage():
        """
        insert un nouvel ouvrage
        """

    def addInsttution():
        """
        insert une nouvelle institution
        """

    def addExperiene():
        """
        insert une nouvelle experience
        """

    def manageMotCle():
        """
        insertion ou update des donnees mot-cle
        """

    def manageInstitutionType():
        """
        insertion ou update des donnees theme
        """

    def manageTheme():
        """
        insertion ou update des donnees theme
        """

    def manageRessource():
        """
        insertion ou update des donnees ressource
        """

    def demandeInscription():
        """
        demande d'inscription
        """

    def manageAssuetudeInterventionForInstitution():
        """
        gestion des assuetude intervention pour institution
        """

    def manageAssuetudeActiviteProposeeForInstitution():
        """
        gestion des assuetude activite proposee pour institution
        """

    def manageAssuetudeThematiqueForInstitution():
        """
        gestion des assuetude thematique pour institution
        """
