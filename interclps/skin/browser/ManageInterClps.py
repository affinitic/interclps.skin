# -*- coding: utf-8 -*-

import datetime
#import time
#import random
from sqlalchemy import select, func, and_
from mailer import Mailer
#from LocalFS import LocalFS
from Products.Five import BrowserView
from zope.interface import implements
from z3c.sqlalchemy import getSAWrapper
from plone.app.form.widgets.wysiwygwidget import WYSIWYGWidget
#from Products.CMFPlone.utils import normalizeString
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.AddRemoveWidget.AddRemoveWidget import AddRemoveWidget
from Products.Archetypes.atapi import LinesField
from Products.Archetypes.Renderer import renderer
from Products.Archetypes.atapi import BaseContent
from interfaces import IManageInterClps
from collective.captcha.browser.captcha import Captcha


class ManageInterClps(BrowserView):
    implements(IManageInterClps)

    def getTuple(self, data):
        dataTuple=()
        if type(data) is str:
            data=int(data)
        if type(data) is int:
            dataTuple = (data, )
        if type(data) is list:
            dataTuple = tuple(data)
        return(dataTuple)

    def getToDayDate(self):
        toDay = datetime.date.today()
        toDayString = ('%s')%(toDay)
        return toDayString

    def getTimeStamp(self):
        timeStamp = datetime.datetime.now()
        return timeStamp


### GESTION DES WIDGETS KUPU ADDREMOVELIST ###

    def getWysiwygField(self, name, value):
        """
        generates a WYSIWYG field containing value
        """

        class MyField:
            __name__ = name
            required = False
            default = value
            missing_value = None
            title = None
            description = None

        request = self.request
        request.form = {}
        field = WYSIWYGWidget(MyField(), request)
        return field()

    def getAddRemoveField(self, name, title, values, nameKey='name', \
                          pkKey='pk', selectedPks=[], canAddValues=False):
        """
        generates an Add / Remove from list field with already selected pks
        nameKey and pkKey are used for the display value and the record pk to
        save
        """
        selectedPks = [str(pk) for pk in selectedPks]

        class MyContext(BaseContent):

            def getSelectedValues(self):
                return selectedPks
        if not isinstance(nameKey, list):
            nameKey = [nameKey]
        items = []
        for value in values:
            if isinstance(value, dict):
                display = ' '.join([value.get(n) for n in nameKey])
                term = (str(value.get(pkKey)), display)
            else:
                display = ' '.join([getattr(value, n) for n in nameKey])
                term = (str(getattr(value, pkKey)), display)
            items.append(term)

        field = LinesField(name,
                           vocabulary=items,
                           edit_accessor='getSelectedValues',
                           enforceVocabulary=not canAddValues,
                           write_permission='View',
                           widget=AddRemoveWidget(size=10,
                                                  description='',
                                                  label=title))

        wrappedContext = MyContext('dummycontext').__of__(self.context)
        widget = field.widget
        res = renderer.render(name, 'edit', widget, wrappedContext, field=field)
        return res


### GESTION DES DEMANDES D'INSCRIPTION ###

    def checkCaptchaDemandeInscription(self):
        obj = self.context
        captcha = self.request.get('captcha', '')
        captchaView = Captcha(obj, self.request)
        isCorrectCaptcha = captchaView.verify(captcha)
        if isCorrectCaptcha:
            cible = "%s/experience-inscription-auteur-merci" % (obj.portal_url(), )
            obj.REQUEST.RESPONSE.redirect(cible)
            self.addAuteur()
            self.sendMailForNewAuteurExperience()

        else:
            obj.plone_utils.addPortalMessage(_(u"Erreur d'encodage du code du captcha."), 'error')
            self.request['captcha'] = ''
            return self()


### GESTION DES MAILS ###

    def sendMail(self, sujet, message, clpsEmailContact):
        """
        envoi de mail à iclps admin
        """
        #mailer = Mailer("localhost", "alain.meurant@affinitic.be, %s"%clpsEmailContact)
        mailer = Mailer("localhost", "alain.meurant@skynet.be")
        mailer.setSubject(sujet)
        #mailer.setRecipients("alain.meurant@affinitic.be, %s"%clpsEmailContact)
        mailer.setRecipients("alain.meurant@skynet.be")
        mail = message
        mailer.sendAllMail(mail)

    def sendMailWhenLoginByAuteur(self, sujet, message):
        """
        envoi de mail à iclps admin lorsqu'un auteur se loggue
        """
        mailer = Mailer("localhost", "alain.meurant@affinitic.be")
        #mailer = Mailer("relay.skynet.be", "alain.meurant@skynet.be")
        mailer.setSubject(sujet)
        mailer.setRecipients("alain.meurant@skynet.be")
        mail = message
        mailer.sendAllMail(mail)

    def sendMailForNewAuteurExperience(self):
        """
        envoi d'un mail lorsqu'un auteur fait une demande d'inscription
        """
        fields = self.context.REQUEST
        auteurNom = getattr(fields, 'auteur_nom', None)
        auteurPrenom = getattr(fields, 'auteur_prenom', None)
        auteurInstitution = getattr(fields, 'auteur_institution', None)
        auteurDescription = getattr(fields, 'auteur_description', None)
        clpsDestinationPk = getattr(fields, 'clpsDestinationPk')
        clpsDestinationPk = int(clpsDestinationPk)
        
        clpsInfo = self.getClpsByPk(clpsDestinationPk)
        clpsSigle = clpsInfo.clps_sigle
        clpsPrenomContact = clpsInfo.clps_prenom_contact
        clpsEmailContact = clpsInfo.clps_email_contact
        
        sujet = "[PROJETS PARTAGES  :: demande d'inscription d'un auteur]"
        message = u"""<font color='#FF0000'><b>:: Ajout d'un nouvel auteur pour %s ::</b></font><br /><br />
                  Bonjour %s, <br />
                  Une personne vient de s'inscrire via le site pour devenir auteur d'un récit partagé.<br />
                  Il s'agit de :<br />
                  <ul>
                    <li>Nom : <font color='#ff9c1b'><b>%s</b></font></li>
                    <li>Prénom : <font color='#ff9c1b'><b>%s</b></font></li>
                    <li>Organisme :  <font color='#ff9c1b'><b>%s</b></font></li>
                    <li>Description : <font color='#ff9c1b'><b>%s</b></font></li>
                  </ul>
                  <hr />
                  L'auteur est encodé dans la base, mais il n'est pas actif et n'a pas d'identifiant "FileMaker"
                  <br />
                  En modifiant l'auteur, tu peux l'activer et lui donner un dentifiant "FileMaker"
                  <br />
                  Voir la liste des auteurs en cliquant sur ce
                  <a href="http://www.projets-partages.be/admin-auteur-creer">lien</a>.
                  <hr />
                  """ \
                  %(clpsSigle, \
                    clpsPrenomContact, \
                    auteurNom, \
                    auteurPrenom, \
                    auteurInstitution, \
                    auteurDescription)
        message = message.encode('utf-8') 
        self.sendMail(sujet, message, clpsEmailContact)

    def sendMailForInsertExperience(self, experiencePk):
        """
        envoi d'un mail a Isabelle lors de la creation d'une experience
        """
        fields = self.context.REQUEST
        experience_pk = experiencePk
        experience_titre = getattr(fields, 'experience_titre', None)
        experience_personne_contact = getattr(fields, 'experience_personne_contact', None)
        experience_creation_employe = self.getUserAuthenticated()
        experience_etat = getattr(fields, 'experience_etat', None)
        experience_public_vise = getattr(fields, 'experience_public_vise', None)
        experience_institution_porteur_autre = getattr(fields, 'experience_institution_porteur_autre', None)
        experience_institution_partenaire_autre = getattr(fields, 'experience_institution_partenaire_autre', None)
        experience_institution_ressource_autre = getattr(fields, 'experience_institution_ressource_autre', None)
        experience_institution_outil_autre = getattr(fields, 'experience_institution_outil_autre', None)

        clpsDestinationPk = 2
        clpsInfo = self.getClpsByPk(clpsDestinationPk)
        clpsSigle = clpsInfo.clps_sigle
        clpsPrenomContact = clpsInfo.clps_prenom_contact
        clpsEmailContact = clpsInfo.clps_email_contact

        sujet = "[PROJETS PARTAGES :: nouvelle experience]"
        message = u"""<font color='#FF0000'><b>:: Ajout d'une nouvelle expérience pour %s::</b></font><br /><br />
                  Bonjour %s, <br />
                  Une nouvelle expérience est ajoutée dans la base via le site.<br />
                  Il s'agit de :<br />
                  <ul>
                  <li>Titre : <font color='#ff9c1b'><b>%s</b></font></li>
                  <li>Contact : <font color='#ff9c1b'><b>%s</b></font></li>
                  <li>Par : <font color='#ff9c1b'><b>%s</b></font></li>
                  <li>Etat : <font color='#ff9c1b'><b>%s</b></font></li>
                  </ul>
                  <hr />
                  Modifier et publier l'expérience en cliquant sur ce
                  <a href="http://www.projets-partages.be/admin-experience-modifier?experiencePk=%s">lien</a>.
                  <hr />
                  <font size="1">
                  :: Autre public visé : <font color='#ff9c1b'><b>%s</b></font><br />
                  :: Autre institution porteur : <font color='#ff9c1b'><b>%s</b></font><br />
                  :: Autre institution partenaire : <font color='#ff9c1b'><b>%s</b></font><br />
                  :: Autre institution ressource : <font color='#ff9c1b'><b>%s</b></font><br />
                  :: Autre institution outil : <font color='#ff9c1b'><b>%s</b></font><br />
                  </font>
                  """ \
                  %(clpsSigle, \
                    clpsPrenomContact, \
                    experience_titre, \
                    experience_personne_contact, \
                    experience_creation_employe, \
                    experience_etat, \
                    experience_pk, \
                    experience_public_vise, \
                    experience_institution_porteur_autre, \
                    experience_institution_partenaire_autre, \
                    experience_institution_ressource_autre, \
                    experience_institution_outil_autre)
        message = message.encode('utf-8')            
        self.sendMail(sujet, message, clpsEmailContact)

    def sendMailForUpdateExperience(self):
        #envoi d'un mail a Celine lors de la mise a jour d'une experience
        fields = self.context.REQUEST
        experience_pk = getattr(fields, 'experience_pk', None)
        experience_titre = getattr(fields, 'experience_titre', None)
        experience_personne_contact = getattr(fields, 'experience_personne_contact', None)
        experience_creation_employe = getattr(fields, 'experience_creation_employe', None)
        experience_modification_employe = self.getUserAuthenticated()
        experience_auteur_login = getattr(fields, 'experience_auteur_login', None)
        experience_etat = getattr(fields, 'experience_etat', None)
        experience_public_vise = getattr(fields, 'experience_public_vise', None)
        experience_institution_porteur_autre = getattr(fields, 'experience_institution_porteur_autre', None)
        experience_institution_partenaire_autre = getattr(fields, 'experience_institution_partenaire_autre', None)
        experience_institution_ressource_autre = getattr(fields, 'experience_institution_ressource_autre', None)
        #experience_institution_outil_autre = getattr(fields, 'experience_institution_outil_autre', None)

        clpsDestinationPk = 2
        clpsInfo = self.getClpsByPk(clpsDestinationPk)
        clpsSigle = clpsInfo.clps_sigle
        clpsPrenomContact = clpsInfo.clps_prenom_contact
        clpsEmailContact = clpsInfo.clps_email_contact

        sujet = "[PROJETS PARTAGES :: modification de l'experience]"
        message = u"""<font color='#FF0000'><b>:: Modification d'une expérience pour %s::</b></font><br /><br />
                  Bonjour %s, <br />
                  L'expérience <font color='#ff9c1b'><b>%s</b></font> vient d'être modifiée.<br />
                  Il s'agit de :<br />
                  <ul>
                  <li>Num : <font color='#ff9c1b'><b>%s</b></font></li>
                  <li>Titre : <font color='#ff9c1b'><b>%s</b></font></li>
                  <li>Contact : <font color='#ff9c1b'><b>%s</b></font></li>
                  <li>Créé par : <font color='#ff9c1b'><b>%s</b></font></li>
                  <li>Modifié par : <font color='#ff9c1b'><b>%s</b></font></li>
                  <li>Auteur : <font color='#ff9c1b'><b>%s</b></font></li>
                  <li>Etat : <font color='#ff9c1b'><b>%s</b></font></li>
                  </ul>
                  <hr />
                  Modifier et publier l'expérience en cliquant sur ce
                  <a href="http://www.clpsbw.be/admin-experience-modifier?experiencePk=%s">lien</a>.
                  <hr />
                  <font size="1">
                  :: Autre public visé : <font color='#ff9c1b'><b>%s</b></font><br />
                  :: Autre institution porteur : <font color='#ff9c1b'><b>%s</b></font><br />
                  :: Autre institution partenaire : <font color='#ff9c1b'><b>%s</b></font><br />
                  :: Autre institution ressource : <font color='#ff9c1b'><b>%s</b></font><br />
                  :: Autre institution outil : <font color='#ff9c1b'><b>%s</b></font><br />
                  </font>
                  """ \
                  %(clpsSigle, \
                    clpsPrenomContact, \
                    experience_titre, \
                    experience_pk, \
                    experience_titre, \
                    experience_personne_contact, \
                    experience_creation_employe, \
                    experience_modification_employe, \
                    experience_auteur_login, \
                    experience_etat, \
                    experience_pk, \
                    experience_public_vise, \
                    experience_institution_porteur_autre, \
                    experience_institution_partenaire_autre, \
                    experience_institution_ressource_autre)
        message = message.encode('utf-8')
        self.sendMail(sujet, message, clpsEmailContact)


### ROLE USER PLONE ###

    def addLoginAuteur(self, login, passw, role):
        """
        ajoute le login et le pass d'un auteur qui
        s'inscrit via le site
        le role est RecitExperience
        """
        uf = getToolByName(self.context, 'acl_users')
        uf.userFolderAddUser(login, passw, [role], [])

    def addInfoAuteur(self, userId, userEmail, userName):
        """
        ajoute l'email de l'auteur qui vient de s'inscrire
        """
        membership = getToolByName(self.context, 'portal_membership')
        member = membership.getMemberById(userId)
        properties={}
        properties['email']=userEmail
        properties['fullname']=userName
        getToolByName(self, 'plone_utils').setMemberProperties(member, **properties)

    def getUserAuthenticated(self):
        """
        retourne le nom du user loggué
        """
        pm=getToolByName(self, 'portal_membership')
        user=pm.getAuthenticatedMember()
        user = user.getUserName()
        return user

    def getRoleUserAuthenticated(self):
        """
        retourne le nom du user loggué
        """
        pm = getToolByName(self.context, 'portal_membership')
        user=pm.getAuthenticatedMember()
        userRole = user.getRoles()
        return userRole


### CLPS PROPRIO ###
  
    def getAllClps(self):
        """
        table pg clps
        recuperation de toutes les clps
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ClpsTable = wrapper.getMapper('clps')
        query = session.query(ClpsTable)
        query = query.order_by(ClpsTable.clps_nom)
        allClps = query.all()
        return allClps

    def getClpsByPk(self, clpsPk):
        """
        table pg clps
        recuperation des infos d'un clps selon sa pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ClpsTable = wrapper.getMapper('clps')
        query = session.query(ClpsTable)
        query = query.filter(ClpsTable.clps_pk == clpsPk)
        query = query.order_by(ClpsTable.clps_nom)
        clpsInfo = query.one()
        return clpsInfo

    def getClpsProprioForRessource(self, ressourcePk, retour):
        """
        table pg ressource et link_ressource_clps
        recuperation des clpsProprio d'une ressource
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkRessourceClpsTable = wrapper.getMapper('link_ressource_clps_proprio')
        query = session.query(LinkRessourceClpsTable)
        query = query.filter(LinkRessourceClpsTable.ressource_fk == ressourcePk)
        ressources = query.all()

        clpsProprioListe=[]
        allClps = self.getAllClps()
        for ressource in ressources:
            for clps in allClps:
                if ressource.clps_fk == clps.clps_pk:
                    if retour == 'nom':
                        clpsProprioListe.append(clps.clps_nom)
                    if retour == 'pk':
                        clpsProprioListe.append(clps.clps_pk)
        return clpsProprioListe

    def getClpsProprioForInstitution(self, institutionPk, retour):
        """
        table pg institution et link_institution_clps
        recuperation des clpsProprio d'une institution
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkInstitutionClpsProprioTable = wrapper.getMapper('link_institution_clps_proprio')
        query = session.query(LinkInstitutionClpsProprioTable)
        query = query.filter(LinkInstitutionClpsProprioTable.institution_fk == institutionPk)
        institutions = query.all()

        clpsProprioListe=[]
        allClps = self.getAllClps()
        for institution in institutions:
            for clps in allClps:
                if institution.clps_fk == clps.clps_pk:
                    if retour == 'nom':
                        clpsProprioListe.append(clps.clps_nom)
                    if retour == 'pk':
                        clpsProprioListe.append(clps.clps_pk)
        return clpsProprioListe

    def getClpsProprioForExperience(self, experiencePk, retour):
        """
        table pg experience et link_experience_clps
        recuperation des clpsProprio d'une experience
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkExperienceClpsProprioTable = wrapper.getMapper('link_experience_clps_proprio')
        query = session.query(LinkExperienceClpsProprioTable)
        query = query.filter(LinkExperienceClpsProprioTable.experience_fk == experiencePk)
        experiences = query.all()

        clpsProprioListe=[]
        allClps = self.getAllClps()
        for experience in experiences:
            for clps in allClps:
                if experience.clps_fk == clps.clps_pk:
                    if retour == 'nom':
                        clpsProprioListe.append(clps.clps_nom)
                    if retour == 'pk':
                        clpsProprioListe.append(clps.clps_pk)
        return clpsProprioListe

### COMMUNES ###

    def getAllCommune(self, province=None):
        """
        table pg commune
        recuperation de toutes les communes
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        CommuneTable = wrapper.getMapper('commune')
        query = session.query(CommuneTable)
        if province:
            query = query.filter(CommuneTable.com_province_fk.in_(province))
        query = query.order_by(CommuneTable.com_localite_nom)
        allCommunes = query.all()
        return allCommunes


    def getCommunePkInBwByExperiencePk(self, experiencePk):
        """
        table pg link_experience_commune
        recuperation des communes du brabant wallon selon experience_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkExperienceCommuneTable = wrapper.getMapper('link_experience_commune')
        query = session.query(LinkExperienceCommuneTable)
        query = query.filter(LinkExperienceCommuneTable.experience_fk == experiencePk)
        communePk = query.all()

        listeCommunePkForExperience = []
        listeAllCommune = self.getAllCommune((5, ))
        for i in communePk:
            for j in listeAllCommune:
                if i.commune_fk == j.com_pk:
                    listeCommunePkForExperience.append(j.com_pk)
        return listeCommunePkForExperience

    def getCommunePkOutBwByExperiencePk(self, experiencePk):
        """
        table pg link_experience_commune
        recuperation des communes hors barbant wallon selon experience_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkExperienceCommuneTable = wrapper.getMapper('link_experience_commune')
        query = session.query(LinkExperienceCommuneTable)
        query = query.filter(LinkExperienceCommuneTable.experience_fk == experiencePk)
        communePk = query.all()

        listeCommunePkForExperience = []
        listeAllCommune = self.getAllCommune((1, 2, 3, 4, 11))
        for i in communePk:
            for j in listeAllCommune:
                if i.commune_fk == j.com_pk:
                    listeCommunePkForExperience.append(j.com_pk)
        return listeCommunePkForExperience

    def getCommuneNomByExperiencePk(self, experiencePk):
        """
        table pg link_experience_commune
        recuperation des communes selon experience_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkExperienceCommuneTable = wrapper.getMapper('link_experience_commune')
        query = session.query(LinkExperienceCommuneTable)
        query = query.filter(LinkExperienceCommuneTable.experience_fk == experiencePk)
        communePk = query.all()

        listeCommuneNomForExperience = []
        listeAllCommune = self.getAllCommune()
        for i in communePk:
            for j in listeAllCommune:
                if i.commune_fk == j.com_pk:
                    listeCommuneNomForExperience.append(j.com_localite_nom)
        return listeCommuneNomForExperience


#### AUTEUR ####

    def getAllAuteur(self):
        """
        table pg auteur
        recuperation de toutes les auteurs
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        AuteurTable = wrapper.getMapper('auteur')
        query = session.query(AuteurTable)
        query = query.filter(AuteurTable.auteur_clps_fk == 2)
        query = query.order_by(AuteurTable.auteur_nom)
        allAuteur = query.all()
        return allAuteur

    def getAllActiveAuteur(self):
        """
        table pg auteur
        recuperation de toutes les auteurs actif
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        AuteurTable = wrapper.getMapper('auteur')
        query = session.query(AuteurTable)
        query = query.filter(AuteurTable.auteur_actif == True)
        query = query.order_by(AuteurTable.auteur_nom)
        allAuteur = query.all()
        return allAuteur

    def getAllAuteurFromInstitution(self):
        """
        table pg auteur
        recuperation de toutes les auteurs d'institution
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        AuteurTable = wrapper.getMapper('auteur')
        query = session.query(AuteurTable)
        query = query.filter(AuteurTable.auteur_for_institution == True)
        query = query.order_by(AuteurTable.auteur_nom)
        allAuteurFromInstitution = query.all()
        return allAuteurFromInstitution

    def getAuteurByPk(self, auteur_pk):
        """
        table pg auteur
        recuperation d'un auteur selon la pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        AuteurTable = wrapper.getMapper('auteur')
        query = session.query(AuteurTable)
        query = query.filter(AuteurTable.auteur_pk == auteur_pk)
        query = query.order_by(AuteurTable.auteur_nom)
        auteur = query.all()
        return auteur

    def getAuteurLogin(self, auteur_pk):
        """
        table pg auteur
        recuperation d'un auteur selon la pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        AuteurTable = wrapper.getMapper('auteur')
        query = session.query(AuteurTable)
        query = query.filter(AuteurTable.auteur_pk == auteur_pk)
        query = query.order_by(AuteurTable.auteur_nom)
        auteur = query.one()
        auteurLogin = auteur.auteur_login
        return auteurLogin

    def getAuteurByLogin(self, typeElement):
        """
        table pg auteur
        recuperation d'un auteur selon son login
        """
        auteurLogin = self.getUserAuthenticated()
        
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        AuteurTable = wrapper.getMapper('auteur')
        query = session.query(AuteurTable)
        query = query.filter(AuteurTable.auteur_login == auteurLogin)
        query = query.order_by(AuteurTable.auteur_nom)
        auteur = query.one()

        auteurNom = auteur.auteur_nom
        auteurPrenom = auteur.auteur_prenom
        auteurInstitution = auteur.auteur_institution        
        sujet = "[PROJETS PARTAGES :: connection externe par %s]"%(auteurLogin, )
        message="%s %s (%s) de %s en mode creation d'une %s"%(auteurPrenom, auteurNom, auteurLogin, auteurInstitution, typeElement)
        message = message.encode('utf-8')
        self.sendMailWhenLoginByAuteur(sujet, message)

        return auteur

    def getAuteurPkByName(self, auteurConnecte):
        """
        table pg auteur
        recuperation d'un auteur selon son login
        """
        auteur = auteurConnecte.split()
        auteurNom = auteur[0]
        auteurPrenom = auteur[1]
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        AuteurTable = wrapper.getMapper('auteur')
        query = session.query(AuteurTable)
        query = query.filter(AuteurTable.auteur_nom == auteurNom)
        query = query.filter(AuteurTable.auteur_prenom == auteurPrenom)
        auteur = query.one()
        auteurPk = auteur.auteur_pk
        return auteurPk

    def getAuteurTypeByLogin(self):
        """
        table pg auteur
        recuperation du type d'auteur (experience - institution) selon son login
        """
        userLogin = self.getUserAuthenticated()
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        AuteurTable = wrapper.getMapper('auteur')
        query = session.query(AuteurTable)
        query = query.filter(AuteurTable.auteur_login == userLogin)
        auteur = query.one()
        return auteur

    def isAuteurHadExperience(self, auteurPk):
        """
        check si un auteur possede au moins une exeperience
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ExperienceTable = wrapper.getMapper('experience')
        query = session.query(ExperienceTable)
        query = query.filter(ExperienceTable.experience_auteur_fk == auteurPk)
        query = query.all()
        auteurHasExperience = False
        if query:
            auteurHasExperience = True
        else:
            auteurHasExperience = False
        return auteurHasExperience

    def isAuteurHadInstitution(self, auteurPk):
        """
        check si un auteur possede au moins une instituion
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionTable = wrapper.getMapper('institution')
        query = session.query(InstitutionTable)
        query = query.filter(InstitutionTable.institution_auteur_fk == auteurPk)
        query = query.all()
        auteurHasInstitution = False
        if query:
            auteurHasInstitution = True
        else:
            auteurHasInstitution = False
        return auteurHasInstitution

    def deleteAuteurByPk(self, auteurPk):
        """
        table pg auteur
        supprime un auteur selon sa pk
        """
        obj = self.context
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        AuteurTable = wrapper.getMapper('auteur')
        query = session.query(AuteurTable)
        query = query.filter(AuteurTable.auteur_pk == auteurPk)
        for auteur in query.all():
            session.delete(auteur)
        session.flush()
        cible = "%s/admin-auteur-creer" % (obj.portal_url(), )
        obj.REQUEST.RESPONSE.redirect(cible)

    def getAuteurByLeffeSearch(self, searchString):
        """
        table pg auteur
        recuperation d'un auteur via le leffesearch
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        AuteurTable = wrapper.getMapper('auteur')
        query = session.query(AuteurTable)
        query = query.filter(AuteurTable.auteur_nom.ilike("%%%s%%" % searchString))
        auteur = ["%s %s  (%s)" % (aut.auteur_nom, aut.auteur_prenom, aut.auteur_login) for aut in query.all()]
        return auteur


    def addAuteur(self):
        """
        table pg auteur
        ajout d'un auteur
        """
        fields = self.context.REQUEST
        auteur_nom = getattr(fields, 'auteur_nom')
        auteur_prenom = getattr(fields, 'auteur_prenom')
        auteur_email = getattr(fields, 'auteur_email')
        auteur_login = getattr(fields, 'auteur_login')
        auteur_pass = getattr(fields, 'auteur_pass')
        auteur_institution = getattr(fields, 'auteur_institution')
        auteur_id_filemaker = getattr(fields, 'auteur_id_filemaker', None)
        auteur_actif = getattr(fields, 'auteur_actif')

        auteur_for_experience = getattr(fields, 'auteur_for_experience', False)
        auteur_for_institution = getattr(fields, 'auteur_for_institution', False)
        auteur_clps_fk = 2
        auteur_creation_date = self.getTimeStamp()
        auteur_modification_date = self.getTimeStamp()
        auteur_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertAuteur = wrapper.getMapper('auteur')
        newEntry = insertAuteur(auteur_nom = auteur_nom, \
                                auteur_prenom = auteur_prenom, \
                                auteur_email = auteur_email, \
                                auteur_login = auteur_login, \
                                auteur_pass = auteur_pass, \
                                auteur_institution = auteur_institution, \
                                auteur_id_filemaker = auteur_id_filemaker, \
                                auteur_actif = auteur_actif, \
                                auteur_for_experience = auteur_for_experience, \
                                auteur_for_institution = auteur_for_institution, \
                                auteur_clps_fk = auteur_clps_fk, \
                                auteur_creation_date = auteur_creation_date, \
                                auteur_modification_date = auteur_modification_date, \
                                auteur_modification_employe = auteur_modification_employe)
        session.add(newEntry)
        session.flush()
        return {'status': 1}

    def updateAuteur(self):
        """
        mise à jour des infos auteur
        """
        fields = self.context.REQUEST
        auteur_pk = getattr(fields, 'auteur_pk')
        auteur_nom = getattr(fields, 'auteur_nom', None)
        auteur_prenom = getattr(fields, 'auteur_prenom', None)
        auteur_login = getattr(fields, 'auteur_login', None)
        auteur_pass = getattr(fields, 'auteur_pass', None)
        auteur_email = getattr(fields, 'auteur_email', None)
        auteur_institution = getattr(fields, 'auteur_institution', None)
        auteur_id_filemaker = getattr(fields, 'auteur_id_filemaker', None)
        auteur_actif = getattr(fields, 'auteur_actif', None)
        auteur_for_experience = getattr(fields, 'auteur_for_experience', False)
        auteur_for_institution = getattr(fields, 'auteur_for_institution', False)
        auteur_modification_date = self.getTimeStamp()
        auteur_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        updateAuteur = wrapper.getMapper('auteur')
        query = session.query(updateAuteur)
        query = query.filter(updateAuteur.auteur_pk == auteur_pk)
        auteurs = query.all()
        for auteur in auteurs:
            auteur.auteur_nom = unicode(auteur_nom, 'utf-8')
            auteur.auteur_prenom = unicode(auteur_prenom, 'utf-8')
            auteur.auteur_login = unicode(auteur_login, 'utf-8')
            auteur.auteur_pass = unicode(auteur_pass, 'utf-8')
            auteur.auteur_email = unicode(auteur_email, 'utf-8')
            auteur.auteur_institution = unicode(auteur_institution, 'utf-8')
            auteur.auteur_id_filemaker = unicode(auteur_id_filemaker, 'utf-8')
            auteur.auteur_actif = auteur_actif
            auteur.auteur_for_experience = auteur_for_experience
            auteur.auteur_for_institution = auteur_for_institution
            auteur.auteur_modification_date = auteur_modification_date
            auteur.auteur_modification_employe = auteur_modification_employe
        session.flush()


### THEME ###

    def getAllTheme(self):
        """
        table pg theme
        recuperation de toutes les themes
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ThemeTable = wrapper.getMapper('theme')
        query = session.query(ThemeTable)
        query = query.order_by(ThemeTable.theme_nom)
        allThemes = query.all()
        return allThemes

    def getAllActiveTheme(self):
        """
        table pg theme
        recuperation de toutes les themes actif
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ThemeTable = wrapper.getMapper('theme')
        query = session.query(ThemeTable)
        query = query.filter(ThemeTable.theme_actif == True)
        query = query.order_by(ThemeTable.theme_nom)
        allThemes = query.all()
        return allThemes

    def getThemeByPk(self, theme_pk):
        """
        table pg theme
        recuperation d'un theme selon la pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ThemeTable = wrapper.getMapper('theme')
        query = session.query(ThemeTable)
        query = query.filter(ThemeTable.theme_pk.in_(theme_pk))
        query = query.order_by(ThemeTable.theme_nom)
        theme = query.all()
        return theme

    def getThemePkByRessourcePk(self, ressourcePk):
        """
        table pg link_ressource_theme
        recuperation des themes selon ressource_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkRessourceThemeTable = wrapper.getMapper('link_ressource_theme')
        query = session.query(LinkRessourceThemeTable)
        query = query.filter(LinkRessourceThemeTable.ressource_fk == ressourcePk)
        themePk = query.all()

        listeThemeForRessource = []
        listeAllTheme = self.getAllTheme()
        for i in themePk:
            for j in listeAllTheme:
                if i.theme_fk == j.theme_pk:
                    listeThemeForRessource.append(j.theme_pk)
        return listeThemeForRessource

    def getThemeNomByRessourcePk(self, ressourcePk):
        """
        table pg link_ressource_theme
        recuperation des themes selon ressource_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkRessourceThemeTable = wrapper.getMapper('link_ressource_theme')
        query = session.query(LinkRessourceThemeTable)
        query = query.filter(LinkRessourceThemeTable.ressource_fk == ressourcePk)
        themePk = query.all()

        listeThemeForRessource = []
        listeAllTheme = self.getAllTheme()
        for i in themePk:
            for j in listeAllTheme:
                if i.theme_fk == j.theme_pk:
                    listeThemeForRessource.append(j.theme_nom)
        return listeThemeForRessource

    def getThemeForSearchEngine(self):
        """
        table pg link_experience_theme
        recuperation des themes utilisés par des experiences
        """
        #recup ds experience active
        experienceActive = self.getAllExperienceByEtat('publish')
        experiencePk=[]
        for exp in experienceActive:
            experiencePk.append(exp.experience_pk)

        #recup des themes selon les experiences actives
        theme = self.getThemeByExperiencePk(experiencePk)

        #elimination des doublons dans les cle
        themeForExperienceActive=[]
        [themeForExperienceActive.append(item) for item in theme if not item in themeForExperienceActive]

        return themeForExperienceActive

    def getThemeByExperiencePk(self, experiencePk):
        """
        table pg link_experience_theme
        recuperation des theme selon experience_pk
        """
        experiencePk = self.getTuple(experiencePk)

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkExperienceThemeTable = wrapper.getMapper('link_experience_theme')
        query = session.query(LinkExperienceThemeTable)
        query = query.filter(LinkExperienceThemeTable.experience_fk.in_(experiencePk))
        themePk = query.all()

        listeThemeForExperience = []
        listeAllTheme = self.getAllTheme()
        for i in themePk:
            for j in listeAllTheme:
                if i.theme_fk == j.theme_pk:
                    listeThemeForExperience.append(j.theme_pk)
        return listeThemeForExperience

    def addTheme(self):
        """
        table pg theme
        ajout d'un theme
        """
        fields = self.context.REQUEST
        theme_nom = getattr(fields, 'theme_nom')
        theme_actif = getattr(fields, 'theme_actif')
        theme_creation_date = self.getTimeStamp()
        theme_modification_date = self.getTimeStamp()
        theme_creation_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertTheme = wrapper.getMapper('theme')
        newEntry = insertTheme(theme_nom = theme_nom, \
                               theme_actif = theme_actif, \
                               theme_creation_date = theme_creation_date, \
                               theme_modification_date = theme_modification_date, \
                               theme_creation_employe = theme_creation_employe)
        session.save(newEntry)
        session.flush()

    def addThemeKeywordsIfNeededAndGetPks(self, themePksOrValues):
        """
        ajoute les mots clés 'Thème' qui n'existent pas encore dans la DB.
        Explication ci-dessus.
        """
        pks = []
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        themeTable = wrapper.getMapper('theme')
        for value in themePksOrValues:
            try:
                int(value)
            except ValueError:
                newEntry = themeTable(theme_nom = value, \
                                      theme_actif = True, \
                                      theme_creation_date = self.getTimeStamp(), \
                                      theme_modification_date = self.getTimeStamp(), \
                                      theme_modification_employe = self.getUserAuthenticated())
                session.save(newEntry)
                session.flush()
                pks.append(int(newEntry.theme_pk))
            else:
                pks.append(int(value))
        return pks

    def updateTheme(self):
        """
        mise à jour des infos theme
        """
        fields = self.context.REQUEST
        theme_pk = getattr(fields, 'theme_pk')
        theme_nom = getattr(fields, 'theme_nom', None)
        theme_actif = getattr(fields, 'theme_actif', None)
        theme_modification_date = self.getTimeStamp()
        theme_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        updateTheme = wrapper.getMapper('theme')
        query = session.query(updateTheme)
        query = query.filter(updateTheme.theme_pk == theme_pk)
        themes = query.all()
        for theme in themes:
            theme.theme_nom = unicode(theme_nom, 'utf-8')
            theme.theme_actif = theme_actif
            theme.theme_modification_date = theme_modification_date
            theme.theme_modification_employe = theme_modification_employe
        session.flush()


### MOT-CLE ###

    def getAllMotCle(self):
        """
        table pg mot_cle
        recuperation de toutes les motcles
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        MotCleTable = wrapper.getMapper('mot_cle')
        query = session.query(MotCleTable)
        query = query.order_by(MotCleTable.motcle_mot)
        allMotCles = query.all()
        return allMotCles

    def getAllActiveMotCle(self):
        """
        table pg mot_cle
        recuperation de toutes les motcles
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        MotCleTable = wrapper.getMapper('mot_cle')
        query = session.query(MotCleTable)
        query = query.filter(MotCleTable.motcle_actif == True)
        query = query.order_by(MotCleTable.motcle_mot)
        allActiveMotCles = query.all()
        return allActiveMotCles

    def getMotCleByPk(self, motcle_pk):
        """
        table pg mot_cle
        recuperation d'un mot_cle selon la pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        MotCleTable = wrapper.getMapper('mot_cle')
        query = session.query(MotCleTable)
        query = query.filter(MotCleTable.motcle_pk == motcle_pk)
        query = query.order_by(MotCleTable.motcle_mot)
        motCle = query.all()
        return motCle

    def getMotCleByExperiencePk(self, experiencePk):
        """
        table pg link_experience_mot_cle
        recuperation des motcles selon experience_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkExperienceMotCleTable = wrapper.getMapper('link_experience_mot_cle')
        query = session.query(LinkExperienceMotCleTable)
        query = query.filter(LinkExperienceMotCleTable.experience_fk == experiencePk)
        motClePk = query.all()

        listeMotCleForExperience = []
        listeAllMotCle = self.getAllMotCle()
        for i in motClePk:
            for j in listeAllMotCle:
                if i.motcle_fk == j.motcle_pk:
                    listeMotCleForExperience.append(j.motcle_pk)
        return listeMotCleForExperience

    def addMotCle(self):
        """
        table pg mot_cle
        ajout d'un mot cle
        """
        fields = self.context.REQUEST
        motcle_mot = getattr(fields, 'motcle_mot')
        motcle_actif = getattr(fields, 'motcle_actif')
        motcle_creation_date = self.getTimeStamp()
        motcle_modification_date = self.getTimeStamp()
        motcle_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertMotCle = wrapper.getMapper('mot_cle')
        newEntry = insertMotCle(motcle_mot = motcle_mot, \
                                motcle_actif = motcle_actif, \
                                motcle_creation_date = motcle_creation_date, \
                                motcle_modification_date = motcle_modification_date, \
                                motcle_modification_employe = motcle_modification_employe)
        session.save(newEntry)
        session.flush()
        return {'status': 1}

    def updateMotCle(self):
        """
        mise à jour des infos mot_lce
        """
        fields = self.context.REQUEST
        motcle_pk = getattr(fields, 'motcle_pk')
        motcle_mot = getattr(fields, 'motcle_mot', None)
        #motcle_theme_fk = getattr(fields, 'motcle_theme_fk', None)
        motcle_actif = getattr(fields, 'motcle_actif', None)
        motcle_modification_date = self.getTimeStamp()
        motcle_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        updateMotCle = wrapper.getMapper('mot_cle')
        query = session.query(updateMotCle)
        query = query.filter(updateMotCle.motcle_pk == motcle_pk)
        motCles = query.all()
        for motcle in motCles:
            motcle.motcle_mot = unicode(motcle_mot, 'utf-8')
            motcle.motcle_actif = motcle_actif
            motcle.motcle_modification_date = motcle_modification_date
            motcle.motcle_modification_employe = motcle_modification_employe

        session.flush()

    def addPublicKeywordsIfNeededAndGetPks(self, publicPksOrValues):
        """
        ajoute les mots clés 'Public' qui n'existent pas encore dans la DB.
        On pourrait checker dans la DB mais on sait que les nouvelles entrées
        seront de type texte tandis que les anciennes seront des entiers (pk).
        On renvoie la liste des pks à la fin, y compris celles des mots-clés
        venant d'être ajoutés à la DB.
        """
        pks = []
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        publicTable = wrapper.getMapper('public')
        for value in publicPksOrValues:
            try:
                int(value)
            except ValueError:
                newEntry = publicTable(public_nom = value, \
                                       public_actif = True, \
                                       public_creation_date = self.getTimeStamp(), \
                                       public_modification_date = self.getTimeStamp(), \
                                       public_creation_employe = self.getUserAuthenticated())
                session.save(newEntry)
                session.flush()
                pks.append(int(newEntry.public_pk))
            else:
                pks.append(int(value))
        return pks

    def addMotCleFkKeywordsIfNeededAndGetPks(self, motClePksOrValues):
        """
        ajoute les mots clés 'Mots Clés' qui n'existent pas encore dans la DB.
        Explication ci-dessus.
        """
        pks = []
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        motCleTable = wrapper.getMapper('mot_cle')
        for value in motClePksOrValues:
            try:
                int(value)
            except ValueError:
                newEntry = motCleTable(motcle_mot = value, \
                                       motcle_actif = True, \
                                       motcle_creation_date = self.getTimeStamp(), \
                                       motcle_modification_date = self.getTimeStamp(), \
                                       motcle_modification_employe = self.getUserAuthenticated())
                session.save(newEntry)
                session.flush()
                pks.append(int(newEntry.motcle_pk))
            else:
                pks.append(int(value))
        return pks


### PUBLIC ###

    def getAllPublic(self):
        """
        table pg public
        recuperation de toutes les publics
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        PublicTable = wrapper.getMapper('public')
        query = session.query(PublicTable)
        query = query.order_by(PublicTable.public_nom)
        allPublics = query.all()
        return allPublics

    def getAllActivePublic(self):
        """
        table pg public
        recuperation de toutes les publics actif
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        PublicTable = wrapper.getMapper('public')
        query = session.query(PublicTable)
        query = query.filter(PublicTable.public_actif == True)
        query = query.order_by(PublicTable.public_nom)
        allPublics = query.all()
        return allPublics

    def getPublicByPk(self, publicPk):
        """
        table pg public
        recuperation d'un public selon la pk
        """
        publicPk = self.getTuple(publicPk)

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        PublicTable = wrapper.getMapper('public')
        query = session.query(PublicTable)
        query = query.filter(PublicTable.public_pk.in_(publicPk))
        query = query.order_by(PublicTable.public_nom)
        public = query.all()
        return public

    def getPublicByRessourcePk(self, ressourcePk, retour):
        """
        table pg link_ressource_public
        recuperation des publics selon ressource_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkRessourcePublicTable = wrapper.getMapper('link_ressource_public')
        query = session.query(LinkRessourcePublicTable)
        query = query.filter(LinkRessourcePublicTable.ressource_fk == ressourcePk)
        publicPk = query.all()

        listePublicForRessource = []
        listeAllPublic = self.getAllPublic()
        for i in publicPk:
            for j in listeAllPublic:
                if i.public_fk == j.public_pk:
                    if retour=='cle':
                        listePublicForRessource.append(j.public_pk)
                    if retour=='nom':
                        listePublicForRessource.append(j.public_nom)
        return listePublicForRessource

    def getPublicByExperiencePk(self, experiencePk):
        """
        table pg link_experience_public
        recuperation des publics selon experiencePk
        """
        experiencePk = self.getTuple(experiencePk)

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkExperiencePublicTable = wrapper.getMapper('link_experience_public')
        query = session.query(LinkExperiencePublicTable)
        query = query.filter(LinkExperiencePublicTable.experience_fk.in_(experiencePk, ))
        publicPk = query.all()

        listePublicForExperience = []
        listeAllPublic = self.getAllPublic()

        for i in publicPk:
            for j in listeAllPublic:
                if i.public_fk == j.public_pk:
                    listePublicForExperience.append(j.public_pk)
        return listePublicForExperience

    def getPublicByExperiencePkFromAuteur(self, experiencePk):
        """
        table pg link_experience_public
        recuperation des publics selon experiencePk d'un auteur
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkExperiencePublicTable = wrapper.getMapper('link_experience_public')
        query = session.query(LinkExperiencePublicTable)
        query = query.filter(LinkExperiencePublicTable.experience_fk == experiencePk)
        publicPk = query.all()

        listePublicForExperience = []
        listeAllPublic = self.getAllPublic()

        for i in publicPk:
            for j in listeAllPublic:
                if i.public_fk == j.public_pk:
                    listePublicForExperience.append(j.public_pk)
        return listePublicForExperience

    def getPublicForSearchEngine(self):
        """
        table pg link_experience_public
        recuperation des publics utilisés par des experiences dont l'etat est publish
        """
        #recup ds experience active
        experienceActive = self.getAllExperienceByEtat('publish')
        experiencePk=[]
        for exp in experienceActive:
            experiencePk.append(exp.experience_pk)

        #recup des publics selon les experiences actives
        public = self.getPublicByExperiencePk(experiencePk)

        #elimination des doublons dans les cle
        publicForExperienceActive=[]
        [publicForExperienceActive.append(item) for item in public if not item in publicForExperienceActive]

        return publicForExperienceActive

    def addPublic(self):
        """
        table pg public
        ajout d'un public
        """
        fields = self.context.REQUEST
        public_nom = getattr(fields, 'public_nom')
        public_actif = getattr(fields, 'public_actif')
        public_creation_date = self.getTimeStamp()
        public_modification_date = self.getTimeStamp()
        public_creation_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertPublic = wrapper.getMapper('public')
        newEntry = insertPublic(public_nom = public_nom, \
                                public_actif = public_actif, \
                                public_creation_date = public_creation_date, \
                                public_modification_date = public_modification_date, \
                                public_creation_employe = public_creation_employe)
        session.save(newEntry)
        session.flush()

    def updatePublic(self):
        """
        mise à jour des infos public
        """
        fields = self.context.REQUEST
        public_pk = getattr(fields, 'public_pk')
        public_nom = getattr(fields, 'public_nom', None)
        public_actif = getattr(fields, 'public_actif', None)
        public_modification_date = self.getTimeStamp()
        public_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        updatePublic = wrapper.getMapper('public')
        query = session.query(updatePublic)
        query = query.filter(updatePublic.public_pk == public_pk)
        publics = query.all()
        for public in publics:
            public.public_nom = unicode(public_nom, 'utf-8')
            public.public_actif = public_actif
            public.public_modification_date = public_modification_date
            public.public_modification_employe = public_modification_employe
        session.flush()


### PLATE-FORME ###

    def getAllPlateForme(self):
        """
        table pg plateforme
        recuperation de toutes les plateformes
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        PlateFormeTable = wrapper.getMapper('plateforme')
        query = session.query(PlateFormeTable)
        query = query.order_by(PlateFormeTable.plateforme_nom)
        allPlateFormes = query.all()
        return allPlateFormes

    def getAllActivePlateForme(self):
        """
        table pg plateforme
        recuperation de toutes les plateforme actif
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        PlateFormeTable = wrapper.getMapper('plateforme')
        query = session.query(PlateFormeTable)
        query = query.filter(PlateFormeTable.plateforme_actif == True)
        query = query.order_by(PlateFormeTable.plateforme_nom)
        allPlateForme = query.all()
        return allPlateForme

    def getPlateFormeByPk(self, plateforme_pk):
        """
        table pg plateforme
        recuperation d'un plateforme selon la pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        PlateFormeTable = wrapper.getMapper('plateforme')
        query = session.query(PlateFormeTable)
        query = query.filter(PlateFormeTable.plateforme_pk == plateforme_pk)
        query = query.order_by(PlateFormeTable.plateforme_nom)
        public = query.all()
        return public

    def getPlateFormeByRessourcePk(self, ressourcePk):
        """
        table pg link_ressource_plateforme
        recuperation des plateforme selon ressource_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkRessourcePlateFormeTable = wrapper.getMapper('link_ressource_plateforme')
        query = session.query(LinkRessourcePlateFormeTable)
        query = query.filter(LinkRessourcePlateFormeTable.ressource_fk == ressourcePk)
        PlateFormePk = query.all()

        listePlateFormeForRessource = []
        listeAllPlateForme = self.getAllPlateForme()
        for i in PlateFormePk:
            for j in listeAllPlateForme:
                if i.plateforme_fk == j.plateforme_pk:
                    listePlateFormeForRessource.append(j.plateforme_nom)
        return listePlateFormeForRessource

    def addPlateForme(self):
        """
        table pg plateforme
        ajout d'un plateforme
        """
        fields = self.context.REQUEST
        plateforme_nom = getattr(fields, 'plateforme_nom')
        plateforme_actif = getattr(fields, 'plateforme_actif')
        plateforme_creation_date = self.getTimeStamp()
        plateforme_modification_date = self.getTimeStamp()
        plateforme_creation_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertPlateForme = wrapper.getMapper('plateforme')
        newEntry = insertPlateForme(plateforme_nom = plateforme_nom, \
                                    plateforme_actif = plateforme_actif, \
                                    plateforme_creation_date = plateforme_creation_date, \
                                    plateforme_modification_date = plateforme_modification_date, \
                                    plateforme_creation_employe = plateforme_creation_employe)
        session.save(newEntry)
        session.flush()

    def updatePlateForme(self):
        """
        mise à jour des infos plateforme
        """
        fields = self.context.REQUEST
        plateforme_pk = getattr(fields, 'plateforme_pk')
        plateforme_nom = getattr(fields, 'plateforme_nom', None)
        plateforme_actif = getattr(fields, 'plateforme_actif', None)
        plateforme_modification_date = self.getTimeStamp()
        plateforme_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        updatePlateForme = wrapper.getMapper('plateforme')
        query = session.query(updatePlateForme)
        query = query.filter(updatePlateForme.plateforme_pk == plateforme_pk)
        plateformes = query.all()
        for plateforme in plateformes:
            plateforme.plateforme_nom = unicode(plateforme_nom, 'utf-8')
            plateforme.plateforme_actif = plateforme_actif
            plateforme.plateforme_modification_date = plateforme_modification_date
            plateforme.plateforme_modification_employe = plateforme_modification_employe
        session.flush()


### SOUS-PLATE-FORME ###

    def getAllSousPlateForme(self):
        """
        table pg sous_plateforme
        recuperation de toutes les sous plate-formes
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        SousPlateFormeTable = wrapper.getMapper('sousplateforme')
        query = session.query(SousPlateFormeTable)
        query = query.order_by(SousPlateFormeTable.sousplateforme_nom)
        allSousPlateFormes = query.all()
        return allSousPlateFormes

    def getAllActiveSousPlateForme(self):
        """
        table pg sous_plateforme
        recuperation de toutes les sous plate-formes actives
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        SousPlateFormeTable = wrapper.getMapper('sousplateforme')
        query = session.query(SousPlateFormeTable)
        query = query.filter(SousPlateFormeTable.sous_plateforme_actif == True)
        query = query.order_by(SousPlateFormeTable.sousplateforme_nom)
        allActiveSousPlateFormes = query.all()
        return allActiveSousPlateFormes

    def getSousPlateFormeByPk(self, sousplateforme_pk):
        """
        table pg sous_plateforme
        recuperation d'une sous plate-forme selon la pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        SousPlateFormeTable = wrapper.getMapper('sousplateforme')
        query = session.query(SousPlateFormeTable)
        query = query.filter(SousPlateFormeTable.sousplateforme_pk == sousplateforme_pk)
        query = query.order_by(SousPlateFormeTable.sousplateforme_nom)
        sousPlateForme = query.all()
        return sousPlateForme

    def getSousPlateFormeByPlateFormePk(self, plateforme_pk):
        """
        table pg sous_plateforme
        recuperation d'une sous plate-forme selon la pk de la plate-forme
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        SousPlateFormeTable = wrapper.getMapper('sousplateforme')
        query = session.query(SousPlateFormeTable)
        query = query.filter(SousPlateFormeTable.sousplateforme_plateforme_fk == plateforme_pk)
        query = query.order_by(SousPlateFormeTable.sousplateforme_nom)
        sousPlateForme = query.all()
        return sousPlateForme

    def addSousPlateForme(self):
        """
        table pg sousplateforme
        ajout d'un sous plateforme
        """
        fields = self.context.REQUEST
        sousplateforme_nom = getattr(fields, 'sousplateforme_nom')
        sousplateforme_actif = getattr(fields, 'sousplateforme_actif')
        sousplateforme_plateforme_fk = getattr(fields, 'sousplateforme_plateforme_fk')
        sousplateforme_creation_date = self.getTimeStamp()
        sousplateforme_modification_date = self.getTimeStamp()
        sousplateforme_creation_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertSousPlateForme = wrapper.getMapper('sousplateforme')
        newEntry = insertSousPlateForme(sousplateforme_nom = sousplateforme_nom, \
                                        sousplateforme_actif = sousplateforme_actif, \
                                        sousplateforme_plateforme_fk = sousplateforme_plateforme_fk, \
                                        sousplateforme_creation_date = sousplateforme_creation_date, \
                                        sousplateforme_modification_date = sousplateforme_modification_date, \
                                        sousplateforme_creation_employe = sousplateforme_creation_employe)
        session.save(newEntry)
        session.flush()

    def updateSousPlateForme(self):
        """
        mise à jour des infos sousplateforme
        """
        fields = self.context.REQUEST
        sousplateforme_pk = getattr(fields, 'sousplateforme_pk')
        sousplateforme_nom = getattr(fields, 'sousplateforme_nom', None)
        sousplateforme_actif = getattr(fields, 'sousplateforme_actif', None)
        sousplateforme_plateforme_fk = getattr(fields, 'sousplateforme_plateforme_fk', None)
        sousplateforme_modification_date = self.getTimeStamp()
        sousplateforme_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        updateSousPlateForme = wrapper.getMapper('sousplateforme')
        query = session.query(updateSousPlateForme)
        query = query.filter(updateSousPlateForme.sousplateforme_pk == sousplateforme_pk)
        sousplateformes = query.all()
        for sousplateforme in sousplateformes:
            sousplateforme.sousplateforme_nom = unicode(sousplateforme_nom, 'utf-8')
            sousplateforme.sousplateforme_actif = sousplateforme_actif
            sousplateforme.sousplateforme_plateforme_fk = int(sousplateforme_plateforme_fk)
            sousplateforme.sousplateforme_modification_date = sousplateforme_modification_date
            sousplateforme_modification_employe = sousplateforme_modification_employe
        session.flush()


### MILIEU DE VIE ###

    def getAllMilieuDeVie(self):
        """
        table pg milieu de vie
        recuperation de tous les milieudevies
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        MilieuDeVieTable = wrapper.getMapper('milieudevie')
        query = session.query(MilieuDeVieTable)
        query = query.order_by(MilieuDeVieTable.milieudevie_nom)
        allMilieuDeVies = query.all()
        return allMilieuDeVies

    def getAllActiveMilieuDeVie(self):
        """
        table pg milieu de vie
        recuperation de tous les milieux de vie actifs
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        MilieuDeVieTable = wrapper.getMapper('milieudevie')
        query = session.query(MilieuDeVieTable)
        query = query.filter(MilieuDeVieTable.milieudevie_actif == True)
        query = query.order_by(MilieuDeVieTable.milieudevie_nom)
        allMilieuDeVies = query.all()
        return allMilieuDeVies

    def getMilieuDeVieByPk(self, milieuDeViePk):
        """
        table pg milieu de vie
        recuperation d'un vie milieu selon milieudevie_pk
        """
        milieuDeViePk = self.getTuple(milieuDeViePk)
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        MilieuDeVieTable = wrapper.getMapper('milieudevie')
        query = session.query(MilieuDeVieTable)
        query = query.filter(MilieuDeVieTable.milieudevie_pk.in_(milieuDeViePk))
        milieuDeVie = query.all()
        return milieuDeVie

    def getMilieuDeVieByExperiencePk(self, experiencePk, retour):
        """
        table pg link_experience_milieudevie
        recuperation des milieudevies selon experiencePk
        """
        experiencePk = self.getTuple(experiencePk)

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkExperienceMilieuDeVieTable = wrapper.getMapper('link_experience_milieudevie')
        query = session.query(LinkExperienceMilieuDeVieTable)
        query = query.filter(LinkExperienceMilieuDeVieTable.experience_fk.in_(experiencePk))
        milieuDeViePk = query.all()

        listeMilieuDeVieForExperience = []
        listeAllMilieuDeVie = self.getAllMilieuDeVie()
        for i in milieuDeViePk:
            for j in listeAllMilieuDeVie:
                if i.milieudevie_fk == j.milieudevie_pk:
                    if retour=='cle':
                        listeMilieuDeVieForExperience.append(j.milieudevie_pk)
                    if retour=='nom':
                        listeMilieuDeVieForExperience.append(j.milieudevie_nom)
        return listeMilieuDeVieForExperience

    def getMilieuDeVieForSearchEngine(self):
        """
        table pg link_experience_milieudevie
        recuperation des milieudevies utilises par des experiences
        fitre selon les experiences actives
        """
        #recup ds experience active
        experienceActive = self.getAllExperienceByEtat('publish')
        experiencePk=[]
        for exp in experienceActive:
            experiencePk.append(exp.experience_pk)
        #recup des milieu de vie selon les experiences actives
        milieuDeVie = self.getMilieuDeVieByExperiencePk(experiencePk, 'cle')
        #elimination des doublons dans les cle
        milieuDeVieForExperienceActive=[]
        [milieuDeVieForExperienceActive.append(item) for item in milieuDeVie if not item in milieuDeVieForExperienceActive]

        return milieuDeVieForExperienceActive

    def addMilieuDeVie(self):
        """
        table pg milieur de vie
        ajout d'un mlieu de vie
        """
        fields = self.context.REQUEST
        milieudevie_nom = getattr(fields, 'milieudevie_nom')
        milieudevie_actif = getattr(fields, 'milieudevie_actif')
        milieudevie_creation_date = self.getTimeStamp()
        milieudevie_modification_date = self.getTimeStamp()
        milieudevie_creation_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertMilieuDeVie = wrapper.getMapper('milieudevie')
        newEntry = insertMilieuDeVie(milieudevie_nom = milieudevie_nom, \
                                     milieudevie_actif = milieudevie_actif, \
                                     milieudevie_creation_date = milieudevie_creation_date, \
                                     milieudevie_modification_date = milieudevie_modification_date, \
                                     milieudevie_creation_employe = milieudevie_creation_employe)
        session.save(newEntry)
        session.flush()

    def addMilieuDeVieKeywordsIfNeededAndGetPks(self, milieuDeViePksOrValues):
        """
        ajoute les mots clés 'Milieu de Vie' qui n'existent pas encore dans la DB.
        Explication ci-dessus.
        """
        pks = []
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        milieuDeVieTable = wrapper.getMapper('milieudevie')
        for value in milieuDeViePksOrValues:
            try:
                int(value)
            except ValueError:
                newEntry = milieuDeVieTable(milieudevie_nom = value, \
                                            milieudevie_actif = True, \
                                            milieudevie_creation_date = self.getTimeStamp(), \
                                            milieudevie_modification_date = self.getTimeStamp(), \
                                            milieudevie_modification_employe = self.getUserAuthenticated())
                session.save(newEntry)
                session.flush()
                pks.append(int(newEntry.milieudevie_pk))
            else:
                pks.append(int(value))
        return pks

    def updateMilieuDeVie(self):
        """
        mise à jour des infos milieu de vie
        """
        fields = self.context.REQUEST
        milieudevie_pk = getattr(fields, 'milieudevie_pk')
        milieudevie_nom = getattr(fields, 'milieudevie_nom', None)
        milieudevie_actif = getattr(fields, 'milieudevie_actif', None)
        milieudevie_modification_date = self.getTimeStamp()
        milieudevie_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        updateMilieuDeVie = wrapper.getMapper('milieudevie')
        query = session.query(updateMilieuDeVie)
        query = query.filter(updateMilieuDeVie.milieudevie_pk == milieudevie_pk)
        milieudevies = query.all()
        for milieudevie in milieudevies:
            milieudevie.milieudevie_nom = unicode(milieudevie_nom, 'utf-8')
            milieudevie.milieudevie_actif = milieudevie_actif
            milieudevie.milieudevie_modification_date = milieudevie_modification_date
            milieudevie.milieudevie_modification_employe = milieudevie_modification_employe
        session.flush()


### SUPPORT ###

    def getAllSupport(self):
        """
        table pg support
        recuperation de tous les supports
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        SupportTable = wrapper.getMapper('support')
        query = session.query(SupportTable)
        query = query.order_by(SupportTable.support_titre)
        allSupports = query.all()
        return allSupports

    def getAllActiveSupport(self):
        """
        table pg support
        recuperation de tous les supports actifs
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        SupportTable = wrapper.getMapper('support')
        query = session.query(SupportTable)
        query = query.filter(SupportTable.support_actif == True)
        query = query.order_by(SupportTable.support_titre)
        allSupports = query.all()
        return allSupports

    def getSupportByPk(self, supportPk):
        """
        table pg support
        recuperation d'un support selon support_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        SupportTable = wrapper.getMapper('support')
        query = session.query(SupportTable)
        query = query.filter(SupportTable.support_pk == supportPk)
        support = query.all()
        return support

    def getSupportByRessourcePk(self, ressourcePk, retour):
        """
        table pg link_ressource_support
        recuperation des supports selon ressource_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkRessourceSupportTable = wrapper.getMapper('link_ressource_support')
        query = session.query(LinkRessourceSupportTable)
        query = query.filter(LinkRessourceSupportTable.ressource_fk == ressourcePk)
        supportPk = query.all()

        listeSuppportForRessource = []
        listeAllSupport = self.getAllSupport()
        for i in supportPk:
            for j in listeAllSupport:
                if i.support_fk == j.support_pk:
                    if retour=='cle':
                        listeSuppportForRessource.append(j.support_pk)
                    if retour=='titre':
                        listeSuppportForRessource.append(j.support_titre)
        return listeSuppportForRessource

    def addSupport(self):
        """
        table pg support
        ajout d'un support
        """
        fields = self.context.REQUEST
        support_titre = getattr(fields, 'support_titre')
        support_description = getattr(fields, 'support_description')
        support_actif = getattr(fields, 'support_actif')
        support_creation_date = self.getTimeStamp()
        support_modification_date = self.getTimeStamp()
        support_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertSupport = wrapper.getMapper('support')
        newEntry = insertSupport(support_titre = support_titre, \
                                 support_description = support_description, \
                                 support_actif = support_actif, \
                                 support_creation_date = support_creation_date, \
                                 support_modification_date = support_modification_date, \
                                 support_modification_employe = support_modification_employe)
        session.save(newEntry)
        session.flush()
        return {'status': 1}

    def updateSupport(self):
        """
        mise à jour des infos support
        """
        fields = self.context.REQUEST
        support_pk = getattr(fields, 'support_pk')
        support_titre = getattr(fields, 'support_titre', None)
        support_description = getattr(fields, 'support_description', None)
        support_actif = getattr(fields, 'support_actif', None)
        support_modification_date = self.getTimeStamp()
        support_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        updateSupport = wrapper.getMapper('support')
        query = session.query(updateSupport)
        query = query.filter(updateSupport.support_pk == support_pk)
        supports = query.all()
        for support in supports:
            support.support_titre = unicode(support_titre, 'utf-8')
            support.support_description =unicode(support_description, 'utf-8')
            support.support_actif = support_actif
            support_modification_date = support_modification_date
            support_modification_employe = support_modification_employe
        session.flush()


### OUTIL ###

    def addOutil(self):
        """
        table pg outil
        ajout d'un outil
        """
        fields = self.context.REQUEST
        outil_nom = getattr(fields, 'outil_nom')
        outil_description = getattr(fields, 'outil_description')
        outil_fabricant = getattr(fields, 'outil_fabricant')
        outil_tranche_age = getattr(fields, 'outil_tranche_age')
        outil_lien = getattr(fields, 'outil_lien')
        outil_lien_siss = getattr(fields, 'outil_lien_siss')
        outil_autre_info = getattr(fields, 'outil_autre_info')
        outil_disponible_clps = getattr(fields, 'outil_disponible_clps')
        outil_etat = getattr(fields, 'outil_etat')
        outil_creation_date = self.getTimeStamp()
        outil_creation_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertOutil = wrapper.getMapper('outil')
        newEntry = insertOutil(outil_nom = outil_nom, \
                               outil_description = outil_description, \
                               outil_fabricant = outil_fabricant, \
                               outil_tranche_age = outil_tranche_age, \
                               outil_lien = outil_lien, \
                               outil_lien_siss = outil_lien_siss, \
                               outil_autre_info = outil_autre_info, \
                               outil_disponible_clps = outil_disponible_clps,\
                               outil_etat = outil_etat, \
                               outil_creation_date = outil_creation_date, \
                               outil_creation_employe = outil_creation_employe)
        session.save(newEntry)
        session.flush()
        return {'status': 1}


### RECIT ###

    def addRecit(self):
        """
        table pg recit
        ajout d'un recit
        """
        pass


### RESSOURCES ###

    def getAllRessource(self, ressourcePk = None):
        """
        table pg ressource
        recuperation de tous les ressources
        """
        fields = self.request.form
        ressourceTitre = fields.get('titreRessource')
        if not ressourcePk:
            ressourcePk = fields.get('ressource_pk')

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        RessourceTable = wrapper.getMapper('ressource')
        query = session.query(RessourceTable)
        if ressourceTitre:
            query = query.filter(RessourceTable.ressource_titre == ressourceTitre)
        if ressourcePk:
            query = query.filter(RessourceTable.ressource_pk == ressourcePk)
        query = query.order_by(RessourceTable.ressource_titre)
        allRessources = query.all()
        return allRessources

    def getAllActiveRessource(self):
        """
        table pg ressource
        recuperation de tous les ressources actives
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        RessourceTable = wrapper.getMapper('ressource')
        query = session.query(RessourceTable)
        query = query.filter(RessourceTable.ressource_etat == 'publish')
        query = query.order_by(RessourceTable.ressource_titre)
        allActiveRessources = query.all()
        return allActiveRessources

    def getRessourceByPk(self, ressourcePk):
        """
        table pg ressource
        recuperation d'un ressource selon ressource_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        RessourceTable = wrapper.getMapper('ressource')
        query = session.query(RessourceTable)
        query = query.filter(RessourceTable.ressource_pk == ressourcePk)
        ressource = query.all()
        return ressource

    def getRessourceMaxPk(self):
        """
        table pg ressource
        recuperation de la derniere pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        RessourceTable = wrapper.getMapper('ressource')
        query = session.query(RessourceTable)
        ressource = query.all()
        listePk=[]
        for i in ressource:
            listePk.append(i.ressource_pk)
        listePk.sort()
        ressourceMaxPk=listePk[-1]
        #experienceMaxPk = query.max(ExperienceTable.experience_pk)
        return ressourceMaxPk

    def getRessourceEtat(self, ressourcePk):
        """
        table pg ressource
        recuperation de l'état d'une ressource
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        RessourceTable = wrapper.getMapper('ressource')
        query = session.query(RessourceTable)
        query = query.filter(RessourceTable.ressource_pk == ressourcePk)
        ressource = query.one()
        ressourceEtat=''
        if ressource.ressource_etat=='private':
            ressourceEtat='Privé'
        if ressource.ressource_etat=='pending':
            ressourceEtat='En attente'
        if ressource.ressource_etat=='publish':
            ressourceEtat='Publié'
        return ressourceEtat

    def getRessourceByExperiencePk(self, experiencePk):
        """
        table pg getRessourceByExperiencePk
        recuperation des ressources liées à une experience selon ressource_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkExperienceRessourceTable = wrapper.getMapper('link_experience_ressource')
        query = session.query(LinkExperienceRessourceTable)
        query = query.filter(LinkExperienceRessourceTable.experience_fk == experiencePk)
        ressourcePk = query.all()
        listeRessourceForExperience = []
        listeAllRessource = self.getAllRessource()
        for i in ressourcePk:
            for j in listeAllRessource:
                if i.ressource_fk == j.ressource_pk:
                    listeRessourceForExperience.append((j.ressource_pk, j.ressource_titre))
        return listeRessourceForExperience

    def getRessourceTitreByExperiencePk(self, experiencePk):
        """
        table pg getRessourceByExperiencePk
        recuperation des ressources liées à une experience selon ressource_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkExperienceRessourceTable = wrapper.getMapper('link_experience_ressource')
        query = session.query(LinkExperienceRessourceTable)
        query = query.filter(LinkExperienceRessourceTable.experience_fk == experiencePk)
        ressourcePk = query.all()
        listeRessourceForExperience = []
        listeAllRessource = self.getAllRessource()
        for i in ressourcePk:
            for j in listeAllRessource:
                if i.ressource_fk == j.ressource_pk:
                    listeRessourceForExperience.append(j.ressource_pk)
        return listeRessourceForExperience

    def getRessourceOutil(self, experiencePk):
        """
        table pg link_experience_ressource_outil
        recuperation de toutes les outils ressource lies a une experience
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ressourceOutilTable = wrapper.getMapper('link_experience_ressource_outil')
        query = session.query(ressourceOutilTable)
        query = query.filter(ressourceOutilTable.experience_fk == experiencePk)
        ressourceOutil = query.all()
        return ressourceOutil

    def getRessourceOuvrage(self, experiencePk):
        """
        table pg link_experience_ressource_ouvrage
        recuperation de toutes les ouvrages ressource lies a une experience
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ressourceOuvrageTable = wrapper.getMapper('link_experience_ressource_ouvrage')
        query = session.query(ressourceOuvrageTable)
        query = query.filter(ressourceOuvrageTable.experience_fk == experiencePk)
        ressourceOuvrage = query.all()
        return ressourceOuvrage

    def getRessourceByLeffeSearch(self, searchString):
        """
        table pg ressource
        recuperation d'une ressource via le leffesearch
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        RessourceTable = wrapper.getMapper('ressource')
        query = session.query(RessourceTable)
        query = query.filter(RessourceTable.ressource_titre.ilike("%%%s%%" % searchString))
        ressource = [res.ressource_titre for res in query.all()]
        return ressource

    def getClpsDispoByRessourcePk(self, ressourcePk, retour):
        """
        table pg link_ressource_clps_dispo
        recuperation des disponobilité dans les clps selon ressource_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkRessourceClpsDispoTable = wrapper.getMapper('link_ressource_clps_dispo')
        query = session.query(LinkRessourceClpsDispoTable)
        query = query.filter(LinkRessourceClpsDispoTable.ressource_fk == ressourcePk)
        clpsPk = query.all()

        listeClpsDispoForRessource = []
        listeAllClps = self.getAllClps()
        for i in clpsPk:
            for j in listeAllClps:
                if i.clps_fk == j.clps_pk:
                    if retour=='cle':
                        listeClpsDispoForRessource.append(j.clps_pk)
                    if retour=='titre':
                        listeClpsDispoForRessource.append(j.clps_nom)
        return listeClpsDispoForRessource



    def addRessource(self):
        """
        table pg ressource
        ajout d'une ressource
        """
        fields = self.context.REQUEST
        ressource_titre = getattr(fields, 'ressource_titre')
        ressource_description = getattr(fields, 'field.ressource_description', None)
        ressource_auteur = getattr(fields, 'ressource_auteur')
        ressource_collection = getattr(fields, 'ressource_collection')
        ressource_edition = getattr(fields, 'ressource_edition')
        ressource_lieu_edition = getattr(fields, 'ressource_lieu_edition')
        ressource_date_edition = getattr(fields, 'ressource_date_edition')
        ressource_autre_info = getattr(fields, 'ressource_autre_info')
        ressource_lien_pipsa = getattr(fields, 'ressource_lien_pipsa')
        ressource_autre_lien = getattr(fields, 'ressource_autre_lien')
        ressource_objectif = getattr(fields, 'field.ressource_objectif', None)
        ressource_disponible_clps = getattr(fields, 'ressource_disponible_clps', False)
        ressource_disponible_autre = getattr(fields, 'ressource_disponible_autre')
        ressource_utilisation = getattr(fields, 'field.ressource_utilisation', None)
        ressource_avis_clps = getattr(fields, 'field.ressource_avis_clps', None)
        ressource_etat = getattr(fields, 'ressource_etat', 'private')
        ressource_plate_forme_sante_ecole = getattr(fields, 'ressource_plate_forme_sante_ecole', False)
        ressource_plate_forme_assuetude = getattr(fields, 'ressource_plate_forme_assuetude', False)
        ressource_plate_forme_sante_famille = getattr(fields, 'ressource_plate_forme_sante_famille', False)
        ressource_plate_forme_sante_environnement = getattr(fields, 'ressource_plate_forme_sante_environnement', False)
        ressource_mission_centre_documentation = getattr(fields, 'ressource_mission_centre_documentation', False)
        ressource_mission_accompagnement_projet = getattr(fields, 'ressource_mission_accompagnement_projet', False)
        ressource_mission_reseau_echange = getattr(fields, 'ressource_mission_reseau_echange', False)
        ressource_mission_formation = getattr(fields, 'ressource_mission_formation', False)
        ressource_creation_date = self.getTimeStamp()
        ressource_modification_date = self.getTimeStamp()
        ressource_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertRessource = wrapper.getMapper('ressource')
        newEntry = insertRessource(ressource_titre = ressource_titre, \
                                   ressource_description = ressource_description, \
                                   ressource_auteur = ressource_auteur, \
                                   ressource_collection = ressource_collection, \
                                   ressource_edition = ressource_edition, \
                                   ressource_lieu_edition = ressource_lieu_edition, \
                                   ressource_date_edition = ressource_date_edition, \
                                   ressource_autre_info = ressource_autre_info, \
                                   ressource_lien_pipsa = ressource_lien_pipsa, \
                                   ressource_autre_lien = ressource_autre_lien, \
                                   ressource_objectif = ressource_objectif, \
                                   ressource_disponible_clps = ressource_disponible_clps, \
                                   ressource_disponible_autre = ressource_disponible_autre, \
                                   ressource_utilisation = ressource_utilisation, \
                                   ressource_avis_clps = ressource_avis_clps, \
                                   ressource_etat = ressource_etat, \
                                   ressource_plate_forme_sante_ecole = ressource_plate_forme_sante_ecole, \
                                   ressource_plate_forme_assuetude = ressource_plate_forme_assuetude, \
                                   ressource_plate_forme_sante_famille = ressource_plate_forme_sante_famille, \
                                   ressource_plate_forme_sante_environnement = ressource_plate_forme_sante_environnement, \
                                   ressource_mission_centre_documentation = ressource_mission_centre_documentation, \
                                   ressource_mission_accompagnement_projet = ressource_mission_accompagnement_projet, \
                                   ressource_mission_reseau_echange = ressource_mission_reseau_echange, \
                                   ressource_mission_formation = ressource_mission_formation, \
                                   ressource_creation_date = ressource_creation_date, \
                                   ressource_modification_date = ressource_modification_date, \
                                   ressource_modification_employe = ressource_modification_employe)
        session.save(newEntry)
        session.flush()
        return {'status': 1}

    def addLinkRessourceSupport(self, ressourceFk):
        """
        table pg link_ressource_support
        ajout des supports liés à une ressource
        """
        fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkRessourceSupport = wrapper.getMapper('link_ressource_support')
        ressourceSupport = getattr(fields, 'ressource_support_fk', None)
        for supportFk in ressourceSupport:
            newEntry = insertLinkRessourceSupport(ressource_fk = ressourceFk,
                                                  support_fk = supportFk)
            session.save(newEntry)
        session.flush()

    def addLinkRessourceTheme(self, ressourceFk):
        """
        table pg link_ressource_theme
        ajout des thèmes liés à une ressource
        """
        fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkRessourceTheme = wrapper.getMapper('link_ressource_theme')
        ressourceTheme = getattr(fields, 'ressource_theme_fk', None)
        for themeFk in ressourceTheme:
            newEntry = insertLinkRessourceTheme(ressource_fk = ressourceFk,
                                                theme_fk = themeFk)
            session.save(newEntry)
        session.flush()

    def addLinkRessourcePublic(self, ressourceFk):
        """
        table pg link_ressource_public
        ajout des publics liés à une ressource
        """
        fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkRessourcePublic = wrapper.getMapper('link_ressource_public')
        ressourcePublic = getattr(fields, 'ressource_public_fk', None)
        for publicFk in ressourcePublic:
            newEntry = insertLinkRessourcePublic(ressource_fk = ressourceFk,
                                                 public_fk = publicFk)
            session.save(newEntry)
        session.flush()

    def addLinkRessourceClpsDispo(self, ressourceFk):
        """
        table pg link_ressource_clps
        ajout des clps proprietaire de la ressource
        """
        fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkRessourceClpsDispo = wrapper.getMapper('link_ressource_clps_dispo')
        ressourceClps = getattr(fields, 'ressource_clps_dispo_fk', None)
        for clpsFk in ressourceClps:
            newEntry = insertLinkRessourceClpsDispo(ressource_fk = ressourceFk,
                                                    clps_fk = clpsFk)
            session.save(newEntry)
        session.flush()

    def deleteLinkRessourceSupport(self, ressourceFk):
        """
        table pg link_ressource_support
        suppression des supports liés à une ressource
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkRessourceSupport = wrapper.getMapper('link_ressource_support')
        query = session.query(deleteLinkRessourceSupport)
        query = query.filter(deleteLinkRessourceSupport.ressource_fk == ressourceFk)
        for ressourceFk in query.all():
            session.delete(ressourceFk)
        session.flush()

    def deleteLinkRessourceTheme(self, ressourceFk):
        """
        table pg link_ressource_theme
        suppression des themes liés à une ressource
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkRessourceTheme = wrapper.getMapper('link_ressource_theme')
        query = session.query(deleteLinkRessourceTheme)
        query = query.filter(deleteLinkRessourceTheme.ressource_fk == ressourceFk)
        for ressourceFk in query.all():
            session.delete(ressourceFk)
        session.flush()

    def deleteLinkRessourceClpsProprio(self, ressourceFk):
        """
        table pg link_ressource_clps_proprio
        suppression des proprio des ressources
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkRessourceClpsProprio = wrapper.getMapper('link_ressource_clps_proprio')
        query = session.query(deleteLinkRessourceClpsProprio)
        query = query.filter(deleteLinkRessourceClpsProprio.ressource_fk == ressourceFk)
        for ressourceFk in query.all():
            session.delete(ressourceFk)
        session.flush()

    def deleteLinkRessourceClpsDispo(self, ressourceFk):
        """
        table pg link_ressource_clps_dispo
        suppression des dispos des ressources dans les clps
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkRessourceClpsDispo = wrapper.getMapper('link_ressource_clps_dispo')
        query = session.query(deleteLinkRessourceClpsDispo)
        query = query.filter(deleteLinkRessourceClpsDispo.ressource_fk == ressourceFk)
        for ressourceFk in query.all():
            session.delete(ressourceFk)
        session.flush()

    def deleteLinkRessourcePublic(self, ressourceFk):
        """
        table pg link_ressource_public
        suppression des publics liés à une ressource
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkRessourcePublic = wrapper.getMapper('link_ressource_public')
        query = session.query(deleteLinkRessourcePublic)
        query = query.filter(deleteLinkRessourcePublic.ressource_fk == ressourceFk)
        for ressourceFk in query.all():
            session.delete(ressourceFk)
        session.flush()

    def addLinkRessourceClpsProprio(self, ressourceFk):
        """
        table pg link_ressource_clps
        ajout des clps proprietaire de la ressource
        """
        fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkRessourceClpsProprio = wrapper.getMapper('link_ressource_clps_proprio')
        ressourceClps = getattr(fields, 'ressource_clps_proprio_fk', None)
        for clpsFk in ressourceClps:
            newEntry = insertLinkRessourceClpsProprio(ressource_fk = ressourceFk,
                                                      clps_fk = clpsFk)
            session.save(newEntry)
        session.flush()

    def updateRessource(self):
        """
        mise à jour des infos ressources
        """
        fields = self.context.REQUEST
        ressource_pk = getattr(fields, 'ressource_pk')
        ressource_titre = getattr(fields, 'ressource_titre')
        ressource_description = getattr(fields, 'field.ressource_description', None)
        ressource_auteur = getattr(fields, 'ressource_auteur')
        ressource_collection = getattr(fields, 'ressource_collection')
        ressource_edition = getattr(fields, 'ressource_edition')
        ressource_lieu_edition = getattr(fields, 'ressource_lieu_edition')
        ressource_date_edition = getattr(fields, 'ressource_date_edition')
        ressource_autre_info = getattr(fields, 'ressource_autre_info')
        ressource_lien_pipsa = getattr(fields, 'ressource_lien_pipsa')
        ressource_autre_lien = getattr(fields, 'ressource_autre_lien')
        ressource_objectif = getattr(fields, 'field.ressource_objectif', None)
        ressource_disponible_clps = getattr(fields, 'ressource_disponible_clps', None)
        ressource_disponible_autre = getattr(fields, 'ressource_disponible_autre')
        ressource_utilisation = getattr(fields, 'field.ressource_utilisation', None)
        ressource_avis_clps = getattr(fields, 'field.ressource_avis_clps', None)
        ressource_etat = getattr(fields, 'ressource_etat')
        ressource_plate_forme_sante_ecole = getattr(fields, 'ressource_plate_forme_sante_ecole', None)
        ressource_plate_forme_assuetude = getattr(fields, 'ressource_plate_forme_assuetude', None)
        ressource_plate_forme_sante_famille = getattr(fields, 'ressource_plate_forme_sante_famille', None)
        ressource_plate_forme_sante_environnement = getattr(fields, 'ressource_plate_forme_sante_environnement', None)
        ressource_mission_centre_documentation = getattr(fields, 'ressource_mission_centre_documentation', None)
        ressource_mission_accompagnement_projet = getattr(fields, 'ressource_mission_accompagnement_projet', None)
        ressource_mission_reseau_echange = getattr(fields, 'ressource_mission_reseau_echange', None)
        ressource_mission_formation = getattr(fields, 'ressource_mission_formation', None)
        ressource_modification_date = self.getTimeStamp()
        ressource_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        updateRessource = wrapper.getMapper('ressource')
        query = session.query(updateRessource)
        query = query.filter(updateRessource.ressource_pk == ressource_pk)
        ressource = query.one()
        ressource.ressource_titre = unicode(ressource_titre, 'utf-8')
        ressource.ressource_description = unicode(ressource_description, 'utf-8')
        ressource.ressource_auteur = unicode(ressource_auteur, 'utf-8')
        ressource.ressource_collection = unicode(ressource_collection, 'utf-8')
        ressource.ressource_edition = unicode(ressource_edition, 'utf-8')
        ressource.ressource_lieu_edition = unicode(ressource_lieu_edition, 'utf-8')
        ressource.ressource_date_edition = unicode(ressource_date_edition, 'utf-8')
        ressource.ressource_autre_info = unicode(ressource_autre_info, 'utf-8')
        ressource.ressource_lien_pipsa = unicode(ressource_lien_pipsa, 'utf-8')
        ressource.ressource_autre_lien = unicode(ressource_autre_lien, 'utf-8')
        ressource.ressource_objectif = unicode(ressource_objectif, 'utf-8')
        ressource.ressource_disponible_clps = ressource_disponible_clps
        ressource.ressource_disponible_autre = unicode(ressource_disponible_autre, 'utf-8')
        ressource.ressource_utilisation = unicode(ressource_utilisation, 'utf-8')
        ressource.ressource_avis_clps = unicode(ressource_avis_clps, 'utf-8')
        ressource.ressource_etat = unicode(ressource_etat, 'utf-8')
        ressource.ressource_plate_forme_sante_ecole = ressource_plate_forme_sante_ecole
        ressource.ressource_plate_forme_assuetude = ressource_plate_forme_assuetude
        ressource.ressource_plate_forme_sante_famille = ressource_plate_forme_sante_famille
        ressource.ressource_plate_forme_sante_environnement = ressource_plate_forme_sante_environnement
        ressource.ressource_mission_centre_documentation = ressource_mission_centre_documentation
        ressource.ressource_mission_accompagnement_projet = ressource_mission_accompagnement_projet
        ressource.ressource_mission_formation = ressource_mission_formation
        ressource.ressource_mission_reseau_echange = ressource_mission_reseau_echange
        ressource.ressource_modification_date = ressource_modification_date
        ressource.ressource_modification_employe = ressource_modification_employe
        session.flush()


### INSTITUTION TYPE ###

    def getAllInstitutionType(self, institutionTypePk = None):
        """
        table pg institution_type
        recuperation de toutes les types d'institutions
        """
        fields = self.request.form
        institutionTypeNom = fields.get('insitution_type_nom')
        if not institutionTypePk:
            institutionTypePk = fields.get('institution_type__pk')

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionTypeTable = wrapper.getMapper('institution_type')
        query = session.query(InstitutionTypeTable)
        if institutionTypeNom:
            query = query.filter(InstitutionTypeTable.institution_type_nom == institutionTypeNom)
        if institutionTypePk:
            query = query.filter(InstitutionTypeTable.institution_type_pk == institutionTypePk)
        query = query.order_by(InstitutionTypeTable.institution_type_nom)
        allInstitutionType = query.all()
        return allInstitutionType

    def getAllActiveInstitutionType(self):
        """
        table pg institution_type
        recuperation de toutes les types d'institutions
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionTypeTable = wrapper.getMapper('institution_type')
        query = session.query(InstitutionTypeTable)
        query = query.order_by(InstitutionTypeTable.institution_type_nom)
        query = query.filter(InstitutionTypeTable.institution_type_actif == True)
        allActiveInstitutionType = query.all()
        return allActiveInstitutionType

    def getInstitutionTypeByPk(self, institutionTypePk):
        """
        table pg intitution_type
        recuperation d'un type d'institution selon sa pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionTypeTable = wrapper.getMapper('institution_type')
        query = session.query(InstitutionTypeTable)
        query = query.filter(InstitutionTypeTable.institution_type_pk == institutionTypePk)
        institutionType = query.all()
        return institutionType
    
    def addInstitutionType(self):
        """
        table pg institution_type
        ajout d'un type d'institution
        """
        fields = self.context.REQUEST
        institution_type_nom = getattr(fields, 'institution_type_nom')
        institution_type_actif = getattr(fields, 'institution_type_actif')
        institution_type_creation_date = self.getTimeStamp()
        institution_type_modification_date = self.getTimeStamp()
        institution_type_creation_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertInstitutionType = wrapper.getMapper('institution_type')
        newEntry = insertInstitutionType(institution_type_nom = institution_type_nom, \
                                         institution_type_actif = institution_type_actif, \
                                         institution_type_creation_date = institution_type_creation_date, \
                                         institution_type_modification_date = institution_type_modification_date, \
                                         institution_typecreation_employe = institution_type_creation_employe)
        session.save(newEntry)
        session.flush()

    def updateInstitutionType(self):
        """
        table pg assuetude_intervention_for_institution
        mise à jour du type d'une experience
        """
        fields = self.context.REQUEST
        institution_type_pk = getattr(fields, 'institution_type_pk')
        institution_type_nom = getattr(fields, 'institution_type_nom', None)
        institution_type_actif = getattr(fields, 'institution_type_actif', None)
        institution_type_modification_date = self.getTimeStamp()
        institution_type_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        updateInstitutionType = wrapper.getMapper('institution_type')
        query = session.query(updateInstitutionType)
        query = query.filter(updateInstitutionType.institution_type_pk == institution_type_pk)
        institutionTypes = query.all()
        for institutionType in institutionTypes:
            institutionType.institution_type_nom = unicode(institution_type_nom, 'utf-8')
            institutionType.institution_type_actif = institution_type_actif
            institutionType.institution_type_modification_date = institution_type_modification_date
            institutionType.institution_type_modification_employe = institution_type_modification_employe

        session.flush()


### INSTITUION ###

    def getAllInstitution(self, institutionPk = None):
        """
        table pg institution
        recuperation de toutes les institutions
        """
        fields = self.request.form
        institutionNom = fields.get('nomInstitution')
        if not institutionPk:
            institutionPk = fields.get('institution_pk')

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionTable = wrapper.getMapper('institution')
        query = session.query(InstitutionTable)
        if institutionNom:
            query = query.filter(InstitutionTable.institution_nom == institutionNom)
        if institutionPk:
            query = query.filter(InstitutionTable.institution_pk == institutionPk)
        query = query.order_by(InstitutionTable.institution_nom)
        allInstitution = query.all()
        return allInstitution

    def getAllActiveInstitution(self):
        """
        table pg institution
        recuperation de toutes les institutions
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionTable = wrapper.getMapper('institution')
        query = session.query(InstitutionTable)
        query = query.order_by(InstitutionTable.institution_nom)
        query = query.filter(InstitutionTable.institution_etat == 'publish')
        allActiveInstitution = query.all()
        return allActiveInstitution

    def getAllInstitutionByClpsProprio(self, clpsProprioPk):
        """
        table pg institution
        recuperation de toutes les institutions
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        clpsProprioInstitutionTable = wrapper.getMapper('link_institution_clps_proprio')
        query = session.query(clpsProprioInstitutionTable)
        query = query.filter(clpsProprioInstitutionTable.clps_fk == clpsProprioPk)
        institutionPkForClpsProprio = query.all()
        listeInstitutionForClpsProprio = []
        listeAllInstitution = self.getAllActiveInstitution()
        for i in institutionPkForClpsProprio:
            for j in listeAllInstitution:
                if i.institution_fk == j.institution_pk:
                    listeInstitutionForClpsProprio.append(j.institution_pk)
        return listeInstitutionForClpsProprio

    def getAllActiveInstitutionByInstitutionTypePk(self, institutionTypePk, etat=None):
        """
        table pg institution
        recuperation de toutes les institutions selon les institution_type_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionTable = wrapper.getMapper('institution')
        query = session.query(InstitutionTable)
        query = query.order_by(InstitutionTable.institution_nom)
        if etat:
            query = query.filter(InstitutionTable.institution_etat == 'publish')
        query = query.filter(InstitutionTable.institution_listing_ressource_plate_forme_assuetude == True)
        query = query.filter(InstitutionTable.institution_institution_type_fk == institutionTypePk)
        allActiveInstitutionByInstitutionTypePk = query.all()
        return allActiveInstitutionByInstitutionTypePk

    def getInstitutionByPk(self, institutionPk):
        """
        table pg recit
        recuperation d'une instiution selon institution_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionTable = wrapper.getMapper('institution')
        query = session.query(InstitutionTable)
        query = query.filter(InstitutionTable.institution_pk == institutionPk)
        institution = query.all()
        return institution

    def getInstitutionMaxPk(self):
        """
        table pg institution
        recuperation de la derniere pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionTable = wrapper.getMapper('institution')
        query = session.query(InstitutionTable)
        institution = query.all()
        listePk=[]
        for i in institution:
            listePk.append(i.institution_pk)
        listePk.sort()
        institutionMaxPk=listePk[-1]
        #experienceMaxPk = query.max(ExperienceTable.experience_pk)
        return institutionMaxPk

    def getInstitutionByPlateForme(self, plateForme):
        """
        table pg institution
        recuperation d'une institution selon la plateForme
        et selon l'etat publish
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionTable = wrapper.getMapper('institution')
        query = session.query(InstitutionTable)
        query = query.filter(InstitutionTable.institution_etat == 'publish')
        dic = {plateForme: True}
        query = query.filter_by(**dic)
        query = query.limit(5)
        institution = query.all()
        return institution

    def getInstitutionByAuteurLogin(self):
        """
        table pg instituion
        recuperation d'un recit selon le login du user
        """
        loginUser = self.getUserAuthenticated()
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionTable = wrapper.getMapper('institution')
        query = session.query(InstitutionTable)
        query = query.filter(InstitutionTable.institution_auteur_login == loginUser)
        institutionByAuteurLogin = query.all()
        return institutionByAuteurLogin

    def getInstitutionByAuteurPk(self, auteurPk):
        """
        table pg instituion
        recuperation des recits selon la pk de l'auteur
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionTable = wrapper.getMapper('institution')
        query = session.query(InstitutionTable)
        query = query.filter(InstitutionTable.institution_auteur_fk == auteurPk)
        institutionByAuteurPk = query.all()
        return institutionByAuteurPk

    def getInstitutionEtat(self, institutionPk):
        """
        table pg institution
        recuperation de l'état d'une institution
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionTable = wrapper.getMapper('institution')
        query = session.query(InstitutionTable)
        query = query.filter(InstitutionTable.institution_pk == institutionPk)
        institution = query.one()
        institutionEtat=''
        if institution.institution_etat=='private':
            institutionEtat='Privé'
        if institution.institution_etat=='pending':
            institutionEtat='En attente'
        if institution.institution_etat=='publish':
            institutionEtat='Publié'
        return institutionEtat

    def getCountInstitutionByEtat(self, institutionEtat):
        """
        table pg institution
        recuperation du nombre d'institution selon institution_etat
        publish ou private
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionTable = wrapper.getMapper('institution')
        query = session.query(InstitutionTable)
        query = query.filter(InstitutionTable.institution_etat == institutionEtat)
        nbrInst = select([func.count(InstitutionTable.institution_pk).label('count')])
        nbrInst.append_whereclause(InstitutionTable.institution_etat == institutionEtat)
        nbrInstitutionByEtat = nbrInst.execute().fetchone().count
        return nbrInstitutionByEtat

    def getAllInstitutionByEtat(self, institutionEtat):
        """
        table pg institution
        recuperation des institutions selon l'etat
        private publish
        """
        #role = self.getRoleUserAuthenticated()
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionTable = wrapper.getMapper('institution')
        query = session.query(InstitutionTable)
        institution = query.all()
        return institution

    def getCountAllInstitution(self):
        """
        table pg institution
        recuperation du nombre total d'institution
        """
        wrapper = getSAWrapper('clpsbw')
        #session = wrapper.session
        InstitutionTable = wrapper.getMapper('institution')
        #query = session.query(InstitutionTable)
        nbrInst = select([func.count(InstitutionTable.institution_pk).label('count')])
        nbrAllInstitutions = nbrInst.execute().fetchone().count
        return nbrAllInstitutions

    def getInstitutionSousPlateForme(self, institutionPk):
        """
        table pg link_institution_sousplateforme
        recuperation de toutes les sous plate-formes liées à une institution
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        sousPlateFormeInstitutionTable = wrapper.getMapper('link_institution_sousplateforme')
        query = session.query(sousPlateFormeInstitutionTable)
        query = query.filter(sousPlateFormeInstitutionTable.institution_fk == institutionPk)
        sousPlateFormeInstitution = query.all()
        sousPlateFormePkForInstitution = []
        for i in sousPlateFormeInstitution:
            sousPlateFormePkForInstitution.append(i.sousplateforme_fk)
        return sousPlateFormePkForInstitution

    def getInstitutionCommuneCouverte(self, institutionPk):
        """
        table pg link_institution_commune_couverte
        recuperation de toutes les noms des communes couvertes par une institution
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        communeCouverteInstitutionTable = wrapper.getMapper('link_institution_commune_couverte')
        query = session.query(communeCouverteInstitutionTable)
        query = query.filter(communeCouverteInstitutionTable.institution_fk == institutionPk)
        communeCouvertePkByInstitution = query.all()

        listeCommuneCouverteByInstitution = []
        listeAllCommune = self.getAllCommune()
        for i in communeCouvertePkByInstitution:
            for j in listeAllCommune:
                if i.commune_fk == j.com_pk:
                    listeCommuneCouverteByInstitution.append(j.com_localite_nom)
        return listeCommuneCouverteByInstitution

    def getInstitutionCommuneCouvertePkInBw(self, institutionPk):
        """
        table pg link_institution_commune_couverte
        recuperation de toutes les pk descommunes couvertes par une institution
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        communeCouverteInstitutionTable = wrapper.getMapper('link_institution_commune_couverte')
        query = session.query(communeCouverteInstitutionTable)
        query = query.filter(communeCouverteInstitutionTable.institution_fk == institutionPk)
        communeCouvertePkByInstitution = query.all()

        listeCommuneCouverteByInstitution = []
        listeAllCommune = self.getAllCommune((5, ))
        for i in communeCouvertePkByInstitution:
            for j in listeAllCommune:
                if i.commune_fk == j.com_pk:
                    listeCommuneCouverteByInstitution.append(j.com_pk)
        return listeCommuneCouverteByInstitution

    def getInstitutionCommuneCouvertePkOutBw(self, institutionPk):
        """
        table pg link_institution_commune_couverte
        recuperation de toutes les pk descommunes couvertes par une institution
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        communeCouverteInstitutionTable = wrapper.getMapper('link_institution_commune_couverte')
        query = session.query(communeCouverteInstitutionTable)
        query = query.filter(communeCouverteInstitutionTable.institution_fk == institutionPk)
        communeCouvertePkByInstitution = query.all()
        listeCommuneCouverteByInstitution = []
        listeAllCommune = self.getAllCommune((1, 2, 3, 4, 11))
        for i in communeCouvertePkByInstitution:
            for j in listeAllCommune:
                if i.commune_fk == j.com_pk:
                    listeCommuneCouverteByInstitution.append(j.com_pk)
        return listeCommuneCouverteByInstitution

    def getInstitutionCommuneCouvertePkInLux(self, institutionPk):
        """
        table pg link_institution_commune_couverte
        recuperation de toutes les pk descommunes couvertes par une institution
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        communeCouverteInstitutionTable = wrapper.getMapper('link_institution_commune_couverte')
        query = session.query(communeCouverteInstitutionTable)
        query = query.filter(communeCouverteInstitutionTable.institution_fk == institutionPk)
        communeCouvertePkByInstitution = query.all()
        listeCommuneCouverteByInstitution = []
        listeAllCommune = self.getAllCommune((4, ))
        for i in communeCouvertePkByInstitution:
            for j in listeAllCommune:
                if i.commune_fk == j.com_pk:
                    listeCommuneCouverteByInstitution.append(j.com_pk)
        return listeCommuneCouverteByInstitution

    def getInstitutionCommuneCouvertePkOutLux(self, institutionPk):
        """
        table pg link_institution_commune_couverte
        recuperation de toutes les pk descommunes couvertes par une institution
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        communeCouverteInstitutionTable = wrapper.getMapper('link_institution_commune_couverte')
        query = session.query(communeCouverteInstitutionTable)
        query = query.filter(communeCouverteInstitutionTable.institution_fk == institutionPk)
        communeCouvertePkByInstitution = query.all()
        listeCommuneCouverteByInstitution = []
        listeAllCommune = self.getAllCommune((1, 2, 3, 5, 11))
        for i in communeCouvertePkByInstitution:
            for j in listeAllCommune:
                if i.commune_fk == j.com_pk:
                    listeCommuneCouverteByInstitution.append(j.com_pk)
        return listeCommuneCouverteByInstitution

    def isInstitutionTerritoireCouvert(self, institutionPk):
        """
        table pg institution
        teste si une institution couvre un commune, region, communaute, pays
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionTable = wrapper.getMapper('institution')
        query = session.query(InstitutionTable)
        query = query.filter(InstitutionTable.institution_pk == institutionPk)
        institution = query.one()

        communeCouverte=self.getInstitutionCommuneCouverte(institutionPk)
        institutionTerritoireCouvert=False

        if len(communeCouverte) > 0:
            institutionTerritoireCouvert = True

        if institution.institution_zone_internationale:
            institutionTerritoireCouvert = True
        if institution.institution_zone_belgique:
            institutionTerritoireCouvert = True
        if institution.institution_zone_cfwb:
            institutionTerritoireCouvert = True
        if institution.institution_zone_rw:
            institutionTerritoireCouvert = True
        if institution.institution_zone_brxl:
            institutionTerritoireCouvert = True

        return institutionTerritoireCouvert

    def getInstitutionPorteurByExperiencePk(self, experiencePk):
        """
        table pg link_experience_institution_porteur
        recuperation des institutions liées à une experience selon experience_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkInstitutionPorteurTable = wrapper.getMapper('link_experience_institution_porteur')
        query = session.query(LinkInstitutionPorteurTable)
        query = query.filter(LinkInstitutionPorteurTable.experience_fk == experiencePk)
        institutionPk = query.all()

        listeInstitutionPorteurForExperience = []
        listeAllInstitution = self.getAllInstitution()
        for i in institutionPk:
            for j in listeAllInstitution:
                if i.institution_fk == j.institution_pk:
                    listeInstitutionPorteurForExperience.append(j.institution_pk)
        return listeInstitutionPorteurForExperience

    def getInstitutionPartenaireByExperiencePk(self, experiencePk):
        """
        table pg link_experience_institution_partenaire
        recuperation des institutions liées à une experience selon experience_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkInstitutionPartenaireTable = wrapper.getMapper('link_experience_institution_partenaire')
        query = session.query(LinkInstitutionPartenaireTable)
        query = query.filter(LinkInstitutionPartenaireTable.experience_fk == experiencePk)
        institutionPk = query.all()

        listeInstitutionPartenaireForExperience = []
        listeAllInstitution = self.getAllInstitution()
        for i in institutionPk:
            for j in listeAllInstitution:
                if i.institution_fk == j.institution_pk:
                    listeInstitutionPartenaireForExperience.append(j.institution_pk)
        return listeInstitutionPartenaireForExperience

    def getInstitutionRessourceByExperiencePk(self, experiencePk):
        """
        table pg link_experience_institution_ressource
        recuperation des institutions liées à une experience selon experience_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkInstitutionRessourceTable = wrapper.getMapper('link_experience_institution_ressource')
        query = session.query(LinkInstitutionRessourceTable)
        query = query.filter(LinkInstitutionRessourceTable.experience_fk == experiencePk)
        institutionPk = query.all()

        listeInstitutionRessourceForExperience = []
        listeAllInstitution = self.getAllInstitution()
        for i in institutionPk:
            for j in listeAllInstitution:
                if i.institution_fk == j.institution_pk:
                    listeInstitutionRessourceForExperience.append(j.institution_pk)
        return listeInstitutionRessourceForExperience

    def getInstitutionPorteur(self, experiencePk):
        """
        table pg link_experience_institution_porteur
        recuperation de toutes les institutions porteur lies a une experience
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionPorteurTable = wrapper.getMapper('link_experience_institution_porteur')
        query = session.query(InstitutionPorteurTable)
        query = query.filter(InstitutionPorteurTable.experience_fk == experiencePk)
        institutionPorteur = query.all()
        return institutionPorteur

    def getInstitutionPartenaire(self, experiencePk):
        """
        table pg link_experience_institution_partenaire
        recuperation de toutes les institutions partenaire lies a une experience
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionPartenaireTable = wrapper.getMapper('link_experience_institution_partenaire')
        query = session.query(InstitutionPartenaireTable)
        query = query.filter(InstitutionPartenaireTable.experience_fk == experiencePk)
        institutionPartenaire = query.all()
        return institutionPartenaire

    def getInstitutionRessource(self, experiencePk):
        """
        table pg link_experience_institution_ressource
        recuperation de toutes les institutions resssources lies a une experience
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionRessourceTable = wrapper.getMapper('link_experience_institution_ressource')
        query = session.query(InstitutionRessourceTable)
        query = query.filter(InstitutionRessourceTable.experience_fk == experiencePk)
        institutionRessource = query.all()
        return institutionRessource

    def getInstitutionByLeffeSearch(self, searchString):
        """
        table pg institution
        recuperation d'une institution via le litesearch
        voir experiencesearch
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionTable = wrapper.getMapper('institution')
        query = session.query(InstitutionTable)
        query = query.filter(InstitutionTable.institution_nom.ilike("%%%s%%" % searchString))
        institution = [inst.institution_nom for inst in query.all()]
        return institution

    def addInstitution(self):
        """
        table pg institution
        ajout d'une institution
        """
        fields = self.context.REQUEST
        institution_nom = getattr(fields, 'institution_nom')
        institution_sigle = getattr(fields, 'institution_sigle')
        institution_adresse = getattr(fields, 'institution_adresse')
        institution_nom_contact = getattr(fields, 'institution_nom_contact')
        institution_email_contact = getattr(fields, 'institution_email_contact')
        institution_tel_contact = getattr(fields, 'institution_tel_contact')
        institution_fonction_contact = getattr(fields, 'institution_fonction_contact')
        institution_url_site = getattr(fields, 'institution_url_site')
        institution_lien_siss = getattr(fields, 'institution_lien_siss')
        institution_lien_autre = getattr(fields, 'institution_lien_autre')
        institution_autre_info = getattr(fields, 'field.institution_autre_info', None)
        institution_mission = getattr(fields, 'field.institution_mission', None)
        institution_activite = getattr(fields, 'field.institution_activite', None)
        institution_public = getattr(fields, 'field.institution_public', None)
        institution_territoire_tout_luxembourg = getattr(fields, 'institution_territoire_tout_luxembourg', 'False')
        institution_zone_internationale = getattr(fields, 'institution_zone_internationale', 'False')
        institution_zone_internationale_info = getattr(fields, 'institution_zone_internationale_info')
        institution_zone_belgique = getattr(fields, 'institution_zone_belgique', 'False')
        institution_zone_cfwb = getattr(fields, 'institution_zone_cfwb', 'False')
        institution_zone_rw = getattr(fields, 'institution_zone_rw', 'False')
        institution_zone_brxl = getattr(fields, 'institution_zone_brxl', 'False')
        institution_commentaire = getattr(fields, 'field.institution_commentaire', None)
        institution_assuet_intervention = getattr(fields, 'institution_assuet_intervention', None)
        institution_assuet_intervention_precision = getattr(fields, 'field.institution_assuet_intervention_precision', None)
        institution_assuet_activite_proposee = getattr(fields, 'institution_assuet_activite_proposee', None)
        institution_assuet_activite_proposee_precision = getattr(fields, 'field.institution_assuet_activite_proposee_precision', None)
        institution_assuet_thematique_precision = getattr(fields, 'field.institution_assuet_thematique_precision', None)
        institution_assuet_aide_soutien_ecole = getattr(fields, 'field.institution_assuet_aide_soutien_ecole', None)
        institution_plate_forme_sante_ecole = getattr(fields, 'institution_plate_forme_sante_ecole', 'False')
        institution_plate_forme_assuetude = getattr(fields, 'institution_plate_forme_assuetude', 'False')
        institution_plate_forme_sante_famille = getattr(fields, 'institution_plate_forme_sante_famille', 'False')
        institution_plate_forme_sante_environnement = getattr(fields, 'institution_plate_forme_sante_environnement', False)
        institution_listing_ressource_plate_forme_sante_ecole = getattr(fields, 'institution_listing_ressource_plate_forme_sante_ecole', False)
        institution_listing_ressource_plate_forme_assuetude = getattr(fields, 'institution_listing_ressource_plate_forme_assuetude', False)
        institution_listing_ressource_plate_forme_sante_famille = getattr(fields, 'institution_listing_ressource_plate_forme_sante_famille', False)
        institution_listing_ressource_plate_forme_sante_environnement = getattr(fields, 'institution_listing_ressource_plate_forme_sante_environnement', False)
        institution_etat = getattr(fields, 'institution_etat', 'private')
        institution_auteur_login = getattr(fields, 'institution_auteur_login', None)
        institution_creation_date = self.getTimeStamp()
        institution_modification_employe = self.getUserAuthenticated()
        institution_auteur = getattr(fields, 'institutionAuteur', None)
        institution_auteur_fk = getattr(fields, 'institution_auteur_fk', None)
        institution_commune_fk = getattr(fields, 'institution_commune_fk', None)
        institution_clps_proprio_fk = getattr(fields, 'institutionClpsProprio', None)
        institution_institution_type_fk = getattr(fields, 'institution_institution_type_fk', None)

        if not institution_auteur_fk:   #cas ou c'est un auteur exterieur qui se loggue
            auteur = self.getAuteurByLogin('institution')
            institution_auteur_fk= auteur.auteur_pk

        if institution_auteur:    #cas ou c'est un clpsmemeber qui se loggue via le formulaire insitution_creation_form
            institution_auteur_fk = self.getAuteurPkByName(institution_auteur)
            institution_auteur_login = self.getAuteurLogin(institution_auteur_fk)

        if not institution_auteur_fk:   #cas ou c'est un auteur exterieur qui se loggue
            auteur = self.getAuteurByLogin('institution')
            institution_auteur_fk= auteur.auteur_pk

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertInstitution = wrapper.getMapper('institution')
        newEntry = insertInstitution(institution_nom = institution_nom, \
                                     institution_sigle = institution_sigle, \
                                     institution_adresse = institution_adresse, \
                                     institution_nom_contact = institution_nom_contact, \
                                     institution_email_contact = institution_email_contact, \
                                     institution_tel_contact = institution_tel_contact, \
                                     institution_fonction_contact = institution_fonction_contact, \
                                     institution_url_site = institution_url_site, \
                                     institution_lien_siss = institution_lien_siss,\
                                     institution_lien_autre = institution_lien_autre, \
                                     institution_autre_info = institution_autre_info, \
                                     institution_mission = institution_mission, \
                                     institution_activite = institution_activite, \
                                     institution_public = institution_public, \
                                     institution_territoire_tout_luxembourg = institution_territoire_tout_luxembourg, \
                                     institution_zone_internationale = institution_zone_internationale, \
                                     institution_zone_internationale_info = institution_zone_internationale_info, \
                                     institution_zone_belgique = institution_zone_belgique, \
                                     institution_zone_cfwb = institution_zone_cfwb, \
                                     institution_zone_rw = institution_zone_rw, \
                                     institution_zone_brxl = institution_zone_brxl, \
                                     institution_commentaire = institution_commentaire, \
                                     institution_assuet_intervention = institution_assuet_intervention, \
                                     institution_assuet_intervention_precision = institution_assuet_intervention_precision, \
                                     institution_assuet_activite_proposee = institution_assuet_activite_proposee, \
                                     institution_assuet_activite_proposee_precision = institution_assuet_activite_proposee_precision, \
                                     institution_assuet_thematique_precision = institution_assuet_thematique_precision, \
                                     institution_assuet_aide_soutien_ecole = institution_assuet_aide_soutien_ecole, \
                                     institution_auteur_login = institution_auteur_login, \
                                     institution_plate_forme_sante_ecole = institution_plate_forme_sante_ecole, \
                                     institution_plate_forme_assuetude = institution_plate_forme_assuetude, \
                                     institution_plate_forme_sante_famille = institution_plate_forme_sante_famille, \
                                     institution_plate_forme_sante_environnement = institution_plate_forme_sante_environnement, \
                                     institution_listing_ressource_plate_forme_sante_ecole = institution_listing_ressource_plate_forme_sante_ecole, \
                                     institution_listing_ressource_plate_forme_assuetude = institution_listing_ressource_plate_forme_assuetude, \
                                     institution_listing_ressource_plate_forme_sante_famille = institution_listing_ressource_plate_forme_sante_famille, \
                                     institution_listing_ressource_plate_forme_sante_environnement = institution_listing_ressource_plate_forme_sante_environnement, \
                                     institution_etat = institution_etat, \
                                     institution_creation_date = institution_creation_date, \
                                     institution_modification_employe = institution_modification_employe, \
                                     institution_clps_proprio_fk = institution_clps_proprio_fk, \
                                     institution_commune_fk = institution_commune_fk, \
                                     institution_auteur_fk = institution_auteur_fk, \
                                     institution_institution_type_fk = institution_institution_type_fk)
        session.save(newEntry)
        session.flush()
        return {'status': 1}


    def addLinkInstitutionAssuetudeIntervention(self, institutionFk):
        """
        table pg link_institution_assuetude_intervention
        ajout des interventions assuetude liees a une institution
        """
        fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkInstitutionAssuetudeIntervention = wrapper.getMapper('link_institution_assuetude_intervention')
        assuetudeInterventionFk = getattr(fields, 'assuetude_intervention_fk', None)
        for interventionFk in assuetudeInterventionFk:
            newEntry = insertLinkInstitutionAssuetudeIntervention(institution_fk = institutionFk,
                                                                  assuetude_intervention_fk = interventionFk)
            session.save(newEntry)
        session.flush()

    def addLinkInstitutionAssuetudeActiviteProposeePublic(self, institutionFk, assuetudeActiviteProposeePublicFk):
        """
        table pg link_institution_assuetude_activite_proposee_public
        ajout des activites proposees assuetude liees a une institution
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkInstitutionAssuetudeActiviteProposeePublic = wrapper.getMapper('link_institution_assuetude_activite_proposee_public')
        for activiteFk in assuetudeActiviteProposeePublicFk:
            newEntry = insertLinkInstitutionAssuetudeActiviteProposeePublic(institution_fk = institutionFk,
                                                                            assuetude_activite_proposee_public_fk = activiteFk)
            session.save(newEntry)
        session.flush()

    def addLinkInstitutionAssuetudeActiviteProposeePro(self, institutionFk, assuetudeActiviteProposeeProFk):
        """
        table pg link_institution_assuetude_activite_proposee_pro
        ajout des activites proposees assuetude liees a une institution
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkInstitutionAssuetudeActiviteProposeePro = wrapper.getMapper('link_institution_assuetude_activite_proposee_pro')
        for activiteFk in assuetudeActiviteProposeeProFk:
            newEntry = insertLinkInstitutionAssuetudeActiviteProposeePro(institution_fk = institutionFk,
                                                                         assuetude_activite_proposee_pro_fk = activiteFk)
            session.save(newEntry)
        session.flush()


    def addLinkInstitutionAssuetudeThematique(self, institutionFk):
        """
        table pg link_institution_assuetude_thematique
        ajout des thematique assuetude liees a une institution
        """
        fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkInstitutionAssuetudeThematique = wrapper.getMapper('link_institution_assuetude_thematique')
        assuetudeThematiqueFk = getattr(fields, 'assuetude_thematique_fk', None)
        for thematiqueFk in assuetudeThematiqueFk:
            newEntry = insertLinkInstitutionAssuetudeThematique(institution_fk = institutionFk,
                                                                assuetude_thematique_fk = thematiqueFk)
            session.save(newEntry)
        session.flush()

    def addLinkInstitutionSousPlateForme(self, institutionFk):
        """
        table pg link_institution_sousplateforme
        ajout des sous plate-forme de vie liées à une institution
        """
        fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkInstitutionSousPlateForme = wrapper.getMapper('link_institution_sousplateforme')
        institutionSousPlateFormeFk = getattr(fields, 'institution_sousplateforme_fk', None)
        for sousPlateFormeFk in institutionSousPlateFormeFk:
            newEntry = insertLinkInstitutionSousPlateForme(institution_fk = institutionFk,
                                                           sousplateforme_fk = sousPlateFormeFk)
            session.save(newEntry)
        session.flush()

    def addLinkInstitutionCommuneCouverte(self, institutionFk, institutionCommuneCouverteFk):
        """
        table pg link_institution_commune_couverte
        ajout des sous communes couvertes par une institution
        """
        #fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkInstitutionCommuneCouverte = wrapper.getMapper('link_institution_commune_couverte')
        for communeCouverteFk in institutionCommuneCouverteFk:
            newEntry = insertLinkInstitutionCommuneCouverte(institution_fk = institutionFk, commune_fk = communeCouverteFk)
            session.save(newEntry)
        session.flush()

    def addLinkInstitutionClpsProprio(self, institutionFk):
        """
        table pg link_institution_clps_proprio
        ajout des clps proprietaire de l'institution
        """
        fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkInstitutionClpsProprio = wrapper.getMapper('link_institution_clps_proprio')
        institutionClps = getattr(fields, 'institution_clps_proprio_fk', None)
        for clpsFk in institutionClps:
            newEntry = insertLinkInstitutionClpsProprio(institution_fk = institutionFk,
                                                        clps_fk = clpsFk)
            session.save(newEntry)
        session.flush()

    def deleteLinkInstitutionAssuetudeIntervention(self, institutionFk):
        """
        table pg link_institution_assuetude_intervention
        suppression des asuetudes intervention liées à une institution
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkInstitutionAssuetudeIntervention = wrapper.getMapper('link_institution_assuetude_intervention')
        query = session.query(deleteLinkInstitutionAssuetudeIntervention)
        query = query.filter(deleteLinkInstitutionAssuetudeIntervention.institution_fk == institutionFk)
        allInstitutions = query.all()
        for institutionFk in allInstitutions:
            session.delete(institutionFk)
        session.flush()

    def deleteLinkInstitutionAssuetudeActiviteProposeePublic(self, institutionFk):
        """
        table pg link_institution_assuetude_activite_proposee_public
        suppression des asuetudes activite proposee liées à une institution
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkInstitutionAssuetudeActiviteProposeePublic = wrapper.getMapper('link_institution_assuetude_activite_proposee_public')
        query = session.query(deleteLinkInstitutionAssuetudeActiviteProposeePublic)
        query = query.filter(deleteLinkInstitutionAssuetudeActiviteProposeePublic.institution_fk == institutionFk)
        allInstitutions = query.all()

        for institutionFk in allInstitutions:
            session.delete(institutionFk)
        session.flush()

    def deleteLinkInstitutionAssuetudeActiviteProposeePro(self, institutionFk):
        """
        table pg link_institution_assuetude_activite_proposee_pro
        suppression des asuetudes activite proposee liées à une institution
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkInstitutionAssuetudeActiviteProposeePro = wrapper.getMapper('link_institution_assuetude_activite_proposee_pro')
        query = session.query(deleteLinkInstitutionAssuetudeActiviteProposeePro)
        query = query.filter(deleteLinkInstitutionAssuetudeActiviteProposeePro.institution_fk == institutionFk)
        allInstitutions = query.all()

        for institutionFk in allInstitutions:
            session.delete(institutionFk)
        session.flush()

    def deleteLinkInstitutionAssuetudeThematique(self, institutionFk):
        """
        table pg link_institution_assuetude_thematique
        suppression des asuetudes yhematique liées à une institution
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkInstitutionAssuetudeThematique = wrapper.getMapper('link_institution_assuetude_thematique')
        query = session.query(deleteLinkInstitutionAssuetudeThematique)
        query = query.filter(deleteLinkInstitutionAssuetudeThematique.institution_fk == institutionFk)
        allInstitutions = query.all()
        for institutionFk in allInstitutions:
            session.delete(institutionFk)
        session.flush()

    def deleteLinkInstitutionClpsProprio(self, institutionFk):
        """
        table pg link_institution_clps_proprio
        suppression des proprio des institutions
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkInstitutionClpsProprio = wrapper.getMapper('link_institution_clps_proprio')
        query = session.query(deleteLinkInstitutionClpsProprio)
        query = query.filter(deleteLinkInstitutionClpsProprio.institution_fk == institutionFk)
        for institutionFk in query.all():
            session.delete(institutionFk)
        session.flush()

    def deleteLinkInstitutionSousPlateForme(self, institutionFk):
        """
        table pg link_institution_sousplateforme
        suppression des milieu de vie liées à une experience
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteInstitutionSousPlateForme = wrapper.getMapper('link_institution_sousplateforme')
        query = session.query(deleteInstitutionSousPlateForme)
        query = query.filter(deleteInstitutionSousPlateForme.institution_fk == institutionFk)
        for institutionFk in query.all():
            session.delete(institutionFk)
        session.flush()

    def deleteLinkInstitutionCommuneCouverte(self, institutionFk):
        """
        table pg link_institution_commune_couverte
        suppression des communes couvertes par une institution
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteInstitutionCommuneCouverte = wrapper.getMapper('link_institution_commune_couverte')
        query = session.query(deleteInstitutionCommuneCouverte)
        query = query.filter(deleteInstitutionCommuneCouverte.institution_fk == institutionFk)
        for institutionFk in query.all():
            session.delete(institutionFk)
        session.flush()

    def updateInstitution(self):
        """
        table pg institution
        mise a jour d'une institution
        test autre info
        """
        fields = self.context.REQUEST
        institution_pk = getattr(fields, 'institution_pk')
        institution_nom = getattr(fields, 'institution_nom')
        institution_sigle = getattr(fields, 'institution_sigle')
        institution_adresse = getattr(fields, 'institution_adresse')
        institution_nom_contact = getattr(fields, 'institution_nom_contact')
        institution_email_contact = getattr(fields, 'institution_email_contact')
        institution_tel_contact = getattr(fields, 'institution_tel_contact')
        institution_fonction_contact = getattr(fields, 'institution_fonction_contact')
        institution_url_site = getattr(fields, 'institution_url_site')
        institution_lien_siss = getattr(fields, 'institution_lien_siss')
        institution_lien_autre = getattr(fields, 'institution_lien_autre')
        institution_autre_info = getattr(fields, 'field.institution_autre_info', None)
        institution_mission = getattr(fields, 'field.institution_mission', None)
        institution_activite = getattr(fields, 'field.institution_activite', None)
        institution_public = getattr(fields, 'field.institution_public', None)
        institution_territoire_tout_luxembourg = getattr(fields, 'institution_territoire_tout_luxembourg', 'False')
        institution_zone_internationale = getattr(fields, 'institution_zone_internationale', 'False')
        institution_zone_internationale_info = getattr(fields, 'institution_zone_internationale_info')
        institution_zone_belgique = getattr(fields, 'institution_zone_belgique', 'False')
        institution_zone_cfwb = getattr(fields, 'institution_zone_cfwb', 'False')
        institution_zone_rw = getattr(fields, 'institution_zone_rw', 'False')
        institution_zone_brxl = getattr(fields, 'institution_zone_brxl', 'False')
        institution_commentaire = getattr(fields, 'field.institution_commentaire', None)
        institution_assuet_intervention = getattr(fields, 'institution_assuet_intervention', '')
        institution_assuet_intervention_precision = getattr(fields, 'field.institution_assuet_intervention_precision', '')
        institution_assuet_activite_proposee = getattr(fields, 'institution_assuet_activite_proposee', '')
        institution_assuet_activite_proposee_precision = getattr(fields, 'field.institution_assuet_activite_proposee_precision', '')
        institution_assuet_thematique_precision = getattr(fields, 'field.institution_assuet_thematique_precision', '')
        institution_assuet_aide_soutien_ecole = getattr(fields, 'field.institution_assuet_aide_soutien_ecole', '')
        institution_plate_forme_sante_ecole = getattr(fields, 'institution_plate_forme_sante_ecole', 'False')
        institution_plate_forme_assuetude = getattr(fields, 'institution_plate_forme_assuetude', 'False')
        institution_plate_forme_sante_famille = getattr(fields, 'institution_plate_forme_sante_famille', 'False')
        institution_plate_forme_sante_environnement = getattr(fields, 'institution_plate_forme_sante_environnement', 'False')
        institution_listing_ressource_plate_forme_sante_ecole = getattr(fields, 'institution_listing_ressource_plate_forme_sante_ecole', 'False')
        institution_listing_ressource_plate_forme_assuetude = getattr(fields, 'institution_listing_ressource_plate_forme_assuetude', 'False')
        institution_listing_ressource_plate_forme_sante_famille = getattr(fields, 'institution_listing_ressource_plate_forme_sante_famille', 'False')
        institution_listing_ressource_plate_forme_sante_environnement = getattr(fields, 'institution_listing_ressource_plate_forme_sante_environnement', 'False')
        institution_etat = getattr(fields, 'institution_etat', 'private')
        institution_modification_date = self.getTimeStamp()
        institution_modification_employe = self.getUserAuthenticated()
        institution_commune_fk = getattr(fields, 'institution_commune_fk')
        institution_institution_type_fk = getattr(fields, 'institution_institution_type_fk', None)
        institution_auteur_fk = getattr(fields, 'institution_auteur_fk', None)
        institution_auteur_login=self.getAuteurLogin(institution_auteur_fk)
        
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        updateInstitution = wrapper.getMapper('institution')
        query = session.query(updateInstitution)
        query = query.filter(updateInstitution.institution_pk == institution_pk)
        institution = query.one()
        institution.institution_nom = unicode(institution_nom, 'utf-8')
        institution.institution_sigle = unicode(institution_sigle, 'utf-8')
        institution.institution_adresse = unicode(institution_adresse, 'utf-8')
        institution.institution_nom_contact = unicode(institution_nom_contact, 'utf-8')
        institution.institution_email_contact = unicode(institution_email_contact, 'utf-8')
        institution.institution_tel_contact = unicode(institution_tel_contact, 'utf-8')
        institution.institution_fonction_contact = unicode(institution_fonction_contact, 'utf-8')
        institution.institution_url_site = unicode(institution_url_site, 'utf-8')
        institution.institution_lien_siss = unicode(institution_lien_siss, 'utf-8')
        institution.institution_lien_autre = unicode(institution_lien_autre, 'utf-8')
        institution.institution_autre_info = unicode(institution_autre_info, 'utf-8')
        institution.institution_mission = unicode(institution_mission, 'utf-8')
        institution.institution_activite = unicode(institution_activite, 'utf-8')
        institution.institution_public = unicode(institution_public, 'utf-8')
        institution.institution_territoire_tout_luxembourg = institution_territoire_tout_luxembourg
        institution.institution_zone_internationale = institution_zone_internationale
        institution.institution_zone_internationale_info = unicode(institution_zone_internationale_info, 'utf-8')
        institution.institution_zone_belgique = institution_zone_belgique
        institution.institution_zone_cfwb = institution_zone_cfwb
        institution.institution_zone_rw = institution_zone_rw
        institution.institution_zone_brxl = institution_zone_brxl
        institution.institution_commentaire = unicode(institution_commentaire, 'utf-8')
        institution.institution_assuet_intervention = unicode(institution_assuet_intervention, 'utf-8')
        institution.institution_assuet_intervention_precision = unicode(institution_assuet_intervention_precision, 'utf-8')
        institution.institution_assuet_activite_proposee = unicode(institution_assuet_activite_proposee, 'utf-8')
        institution.institution_assuet_activite_proposee_precision = unicode(institution_assuet_activite_proposee_precision, 'utf-8')
        institution.institution_assuet_thematique_precision = unicode(institution_assuet_thematique_precision, 'utf-8')
        institution.institution_assuet_aide_soutien_ecole = unicode(institution_assuet_aide_soutien_ecole, 'utf-8')
        institution.institution_plate_forme_sante_ecole = institution_plate_forme_sante_ecole
        institution.institution_plate_forme_assuetude = institution_plate_forme_assuetude
        institution.institution_plate_forme_sante_famille = institution_plate_forme_sante_famille
        institution.institution_plate_forme_sante_environnement = institution_plate_forme_sante_environnement
        institution.institution_listing_ressource_plate_forme_sante_ecole = institution_listing_ressource_plate_forme_sante_ecole
        institution.institution_listing_ressource_plate_forme_assuetude = institution_listing_ressource_plate_forme_assuetude
        institution.institution_listing_ressource_plate_forme_sante_famille = institution_listing_ressource_plate_forme_sante_famille
        institution.institution_listing_ressource_plate_forme_sante_environnement = institution_listing_ressource_plate_forme_sante_environnement
        institution.institution_etat = institution_etat
        institution.institution_modification_date = institution_modification_date
        institution.institution_modification_employe = institution_modification_employe
        institution.institution_commune_fk = institution_commune_fk
        institution.institution_institution_type_fk = institution_institution_type_fk
        institution.institution_auteur_fk = institution_auteur_fk
        institution.institution_auteur_login = institution_auteur_login
        session.flush()
        return {'status': 1}


### ASSUETUDE FOR INSTITUION ###

    def getAllInstitutionAssuetudeIntervention(self):
        """
        table pg assuetude_intervention_for_institution
        recuperation de toutes les assuetudes intervention
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionAssuetudeInterventionTable = wrapper.getMapper('assuetude_intervention_for_institution')
        query = session.query(InstitutionAssuetudeInterventionTable)
        query = query.order_by(InstitutionAssuetudeInterventionTable.assuetude_intervention_num_ordre)
        allInstitutionAssuetudeIntervention = query.all()
        return allInstitutionAssuetudeIntervention

    def getAllInstitutionAssuetudeActiviteProposee(self, cible=None):
        """
        table pg assuetude_activite_proposee_for_institution
        recuperation de toutes les assuetudes activite proposee
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionAssuetudeActiviteProposeeTable = wrapper.getMapper('assuetude_activite_proposee_for_institution')
        query = session.query(InstitutionAssuetudeActiviteProposeeTable)
        if cible:
            if cible=='public':
                query = query.filter(InstitutionAssuetudeActiviteProposeeTable.assuetude_activite_proposee_public == True)
            if cible=='pro':
                query = query.filter(InstitutionAssuetudeActiviteProposeeTable.assuetude_activite_proposee_pro == True)
        query = query.order_by(InstitutionAssuetudeActiviteProposeeTable.assuetude_activite_proposee_num_ordre)
        allInstitutionAssuetudeActiviteProposee = query.all()
        return allInstitutionAssuetudeActiviteProposee

    def getAllInstitutionAssuetudeThematique(self):
        """
        table pg link_institution_assuetude_thematique
        recuperation de toutes les assuetudes theme
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionAssuetudeThematiqueTable = wrapper.getMapper('assuetude_thematique_for_institution')
        query = session.query(InstitutionAssuetudeThematiqueTable)
        query = query.order_by(InstitutionAssuetudeThematiqueTable.assuetude_thematique_num_ordre)
        allInstitutionAssuetudeThematique = query.all()
        return allInstitutionAssuetudeThematique

    def getInstitutionAssuetudeInterventionByPk(self, assuetudePk):
        """
        table pg assuetude_intervention_for_institution
        recuperation d'une assuetudes intervention selon sa pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionAssuetudeInterventionTable = wrapper.getMapper('assuetude_intervention_for_institution')
        query = session.query(InstitutionAssuetudeInterventionTable)
        query = query.filter(InstitutionAssuetudeInterventionTable.assuetude_intervention_pk == assuetudePk)
        institutionAssuetudeIntervention = query.one()
        return institutionAssuetudeIntervention

    def getInstitutionAssuetudeActiviteProposeeByPk(self, assuetudePk):
        """
        table pg assuetude_activite_proposee_for_institution
        recuperation d'une assuetude activite proposee selon sa pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionAssuetudeActiviteProposeeTable = wrapper.getMapper('assuetude_activite_proposee_for_institution')
        query = session.query(InstitutionAssuetudeActiviteProposeeTable)
        query = query.filter(InstitutionAssuetudeActiviteProposeeTable.assuetude_activite_proposee_pk == assuetudePk)
        institutionAssuetudeActiviteProposee = query.one()
        return institutionAssuetudeActiviteProposee

    def getInstitutionAssuetudeThematiqueByPk(self, assuetudePk):
        """
        table pg assuetude_thematique_for_institution
        recuperation d'une assuetude thematique selon sa PK
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InstitutionAssuetudeThematiqueTable = wrapper.getMapper('assuetude_thematique_for_institution')
        query = session.query(InstitutionAssuetudeThematiqueTable)
        query = query.filter(InstitutionAssuetudeThematiqueTable.assuetude_thematique_pk == assuetudePk)
        institutionAssuetudeThematique = query.one()
        return institutionAssuetudeThematique

    def getAssuetudeInterventionForInstituion(self, institutionPk, retour):
        """
        table pg intitution et link_institution_assuetude_intervention
        recuperation d'un type d'intervention selon sa pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        InterventionTable = wrapper.getMapper('link_institution_assuetude_intervention')
        query = session.query(InterventionTable)
        query = query.filter(InterventionTable.institution_fk == institutionPk)
        interventions = query.all()

        interventionListe=[]
        assuetudeInterventions = self.getAllInstitutionAssuetudeIntervention()
        for ass in assuetudeInterventions:
            for inte in interventions:
                if inte.assuetude_intervention_fk == ass.assuetude_intervention_pk:
                    if retour == 'nom':
                        interventionListe.append(ass.assuetude_intervention_nom)
                    if retour == 'pk':
                        interventionListe.append(ass.assuetude_intervention_pk)
        return interventionListe

    def getAssuetudeActiviteProposeePublicForInstituion(self, institutionPk, retour):
        """
        table pg intitution et link_institution_assuetude_activite_proposee_public
        recuperation d'un type d'institution selon sa pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ActiviteProposeePublicTable = wrapper.getMapper('link_institution_assuetude_activite_proposee_public')
        query = session.query(ActiviteProposeePublicTable)
        query = query.filter(ActiviteProposeePublicTable.institution_fk == institutionPk)
        activites = query.all()

        activitePublicListe=[]
        assuetudeActivitesProposees = self.getAllInstitutionAssuetudeActiviteProposee()
        for ass in assuetudeActivitesProposees:
            for act in activites:
                if act.assuetude_activite_proposee_public_fk == ass.assuetude_activite_proposee_pk:
                    if retour == 'nom':
                        activitePublicListe.append(ass.assuetude_activite_proposee_nom)
                    if retour == 'pk':
                        activitePublicListe.append(ass.assuetude_activite_proposee_pk)
        return activitePublicListe

    def getAssuetudeActiviteProposeeProForInstituion(self, institutionPk, retour):
        """
        table pg intitution et link_institution_assuetude_activite_proposee_pro
        recuperation d'un type d'institution selon sa pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ActiviteProposeeProTable = wrapper.getMapper('link_institution_assuetude_activite_proposee_pro')
        query = session.query(ActiviteProposeeProTable)
        query = query.filter(ActiviteProposeeProTable.institution_fk == institutionPk)
        activites = query.all()

        activiteProListe=[]
        assuetudeActivitesProposees = self.getAllInstitutionAssuetudeActiviteProposee()
        for ass in assuetudeActivitesProposees:
            for act in activites:
                if act.assuetude_activite_proposee_pro_fk == ass.assuetude_activite_proposee_pk:
                    if retour == 'nom':
                        activiteProListe.append(ass.assuetude_activite_proposee_nom)
                    if retour == 'pk':
                        activiteProListe.append(ass.assuetude_activite_proposee_pk)
        return activiteProListe

    def getAssuetudeThematiqueForInstituion(self, institutionPk, retour):
        """
        table pg intitution et public.link_institution_assuetude_thematique
        recuperation d'un type d'institution selon sa pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ThematiqueTable = wrapper.getMapper('public.link_institution_assuetude_thematique')
        query = session.query(ThematiqueTable)
        query = query.filter(ThematiqueTable.institution_fk == institutionPk)
        thematiques = query.all()

        thematiqueListe=[]
        assuetudeThematiques = self.getAllInstitutionAssuetudeThematique()
        for ass in assuetudeThematiques:
            for act in thematiques:
                if act.assuetude_thematique_fk == ass.assuetude_thematique_pk:
                    if retour == 'nom':
                        thematiqueListe.append(ass.assuetude_thematique_nom)
                    if retour == 'pk':
                        thematiqueListe.append(ass.assuetude_thematique_pk)
        return thematiqueListe

    def addAssuetudeInterventionForInstitution(self):
        """
        table pg assuetude_intervention_for_institution
        ajout d'un item assuetude de type intervention pour une institution
        """
        fields = self.context.REQUEST
        assuetude_intervention_nom = getattr(fields, 'assuetude_intervention_nom')
        assuetude_intervention_actif = getattr(fields, 'assuetude_intervention_actif')
        assuetude_intervention_num_ordre = getattr(fields, 'assuetude_intervention_num_ordre')
        assuetude_intervention_creation_date = self.getTimeStamp()
        assuetude_intervention_modification_date = self.getTimeStamp()
        assuetude_intervention_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertAssuetudeIntervention = wrapper.getMapper('assuetude_intervention_for_institution')
        newEntry = insertAssuetudeIntervention(assuetude_intervention_nom = assuetude_intervention_nom, \
                                               assuetude_intervention_actif = assuetude_intervention_actif, \
                                               assuetude_intervention_num_ordre = assuetude_intervention_num_ordre, \
                                               assuetude_intervention_creation_date = assuetude_intervention_creation_date, \
                                               assuetude_intervention_modification_date = assuetude_intervention_modification_date, \
                                               assuetude_intervention_modification_employe = assuetude_intervention_modification_employe)
        session.save(newEntry)
        session.flush()
        cible = "%s/assuetude-for-institution-gerer" % (self.context.portal_url(), )
        self.context.REQUEST.RESPONSE.redirect(cible)

    def updateAssuetudeInterventionForInstitution(self):
        """
        table pg assuetude_intervention_for_institution
        mise a jour d'une assuetude de type intervention pour une institution
        """
        fields = self.context.REQUEST
        assuetude_intervention_pk = getattr(fields, 'assuetude_intervention_pk')
        assuetude_intervention_nom = getattr(fields, 'assuetude_intervention_nom', None)
        assuetude_intervention_actif = getattr(fields, 'assuetude_intervention_actif', None)
        assuetude_intervention_num_ordre = getattr(fields, 'assuetude_intervention_num_ordre', 0)
        assuetude_intervention_modification_date = self.getTimeStamp()
        assuetude_intervention_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        updateAssuetudeInterventionTable = wrapper.getMapper('assuetude_intervention_for_institution')
        query = session.query(updateAssuetudeInterventionTable)
        query = query.filter(updateAssuetudeInterventionTable.assuetude_intervention_pk == assuetude_intervention_pk)
        assuetudeInterventions = query.all()
        for assuetudeIntervention in assuetudeInterventions:
            assuetudeIntervention.assuetude_intervention_nom = unicode(assuetude_intervention_nom, 'utf-8')
            assuetudeIntervention.assuetude_intervention_actif = assuetude_intervention_actif
            assuetudeIntervention.assuetude_intervention_num_ordre = assuetude_intervention_num_ordre
            assuetudeIntervention.assuetude_intervention_modification_date = assuetude_intervention_modification_date
            assuetudeIntervention.assuetude_intervention_modification_employe = assuetude_intervention_modification_employe

        session.flush()
        cible = "%s/assuetude-for-institution-gerer" % (self.context.portal_url(), )
        self.context.REQUEST.RESPONSE.redirect(cible)

    def addAssuetudeActiviteProposeeForInstitution(self):
        """
        table pg assuetude_activite_proposee_for_institution
        ajout d'un item assuetude de type activite proposee pour une institution
        """
        fields = self.context.REQUEST
        assuetude_activite_proposee_nom = getattr(fields, 'assuetude_activite_proposee_nom')
        assuetude_activite_proposee_actif = getattr(fields, 'assuetude_activite_proposee_actif')
        assuetude_activite_proposee_num_ordre = getattr(fields, 'assuetude_activite_proposee_num_ordre')
        assuetude_activite_proposee_public = getattr(fields, 'assuetude_activite_proposee_public', False)
        assuetude_activite_proposee_pro = getattr(fields, 'assuetude_activite_proposee_pro', False)
        assuetude_activite_proposee_creation_date = self.getTimeStamp()
        assuetude_activite_proposee_modification_date = self.getTimeStamp()
        assuetude_activite_proposee_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertAssuetudeActiviteProposee = wrapper.getMapper('assuetude_activite_proposee_for_institution')
        newEntry = insertAssuetudeActiviteProposee(assuetude_activite_proposee_nom = assuetude_activite_proposee_nom, \
                                                   assuetude_activite_proposee_actif = assuetude_activite_proposee_actif, \
                                                   assuetude_activite_proposee_num_ordre = assuetude_activite_proposee_num_ordre,\
                                                   assuetude_activite_proposee_public = assuetude_activite_proposee_public, \
                                                   assuetude_activite_proposee_pro = assuetude_activite_proposee_pro, \
                                                   assuetude_activite_proposee_creation_date = assuetude_activite_proposee_creation_date, \
                                                   assuetude_activite_proposee_modification_date = assuetude_activite_proposee_modification_date, \
                                                   assuetude_activite_proposee_modification_employe = assuetude_activite_proposee_modification_employe)
        session.save(newEntry)
        session.flush()
        cible = "%s/assuetude-for-institution-gerer" % (self.context.portal_url(), )
        self.context.REQUEST.RESPONSE.redirect(cible)

    def updateAssuetudeActiviteProposeeForInstitution(self):
        """
        table pg assuetude_activite_proposee_for_institution
        mise a jour d'une assuetude de type activite proposee pour une institution
        """
        fields = self.context.REQUEST
        assuetude_activite_proposee_pk = getattr(fields, 'assuetude_activite_proposee_pk')
        assuetude_activite_proposee_nom = getattr(fields, 'assuetude_activite_proposee_nom', None)
        assuetude_activite_proposee_actif = getattr(fields, 'assuetude_activite_proposee_actif', None)
        assuetude_activite_proposee_num_ordre = getattr(fields, 'assuetude_activite_proposee_num_ordre', None)
        assuetude_activite_proposee_public = getattr(fields, 'assuetude_activite_proposee_public', False)
        assuetude_activite_proposee_pro = getattr(fields, 'assuetude_activite_proposee_pro', False)
        assuetude_activite_proposee_modification_date = self.getTimeStamp()
        assuetude_activite_proposee_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        updateAssuetudeActiviteProposeeTable = wrapper.getMapper('assuetude_activite_proposee_for_institution')
        query = session.query(updateAssuetudeActiviteProposeeTable)
        query = query.filter(updateAssuetudeActiviteProposeeTable.assuetude_activite_proposee_pk == assuetude_activite_proposee_pk)
        assuetudeActivites = query.all()
        for assuetudeActivite in assuetudeActivites:
            assuetudeActivite.assuetude_activite_proposee_nom = unicode(assuetude_activite_proposee_nom, 'utf-8')
            assuetudeActivite.assuetude_activite_proposee_actif = assuetude_activite_proposee_actif
            assuetudeActivite.assuetude_activite_proposee_num_ordre = assuetude_activite_proposee_num_ordre
            assuetudeActivite.assuetude_activite_proposee_public = assuetude_activite_proposee_public
            assuetudeActivite.assuetude_activite_proposee_pro = assuetude_activite_proposee_pro
            assuetudeActivite.assuetude_activite_proposee_modification_date = assuetude_activite_proposee_modification_date
            assuetudeActivite.assuetude_activite_proposee_modification_employe = assuetude_activite_proposee_modification_employe

        session.flush()
        cible = "%s/assuetude-for-institution-gerer" % (self.context.portal_url(), )
        self.context.REQUEST.RESPONSE.redirect(cible)

    def addAssuetudeThematiqueForInstitution(self):
        """
        table pg public.assuetude_thematique_for_institution
        ajout d'un item assuetude de type thematique pour une institution
        """
        fields = self.context.REQUEST
        assuetude_thematique_nom = getattr(fields, 'assuetude_thematique_nom')
        assuetude_thematique_actif = getattr(fields, 'assuetude_thematique_actif')
        assuetude_thematique_num_ordre = getattr(fields, 'assuetude_thematique_num_ordre')
        assuetude_thematique_creation_date = self.getTimeStamp()
        assuetude_thematique_modification_date = self.getTimeStamp()
        assuetude_thematique_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertAssuetudeIntervention = wrapper.getMapper('assuetude_thematique_for_institution')
        newEntry = insertAssuetudeIntervention(assuetude_thematique_nom = assuetude_thematique_nom, \
                                               assuetude_thematique_actif = assuetude_thematique_actif, \
                                               assuetude_thematique_num_ordre = assuetude_thematique_num_ordre,\
                                               assuetude_thematique_creation_date = assuetude_thematique_creation_date, \
                                               assuetude_thematique_modification_date = assuetude_thematique_modification_date, \
                                               assuetude_thematique_modification_employe = assuetude_thematique_modification_employe)
        session.save(newEntry)
        session.flush()
        cible = "%s/assuetude-for-institution-gerer" % (self.context.portal_url(), )
        self.context.REQUEST.RESPONSE.redirect(cible)

    def updateAssuetudeThematiqueForInstitution(self):
        """
        table pg assuetude_thematique_for_institution
        mise a jour d'une assuetude de type thematique pour une institution
        """
        fields = self.context.REQUEST
        assuetude_thematique_pk = getattr(fields, 'assuetude_thematique_pk')
        assuetude_thematique_nom = getattr(fields, 'assuetude_thematique_nom', None)
        assuetude_thematique_actif = getattr(fields, 'assuetude_thematique_actif', None)
        assuetude_thematique_num_ordre = getattr(fields, 'assuetude_thematique_num_ordre', 0)
        assuetude_thematique_modification_date = self.getTimeStamp()
        assuetude_thematique_modification_employe = self.getUserAuthenticated()

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        updateAssuetudeActiviteProposeeTable = wrapper.getMapper('assuetude_thematique_for_institution')
        query = session.query(updateAssuetudeActiviteProposeeTable)
        query = query.filter(updateAssuetudeActiviteProposeeTable.assuetude_thematique_pk == assuetude_thematique_pk)
        assuetudeThematiques = query.all()
        for assuetudeThematique in assuetudeThematiques:
            assuetudeThematique.assuetude_thematique_nom = unicode(assuetude_thematique_nom, 'utf-8')
            assuetudeThematique.assuetude_thematique_actif = assuetude_thematique_actif
            assuetudeThematique.assuetude_thematique_num_ordre = assuetude_thematique_num_ordre
            assuetudeThematique.assuetude_thematique_modification_date = assuetude_thematique_modification_date
            assuetudeThematique.assuetude_thematique_modification_employe = assuetude_thematique_modification_employe

        session.flush()
        cible = "%s/assuetude-for-institution-gerer" % (self.context.portal_url(), )
        self.context.REQUEST.RESPONSE.redirect(cible)


### EXPERIENCES ###

    def getAllExperience(self):
        """
        table pg recit
        recuperation de tous les recits
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ExperienceTable = wrapper.getMapper('experience')
        query = session.query(ExperienceTable)
        query = query.order_by(ExperienceTable.experience_titre)
        allExperiences = query.all()
        return allExperiences

    def getActiveExperience(self, experiencePk = None):
        """
        table pg recit
        recuperation de l'experience selon la pk
        la pk peut arriver via le form en hidden ou via un lien construit,
         (cas du listing de resultat de moteur de recherche)
        je teste si la pk arrive par param, si pas je prends celle du form
        """
        fields = self.request.form
        experienceTitre = fields.get('titreExperience')
        if not experiencePk:
            experiencePk = fields.get('experience_pk')

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ExperienceTable = wrapper.getMapper('experience')
        query = session.query(ExperienceTable)
        if experienceTitre:
            query = query.filter(ExperienceTable.experience_titre == experienceTitre)
        if experiencePk:
            query = query.filter(ExperienceTable.experience_pk == experiencePk)
        allExperiences = query.all()
        for experience in allExperiences:
            experiencePk = experience.experience_pk
            self.addRechercheLog(experiencePk = experiencePk)
        return allExperiences

    def getExperienceMaxPk(self):
        """
        table pg experience
        recuperation de la derniere pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ExperienceTable = wrapper.getMapper('experience')
        query = session.query(ExperienceTable)
        experience = query.all()
        listePk=[]
        for i in experience:
            listePk.append(i.experience_pk)
        listePk.sort()
        experienceMaxPk=listePk[-1]
        #experienceMaxPk = query.max(ExperienceTable.experience_pk)
        return experienceMaxPk

    def getTranslationExperienceEtat(self, etat):
        """
        traduction de l'état d'une experience
        """
        experienceEtat=''
        if etat=='private':
            experienceEtat='Privé'
        if etat=='pending':
            experienceEtat='En attente'
        if etat=='pending_for_review':
            experienceEtat='En cours de validation'
        if etat=='publish':
            experienceEtat='Publié'
        return experienceEtat

    def getExperienceEtat(self, experiencePk):
        """
        table pg experience
        recuperation de l'état d'une experience selon experience_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ExperienceTable = wrapper.getMapper('experience')
        query = session.query(ExperienceTable)
        query = query.filter(ExperienceTable.experience_pk == experiencePk)
        experience = query.one()
        experienceEtat = self.getTranslationExperienceEtat(experience.experience_etat)
        return experienceEtat

    def getExperienceStatutPublicationForSiss(self, experiencePk):
        """
        table pg experience
        recuperation de l'état de publication de l'experience aupres de SISS BW selon experience_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ExperienceTable = wrapper.getMapper('experience')
        query = session.query(ExperienceTable)
        query = query.filter(ExperienceTable.experience_pk == experiencePk)
        experience = query.one()
        experienceEtatPublicationSiss = self.getTranslationExperienceEtat(experience.experience_etat)
        return experienceEtatPublicationSiss

    def setExperienceStatutPublicationForSissToTrue(self, experiencePk):
        """
        table pg experience
        mettre le statut experience_publication_siss a True apres envoie mail a Siss
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        updateExperience = wrapper.getMapper('experience')
        query = session.query(updateExperience)
        query = query.filter(updateExperience.experience_pk == experiencePk)
        experience = query.one()
        experience.experience_publication_siss = True
        session.flush()

    def permission(self):
        """
        donne des accès particulier à un authentifié qui a le role visiteurDB
        """
        userRole = self.getRoleUserAuthenticated()
        permission = False
        if 'Manager' in userRole:
            permission = True
        elif 'VisiteurDb' in userRole:
            permission = True
        else:
            permission = False
        return permission

    def getExperienceByPk(self, experiencePk, experienceEtat=None):
        """
        table pg experience
        recuperation d'un recit selon experience_pk
        """
        experiencePk = self.getTuple(experiencePk)

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ExperienceTable = wrapper.getMapper('experience')
        query = session.query(ExperienceTable)
        query = query.filter(ExperienceTable.experience_pk.in_(experiencePk))
        if experienceEtat:
            query = query.filter(ExperienceTable.experience_etat == experienceEtat)
        experience = query.all()
        return experience

    def getAllExperienceByEtat(self, experienceEtat):
        """
        table pg experience
        recuperation d'un recit selon experience_pk
        private pending publish
        """
        #role = self.getRoleUserAuthenticated()
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ExperienceTable = wrapper.getMapper('experience')
        query = session.query(ExperienceTable)
        query = query.filter(ExperienceTable.experience_etat == experienceEtat)
        experience = query.all()
        return experience

    def getExperienceByClps(self, clpsPk):
        """
        table pg experience
        recuperation d'une experience selon experience_clps_proprio_fk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ExperienceTable = wrapper.getMapper('experience')
        query = session.query(ExperienceTable)
        query = query.filter(ExperienceTable.experience_clps_proprio_fk == clpsPk)
        experienceByClps = query.all()
        return experienceByClps

    def getExperienceByClpsByEtat(self, clpsPk, experienceEtat):
        """
        table pg experience
        recuperation d'une experience selon experience_clps_proprio_fk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ExperienceTable = wrapper.getMapper('experience')
        query = session.query(ExperienceTable)
        query = query.filter(and_(ExperienceTable.experience_clps_proprio_fk == clpsPk,
                                  ExperienceTable.experience_etat == experienceEtat))
        experienceByClps = query.all()
        return experienceByClps


    def getExperienceByLeffeSearch(self, searchString):
        """
        table pg experience
        recuperation de l'état d'une experience selon experience_pk
        voir ExperienceSearch
        """
        userRole = self.getRoleUserAuthenticated()
        experienceEtat = 'publish'
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ExperienceTable = wrapper.getMapper('experience')
        query = session.query(ExperienceTable)
        if 'Manager' not in userRole:
            query = query.filter(ExperienceTable.experience_etat == experienceEtat)
        query = query.filter(ExperienceTable.experience_titre.ilike("%%%s%%" % searchString))
        experience = [exp.experience_titre for exp in query.all()]
        return experience

    def getCountExperienceByEtat(self, experienceEtat):
        """
        table pg experience
        recuperation du nombre d'experience selon experience_etat
        private pending publish
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ExperienceTable = wrapper.getMapper('experience')
        query = session.query(ExperienceTable)
        query = query.filter(ExperienceTable.experience_etat == experienceEtat)
        nbrExp = select([func.count(ExperienceTable.experience_pk).label('count')])
        nbrExp.append_whereclause(ExperienceTable.experience_etat == experienceEtat)
        nbrExperiencesByEtat = nbrExp.execute().fetchone().count
        return nbrExperiencesByEtat

    def getCountAllExperience(self):
        """
        table pg experience
        recuperation du nombre d'experience
        """
        wrapper = getSAWrapper('clpsbw')
        #session = wrapper.session
        ExperienceTable = wrapper.getMapper('experience')
        #query = session.query(ExperienceTable)
        nbrExp = select([func.count(ExperienceTable.experience_pk).label('count')])
        nbrAllExperiences = nbrExp.execute().fetchone().count
        return nbrAllExperiences

    def getExperienceByAuteurLogin(self):
        """
        table pg experience
        recuperation d'un recit selon le login du user
        """
        loginUser = self.getUserAuthenticated()
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ExperienceTable = wrapper.getMapper('experience')
        query = session.query(ExperienceTable)
        query = query.filter(ExperienceTable.experience_auteur_login == loginUser)
        experienceByAuteurLogin = query.all()
        return experienceByAuteurLogin

    def getExperienceByPlateForme(self, plateForme, limite=None):
        """
        table pg experience
        recuperation d'une experience selon la plateForme
        et selon l'etat publish
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ExperienceTable = wrapper.getMapper('experience')
        query = session.query(ExperienceTable)
        query = query.filter(ExperienceTable.experience_etat == 'publish')
        query = query.order_by(ExperienceTable.experience_modification_date)
        dic = {plateForme: True}
        query = query.filter_by(**dic)
        if limite:
            query = query.limit(5)
        experience = query.all()
        return experience

    def getLastExperience(self, limite=None):
        """
        table pg experience
        recuperation d'une experience selon
           la date de modification
           une limite de 5
           l'etat publish
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ExperienceTable = wrapper.getMapper('experience')
        query = session.query(ExperienceTable)
        query = query.filter(ExperienceTable.experience_etat == 'publish')
        query = query.order_by(ExperienceTable.experience_modification_date)
        if limite:
            query = query.limit(5)
        experience = query.all()
        return experience

    def getExperienceByCommune(self, communePk):
        """
        table pg recit
        recuperation d'un recit selon experience_commune_fk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        ExperienceTable = wrapper.getMapper('experience')
        query = session.query(ExperienceTable)
        query = query.filter(ExperienceTable.experience_commune_fk == communePk)
        experienceByCommune = query.all()
        return experienceByCommune

    def getExperienceByMilieuDeVie(self, milieudeviePk):
        """
        table pg experience
        recuperation d'une experience selon un milieu de vie
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkExperienceMilieuDeVieTable = wrapper.getMapper('link_experience_milieudevie')
        query = session.query(LinkExperienceMilieuDeVieTable)
        for pk in milieudeviePk:
            query = query.filter(LinkExperienceMilieuDeVieTable.milieudevie_fk == pk)
            self.addRechercheLog(milieudeviePk = pk)
        query = query.all()

        experiencePkByMilieuDeVie = []
        for pk in query:
            experiencePkByMilieuDeVie.append(pk.experience_fk)
        experiencesByMilieuDeVie = self.getExperienceByPk(experiencePkByMilieuDeVie, 'publish')
        return experiencesByMilieuDeVie

    def getExperienceByTheme(self, themePk):
        """
        table pg experience
        recuperation d'une experience selon un theme
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkExperienceThemeTable = wrapper.getMapper('link_experience_theme')
        query = session.query(LinkExperienceThemeTable)
        for pk in themePk:
            query = query.filter(LinkExperienceThemeTable.theme_fk == pk)
            self.addRechercheLog(themePk = pk)
        query = query.all()
        experiencePkByTheme = []
        for pk in query:
            experiencePkByTheme.append(pk.experience_fk)
        experiencesByTheme = self.getExperienceByPk(experiencePkByTheme, 'publish')
        return experiencesByTheme

    def getExperienceByRessource(self, ressourcePk):
        """
        table pg experience
        recuperation d'une experience selon une ressource
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkExperienceRessourceTable = wrapper.getMapper('link_experience_ressource')
        query = session.query(LinkExperienceRessourceTable)
        query = query.filter(LinkExperienceRessourceTable.ressource_fk == ressourcePk)
        query = query.all()

        experiencePkByRessource = []
        for pk in query:
            experiencePkByRessource.append(pk.experience_fk)
        experiencesByRessource = self.getExperienceByPk(experiencePkByRessource, 'publish')
        return experiencesByRessource

    def getExperienceByPublic(self, publicPk):
        """
        table pg experience
        recuperation d'une experience selon un public
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkExperiencePublicTable = wrapper.getMapper('link_experience_public')
        query = session.query(LinkExperiencePublicTable)
        for pk in publicPk:
            query = query.filter(LinkExperiencePublicTable.public_fk == pk)
            self.addRechercheLog(publicPk = pk)
        query = query.all()

        experiencePkByPublic = []
        for pk in query:
            experiencePkByPublic.append(pk.experience_fk)
        experiencesByPublic = self.getExperienceByPk(experiencePkByPublic, 'publish')
        return experiencesByPublic

    def getExperienceFromInstitutionPorteur(self, institutionPk):
        """
        table pg link_experience_institution_porteur
        recuperation des experiences liées à une institution selon institution_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkInstitutionPorteurTable = wrapper.getMapper('link_experience_institution_porteur')
        query = session.query(LinkInstitutionPorteurTable)
        query = query.filter(LinkInstitutionPorteurTable.institution_fk == institutionPk)
        experiencePk = query.all()
        listeExperienceForInstitutionPorteur = []
        listeAllExperience = self.getAllExperience()
        for i in experiencePk:
            for j in listeAllExperience:
                if i.experience_fk == j.experience_pk:
                    listeExperienceForInstitutionPorteur.append((j.experience_pk, j.experience_titre))
        return listeExperienceForInstitutionPorteur

    def getExperienceFromInstitutionPartenaire(self, institutionPk):
        """
        table pg link_experience_institution_partenaire
        recuperation des experiences liées à une institution selon institution_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkInstitutionPartenaireTable = wrapper.getMapper('link_experience_institution_partenaire')
        query = session.query(LinkInstitutionPartenaireTable)
        query = query.filter(LinkInstitutionPartenaireTable.institution_fk == institutionPk)
        experiencePk = query.all()
        listeExperienceForInstitutionPartenaire = []
        listeAllExperience = self.getAllExperience()
        for i in experiencePk:
            for j in listeAllExperience:
                if i.experience_fk == j.experience_pk:
                    listeExperienceForInstitutionPartenaire.append((j.experience_pk, j.experience_titre))
        return listeExperienceForInstitutionPartenaire

    def getExperienceFromInstitutionRessource(self, institutionPk):
        """
        table pg link_experience_institution_ressource
        recuperation des experiences liées à une institution selon institution_pk
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        LinkInstitutionRessourceTable = wrapper.getMapper('link_experience_institution_ressource')
        query = session.query(LinkInstitutionRessourceTable)
        query = query.filter(LinkInstitutionRessourceTable.institution_fk == institutionPk)
        experiencePk = query.all()
        listeExperienceForInstitutionRessource = []
        listeAllExperience = self.getAllExperience()
        for i in experiencePk:
            for j in listeAllExperience:
                if i.experience_fk == j.experience_pk:
                    listeExperienceForInstitutionRessource.append((j.experience_pk, j.experience_titre))
        return listeExperienceForInstitutionRessource



    def addExperience(self):
        """
        table pg recit
        ajout d'un recit
        """
        fields = self.context.REQUEST
        experience_titre = getattr(fields, 'experience_titre', None)
        experience_resume = getattr(fields, 'field.experience_resume', None)
        #experience_mots_cles = getattr(fields, 'experience_most_cles', None)
        experience_personne_contact = getattr(fields, 'experience_personne_contact', None)
        experience_personne_contact_email = getattr(fields, 'experience_personne_contact_email', None)
        experience_personne_contact_telephone = getattr(fields, 'experience_personne_contact_telephone', None)
        experience_personne_contact_institution = getattr(fields, 'experience_personne_contact_institution', None)
        experience_element_contexte = getattr(fields, 'field.experience_element_contexte', None)
        experience_objectif = getattr(fields, 'field.experience_objectif', None)
        experience_public_vise = getattr(fields, 'experience_public_vise', None)
        experience_demarche_actions = getattr(fields, 'field.experience_demarche_actions', None)
        experience_commune_international = getattr(fields, 'experience_commune_international', None)
        experience_territoire_tout_luxembourg = getattr(fields, 'experience_territoire_tout_luxembourg', 'False')
        experience_periode_deroulement = getattr(fields, 'experience_periode_deroulement', None)
        experience_moyens = getattr(fields, 'field.experience_moyens', None)
        experience_evaluation_enseignement = getattr(fields, 'field.experience_evaluation_enseignement', None)
        experience_perspective_envisagee = getattr(fields, 'field.experience_perspective_envisagee', None)
        experience_institution_porteur_autre = getattr(fields, 'experience_institution_porteur_autre', None)
        experience_institution_partenaire_autre = getattr(fields, 'experience_institution_partenaire_autre', None)
        experience_institution_ressource_autre = getattr(fields, 'experience_institution_ressource_autre', None)
        experience_institution_outil_autre = getattr(fields, 'experience_institution_outil_autre', None)
        experience_formation_suivie = getattr(fields, 'field.experience_formation_suivie', None)
        experience_autres_ressources = getattr(fields, 'experience_autres_ressources', None)
        experience_aller_plus_loin = getattr(fields, 'field.experience_aller_plus_loin', None)
        experience_plate_forme_sante_ecole = getattr(fields, 'experience_plate_forme_sante_ecole', 'False')
        experience_plate_forme_assuetude = getattr(fields, 'experience_plate_forme_assuetude', 'False')
        experience_plate_forme_sante_famille = getattr(fields, 'experience_plate_forme_sante_famille', 'False')
        experience_plate_forme_sante_environnement = getattr(fields, 'experience_plate_forme_sante_environnement', 'False')
        experience_mission_centre_documentation = getattr(fields, 'experience_mission_centre_documentation', 'False')
        experience_mission_accompagnement_projet = getattr(fields, 'experience_mission_accompagnement_projet', 'False')
        experience_mission_reseau_echange = getattr(fields, 'experience_mission_reseau_echange', 'False')
        experience_mission_formation = getattr(fields, 'experience_mission_formation', 'False')
        experience_etat = getattr(fields, 'experience_etat', None)
        experience_creation_date = self.getTimeStamp()
        experience_creation_employe = self.getUserAuthenticated()
        experience_auteur = getattr(fields, 'experienceAuteur', None)  #via formlaire admin_experience_creation_form
        experience_auteur_fk = getattr(fields, 'experience_auteur_fk', None)
        experience_auteur_login = getattr(fields, 'experience_auteur_login', None)
        experience_clps_proprio_fk = getattr(fields, 'experienceClpsProprio', None)

        if not experience_auteur_fk:   #cas ou c'est un auteur exterieur qui se loggue formulaire experience_creation_form
            auteur = self.getAuteurByLogin('institution')
            experience_auteur_fk= auteur.auteur_pk

        if experience_auteur: #cas ou c'est un clpsmember qui se loggue via formulaire admin_experience_creation_form 
            experience_auteur_fk = self.getAuteurPkByName(experience_auteur)
            experience_auteur_login = self.getAuteurLogin(experience_auteur_fk)

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertExperience = wrapper.getMapper('experience')
        newEntry = insertExperience(experience_titre = experience_titre, \
                                    experience_resume = experience_resume, \
                                    experience_personne_contact = experience_personne_contact, \
                                    experience_personne_contact_email = experience_personne_contact_email, \
                                    experience_personne_contact_telephone = experience_personne_contact_telephone, \
                                    experience_personne_contact_institution = experience_personne_contact_institution, \
                                    experience_element_contexte = experience_element_contexte, \
                                    experience_objectif = experience_objectif, \
                                    experience_public_vise = experience_public_vise, \
                                    experience_demarche_actions = experience_demarche_actions, \
                                    experience_commune_international = experience_commune_international, \
                                    experience_territoire_tout_luxembourg = experience_territoire_tout_luxembourg, \
                                    experience_periode_deroulement = experience_periode_deroulement, \
                                    experience_moyens = experience_moyens, \
                                    experience_evaluation_enseignement = experience_evaluation_enseignement, \
                                    experience_perspective_envisagee = experience_perspective_envisagee, \
                                    experience_institution_porteur_autre = experience_institution_porteur_autre, \
                                    experience_institution_partenaire_autre = experience_institution_partenaire_autre, \
                                    experience_institution_ressource_autre = experience_institution_ressource_autre, \
                                    experience_institution_outil_autre = experience_institution_outil_autre, \
                                    experience_formation_suivie = experience_formation_suivie, \
                                    experience_autres_ressources = experience_autres_ressources, \
                                    experience_aller_plus_loin = experience_aller_plus_loin, \
                                    experience_plate_forme_sante_ecole = experience_plate_forme_sante_ecole, \
                                    experience_plate_forme_assuetude = experience_plate_forme_assuetude, \
                                    experience_plate_forme_sante_famille = experience_plate_forme_sante_famille, \
                                    experience_plate_forme_sante_environnement = experience_plate_forme_sante_environnement, \
                                    experience_mission_centre_documentation = experience_mission_centre_documentation, \
                                    experience_mission_accompagnement_projet = experience_mission_accompagnement_projet, \
                                    experience_mission_reseau_echange = experience_mission_reseau_echange, \
                                    experience_mission_formation = experience_mission_formation, \
                                    experience_auteur_login = experience_auteur_login, \
                                    experience_auteur_fk = experience_auteur_fk, \
                                    experience_clps_proprio_fk = experience_clps_proprio_fk, \
                                    experience_etat = experience_etat, \
                                    experience_creation_date = experience_creation_date, \
                                    experience_creation_employe = experience_creation_employe)
        session.save(newEntry)
        session.flush()

    def addLinkExperienceCommune(self, experienceFk, experienceCommuneFk):
        """
        table pg link_experience_commune
        ajout des communes liées à une expérience
        """
        #fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkExperienceCommune = wrapper.getMapper('link_experience_commune')
        for communeFk in experienceCommuneFk:
            newEntry = insertLinkExperienceCommune(experience_fk = experienceFk,
                                                   commune_fk = communeFk)
            session.save(newEntry)
        session.flush()

    def addLinkExperienceInstitutionPorteur(self, experienceFk):
        """
        ajout des institution de types porteur
        """
        fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        experience_institution_porteur_fk = getattr(fields, 'experience_institution_porteur_fk', None)
        if experience_institution_porteur_fk:
            insertExperienceInstitutionPorteur = wrapper.getMapper('link_experience_institution_porteur')
            institutionPorteur =getattr(fields, 'experience_institution_porteur_fk', None)
            for pk in institutionPorteur:
                newEntry = insertExperienceInstitutionPorteur(experience_fk = experienceFk,
                                                              institution_fk= pk)
                session.save(newEntry)
        session.flush()

    def addLinkExperienceInstitutionPartenaire(self, experienceFk):
        """
        ajout des institutions partenaire
        """
        fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        experience_institution_partenaire_fk = getattr(fields, 'experience_institution_partenaire_fk', None)
        if experience_institution_partenaire_fk:
            insertExperienceInstitutionPartenaire = wrapper.getMapper('link_experience_institution_partenaire')
            institutionPartenaire = getattr(fields, 'experience_institution_partenaire_fk', None)
            for pk in institutionPartenaire:
                newEntry = insertExperienceInstitutionPartenaire(experience_fk = experienceFk,
                                                                 institution_fk= pk)
                session.save(newEntry)
        session.flush()

    def addLinkExperienceInstitutionRessource(self, experienceFk):
        """
        ajout des ressources institutions
        """
        fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        experience_institution_ressource_fk = getattr(fields, 'experience_institution_ressource_fk', None)
        if experience_institution_ressource_fk:
            insertExperienceInstitutionRessource = wrapper.getMapper('link_experience_institution_ressource')
            institutionRessource = getattr(fields, 'experience_institution_ressource_fk', None)
            for pk in institutionRessource:
                newEntry = insertExperienceInstitutionRessource(experience_fk = experienceFk,
                                                                institution_fk= pk)
                session.save(newEntry)
        session.flush()

    def addLinkExperienceRessource(self, experienceFk):
        """
        table pg link_experience_ressource
        ajout des ressources liées à une expérience
        """
        fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkExperienceRessource = wrapper.getMapper('link_experience_ressource')
        experienceRessourceFk = getattr(fields, 'experience_ressource_fk', None)
        for ressourceFk in experienceRessourceFk:
            newEntry = insertLinkExperienceRessource(experience_fk = experienceFk,
                                                     ressource_fk = ressourceFk)
            session.save(newEntry)
        session.flush()

    def addLinkExperienceMilieuDeVie(self, experienceFk, milieuDeVieFks):
        """
        table pg link_experience_milieudevie
        ajout des milieux de vie liées à une expérience
        """
        #fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkExperienceMilieuDeVie = wrapper.getMapper('link_experience_milieudevie')
        for milieuDeVieFk in milieuDeVieFks:
            newEntry = insertLinkExperienceMilieuDeVie(experience_fk = experienceFk,
                                                       milieudevie_fk = milieuDeVieFk)
            session.save(newEntry)
        session.flush()

    def addLinkExperienceTheme(self, experienceFk, themeFks):
        """
        table pg link_experience_theme
        ajout des thèmes liées à une expérience
        """
        #fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkExperienceTheme = wrapper.getMapper('link_experience_theme')
        for themeFk in themeFks:
            newEntry = insertLinkExperienceTheme(experience_fk = experienceFk,
                                                 theme_fk = themeFk)
            session.save(newEntry)
        session.flush()

    def addLinkExperiencePublic(self, experienceFk, publicFks):
        """
        table pg link_experience_public
        ajout des publics liées à une expérience
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkExperiencePublic = wrapper.getMapper('link_experience_public')
        for publicFk in publicFks:
            newEntry = insertLinkExperiencePublic(experience_fk = experienceFk,
                                                  public_fk = publicFk)
            session.save(newEntry)
        session.flush()

    def addLinkExperienceMotCle(self, experienceFk, motCleFks):
        """
        table pg link_experience_commune
        ajout des communes liées à une expérience
        """
        #fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkExperienceMotCle = wrapper.getMapper('link_experience_mot_cle')
        for motCleFk in motCleFks:
            newEntry = insertLinkExperienceMotCle(experience_fk = experienceFk,
                                                  motcle_fk = motCleFk)
            session.save(newEntry)
        session.flush()

    def addLinkExperienceSousPlateForme(self, experienceFk):
        """
        table pg link_experience_sousplateforme
        ajout des sous plate-forme de vie liées à une expérience
        """
        fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkExperienceSousPlateForme = wrapper.getMapper('link_experience_sousplateforme')
        experienceSousPlateFormeFk = getattr(fields, 'experience_sousplateforme_fk', None)
        for sousPlateFormeFk in experienceSousPlateFormeFk:
            newEntry = insertLinkExperienceSousPlateForme(experience_fk = experienceFk,
                                                          sousplateforme_fk = sousPlateFormeFk)
            session.save(newEntry)
        session.flush()

    def addLinkExperienceClpsProprio(self, experienceFk):
        """
        table pg link_experience_clps_proprio
        ajout des clps proprietaire de l'experience
        """
        fields = self.context.REQUEST
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertLinkExperienceClpsProprio = wrapper.getMapper('link_experience_clps_proprio')
        experienceClps = getattr(fields, 'experience_clps_proprio_fk', None)
        for clpsFk in experienceClps:
            newEntry = insertLinkExperienceClpsProprio(experience_fk = experienceFk,
                                                       clps_fk = clpsFk)
            session.save(newEntry)
        session.flush()

    def deleteLinkExperienceClpsProprio(self, experienceFk):
        """
        table pg link_experience_clps_proprio
        suppression des proprio des experiences
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkExperienceClpsProprio = wrapper.getMapper('link_experience_clps_proprio')
        query = session.query(deleteLinkExperienceClpsProprio)
        query = query.filter(deleteLinkExperienceClpsProprio.experience_fk == experienceFk)
        for experienceFk in query.all():
            session.delete(experienceFk)
        session.flush()

    def deleteLinkExperienceMotCle(self, experienceFk):
        """
        table pg Link_experience_mot_cle
        suppression des mots-cle liées à une experience
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkExperienceMotCle = wrapper.getMapper('link_experience_mot_cle')
        query = session.query(deleteLinkExperienceMotCle)
        query = query.filter(deleteLinkExperienceMotCle.experience_fk == experienceFk)
        for experienceFk in query.all():
            session.delete(experienceFk)
        session.flush()

    def deleteLinkExperienceCommune(self, experienceFk):
        """
        table pg Link_experience_commune
        suppression des communes liées à une experience
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkExperienceCommune = wrapper.getMapper('link_experience_commune')
        query = session.query(deleteLinkExperienceCommune)
        query = query.filter(deleteLinkExperienceCommune.experience_fk == experienceFk)
        for experienceFk in query.all():
            session.delete(experienceFk)
        session.flush()

    def deleteLinkExperienceInstitutionPorteur(self, experienceFk):
        """
        table pg link_experience_institution_porteur
        suppression des institutions porteur liées à une experience
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkExperienceInstitutionPorteur = wrapper.getMapper('link_experience_institution_porteur')
        query = session.query(deleteLinkExperienceInstitutionPorteur)
        query = query.filter(deleteLinkExperienceInstitutionPorteur.experience_fk == experienceFk)
        for experienceFk in query.all():
            session.delete(experienceFk)
        session.flush()

    def deleteLinkExperienceInstitutionPartenaire(self, experienceFk):
        """
        table pg link_experience_institution_partenaire
        suppression des institutions partenaires liées à une experience
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkExperienceInstitutionPartenaire = wrapper.getMapper('link_experience_institution_partenaire')
        query = session.query(deleteLinkExperienceInstitutionPartenaire)
        query = query.filter(deleteLinkExperienceInstitutionPartenaire.experience_fk == experienceFk)
        for experienceFk in query.all():
            session.delete(experienceFk)
        session.flush()

    def deleteLinkExperienceInstitutionRessource(self, experienceFk):
        """
        table pg link_experience_institution_ressource
        suppression des institutions ressources liées à une experience
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkExperienceInstitutionRessource = wrapper.getMapper('link_experience_institution_ressource')
        query = session.query(deleteLinkExperienceInstitutionRessource)
        query = query.filter(deleteLinkExperienceInstitutionRessource.experience_fk == experienceFk)
        for experienceFk in query.all():
            session.delete(experienceFk)
        session.flush()

    def deleteLinkExperienceRessource(self, experienceFk):
        """
        table pg link_experience_ressource
        suppression des ressources liées à une experience
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkExperienceRessource = wrapper.getMapper('link_experience_ressource')
        query = session.query(deleteLinkExperienceRessource)
        query = query.filter(deleteLinkExperienceRessource.experience_fk == experienceFk)
        for experienceFk in query.all():
            session.delete(experienceFk)
        session.flush()

    def deleteLinkExperienceMilieuDeVie(self, experienceFk):
        """
        table pg link_experience_milieudevie
        suppression des milieu de vie liées à une experience
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkExperienceMilieuDeVie = wrapper.getMapper('link_experience_milieudevie')
        query = session.query(deleteLinkExperienceMilieuDeVie)
        query = query.filter(deleteLinkExperienceMilieuDeVie.experience_fk == experienceFk)
        for experienceFk in query.all():
            session.delete(experienceFk)
        session.flush()

    def deleteLinkExperienceTheme(self, experienceFk):
        """
        table pg link_experience_theme
        suppression des themes liées à une experience
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkExperienceTheme = wrapper.getMapper('link_experience_theme')
        query = session.query(deleteLinkExperienceTheme)
        query = query.filter(deleteLinkExperienceTheme.experience_fk == experienceFk)
        for experienceFk in query.all():
            session.delete(experienceFk)
        session.flush()

    def deleteLinkExperiencePublic(self, experienceFk):
        """
        table pg link_experience_public
        suppression des publics liées à une experience
        """
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        deleteLinkExperiencePublic = wrapper.getMapper('link_experience_public')
        query = session.query(deleteLinkExperiencePublic)
        query = query.filter(deleteLinkExperiencePublic.experience_fk == experienceFk)
        for experienceFk in query.all():
            session.delete(experienceFk)
        session.flush()

    def updateExperience(self):
        """
        table pg experience
        mise à jour des infos d'une experience
        """
        fields = self.context.REQUEST
        experience_pk = getattr(fields, 'experience_pk')
        experience_titre = getattr(fields, 'experience_titre', None)
        experience_resume = getattr(fields, 'field.experience_resume', None)
        #experience_mots_cles = getattr(fields, 'experience_most_cles', None)
        experience_personne_contact = getattr(fields, 'experience_personne_contact', None)
        experience_personne_contact_email = getattr(fields, 'experience_personne_contact_email', None)
        experience_personne_contact_telephone = getattr(fields, 'experience_personne_contact_telephone', None)
        experience_personne_contact_institution = getattr(fields, 'experience_personne_contact_institution', None)
        experience_element_contexte = getattr(fields, 'field.experience_element_contexte', None)
        experience_objectif = getattr(fields, 'field.experience_objectif', None)
        experience_public_vise = getattr(fields, 'experience_public_vise', None)
        experience_demarche_actions = getattr(fields, 'field.experience_demarche_actions', None)
        experience_commune_international = getattr(fields, 'experience_commune_international', None)
        experience_territoire_tout_luxembourg = getattr(fields, 'experience_territoire_tout_luxembourg', None)
        experience_periode_deroulement = getattr(fields, 'experience_periode_deroulement', None)
        experience_moyens = getattr(fields, 'field.experience_moyens', None)
        experience_evaluation_enseignement = getattr(fields, 'field.experience_evaluation_enseignement', None)
        experience_perspective_envisagee = getattr(fields, 'field.experience_perspective_envisagee', None)
        experience_institution_porteur_autre = getattr(fields, 'experience_institution_porteur_autre', None)
        experience_institution_partenaire_autre = getattr(fields, 'experience_institution_partenaire_autre', None)
        experience_institution_ressource_autre = getattr(fields, 'experience_institution_ressource_autre', None)
        experience_institution_outil_autre = getattr(fields, 'experience_institution_outil_autre', None)
        experience_formation_suivie = getattr(fields, 'field.experience_formation_suivie', None)
        experience_aller_plus_loin = getattr(fields, 'field.experience_aller_plus_loin', None)
        experience_plate_forme_sante_ecole = getattr(fields, 'experience_plate_forme_sante_ecole', False)
        experience_plate_forme_assuetude = getattr(fields, 'experience_plate_forme_assuetude', False)
        experience_plate_forme_sante_famille = getattr(fields, 'experience_plate_forme_sante_famille', False)
        experience_plate_forme_sante_environnement = getattr(fields, 'experience_plate_forme_sante_environnement', False)
        experience_mission_centre_documentation = getattr(fields, 'experience_mission_centre_documentation', False)
        experience_mission_accompagnement_projet = getattr(fields, 'experience_mission_accompagnement_projet', False)
        experience_mission_reseau_echange = getattr(fields, 'experience_mission_reseau_echange', False)
        experience_mission_formation = getattr(fields, 'experience_mission_formation', False)
        experience_etat = getattr(fields, 'experience_etat', None)
        experience_modification_date = self.getTimeStamp()
        experience_modification_employe = self.getUserAuthenticated()
        experience_auteur_fk = getattr(fields, 'experience_auteur_fk', None)
        experience_auteur_login = getattr(fields, 'experience_auteur_login', None)


        #cas de modification de l'auteur via ligth search
        experience_auteur = getattr(fields, 'experienceAuteur', None)
        if experience_auteur:
            experience_auteur_fk = self.getAuteurPkByName(experience_auteur)

        #cas d'un update par personnel CLPS qui peut modifier le login , donc la propriété d'une expérience.
        if not experience_auteur_login:
            experience_auteur_login = self.getAuteurLogin(experience_auteur_fk)

        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        updateExperience = wrapper.getMapper('experience')
        query = session.query(updateExperience)
        query = query.filter(updateExperience.experience_pk == experience_pk)
        experience = query.one()

        experience.experience_titre = unicode(experience_titre, 'utf-8')
        experience.experience_resume = unicode(experience_resume, 'utf-8')
        experience.experience_personne_contact = unicode(experience_personne_contact, 'utf-8')
        experience.experience_personne_contact_email = unicode(experience_personne_contact_email, 'utf-8')
        experience.experience_personne_contact_telephone = unicode(experience_personne_contact_telephone, 'utf-8')
        experience.experience_personne_contact_institution = unicode(experience_personne_contact_institution, 'utf-8')
        experience.experience_element_contexte = unicode(experience_element_contexte, 'utf-8')
        experience.experience_objectif = unicode(experience_objectif, 'utf-8')
        experience.experience_public_vise = unicode(experience_public_vise, 'utf-8')
        experience.experience_demarche_actions = unicode(experience_demarche_actions, 'utf-8')
        experience.experience_commune_international = unicode(experience_commune_international, 'utf-8')
        experience.experience_territoire_tout_luxembourg = experience_territoire_tout_luxembourg
        experience.experience_periode_deroulement = unicode(experience_periode_deroulement, 'utf-8')
        experience.experience_moyens = unicode(experience_moyens, 'utf-8')
        experience.experience_evaluation_enseignement = unicode(experience_evaluation_enseignement, 'utf-8')
        experience.experience_perspective_envisagee = unicode(experience_perspective_envisagee, 'utf-8')
        experience.experience_institution_porteur_autre = unicode(experience_institution_porteur_autre, 'utf-8')
        experience.experience_institution_partenaire_autre = unicode(experience_institution_partenaire_autre, 'utf-8')
        experience.experience_institution_ressource_autre = unicode(experience_institution_ressource_autre, 'utf-8')
        experience.experience_institution_outil_autre = unicode(experience_institution_outil_autre, 'utf-8')
        experience.experience_formation_suivie = unicode(experience_formation_suivie, 'utf-8')
        experience.experience_aller_plus_loin = unicode(experience_aller_plus_loin, 'utf-8')
        experience.experience_plate_forme_sante_ecole = experience_plate_forme_sante_ecole
        experience.experience_plate_forme_assuetude = experience_plate_forme_assuetude
        experience.experience_plate_forme_sante_famille = experience_plate_forme_sante_famille
        experience.experience_plate_forme_sante_environnement = experience_plate_forme_sante_environnement
        experience.experience_mission_centre_documentation = experience_mission_centre_documentation
        experience.experience_mission_accompagnement_projet = experience_mission_accompagnement_projet
        experience.experience_mission_reseau_echange = experience_mission_reseau_echange
        experience.experience_mission_formation = experience_mission_formation
        experience.experience_auteur_login = experience_auteur_login
        experience.experience_auteur_fk = experience_auteur_fk
        experience.experience_etat = unicode(experience_etat, 'utf-8')
        experience.experience_modification_employe = experience_modification_employe
        experience.experience_modification_date = experience_modification_date
        session.flush()


### LOG ###

    def addRechercheLog(self, \
                        experiencePk = None, \
                        milieudeviePk = None, \
                        themePk = None, \
                        publicPk = None, \
                        motclePk = None):
        """
        table pg recherche_log
        ajout les pk des parametres d'une recherche
        """
        fields = self.context.REQUEST
        recherchelog_requete = getattr(fields, 'recherchelog_requete', None)
        recherchelog_user = self.getUserAuthenticated()
        recherchelog_date = self.getTimeStamp()
        wrapper = getSAWrapper('clpsbw')
        session = wrapper.session
        insertRechercheLog = wrapper.getMapper('recherche_log')
        newEntry = insertRechercheLog(recherchelog_requete = recherchelog_requete, \
                                      recherchelog_user = recherchelog_user, \
                                      recherchelog_experience_fk = experiencePk, \
                                      recherchelog_milieudevie_fk = milieudeviePk, \
                                      recherchelog_theme_fk = themePk, \
                                      recherchelog_public_fk = publicPk, \
                                      recherchelog_motcle_fk = motclePk, \
                                      recherchelog_date = recherchelog_date)
        session.add(newEntry) #session.save(newEntry)
        session.flush()
        return {'status': 1}



#### MANAGE ####

    def manageAssuetudeInterventionForInstitution(self):
        """
        insertion ou update d'une assuetude intervention pour institution
        """
        fields = self.context.REQUEST
        operation = getattr(fields, 'operation')

        if operation =="insert":
            self.addAssuetudeInterventionForInstitution()
            return {'status': 1}

        if operation == "update":
            self.updateAssuetudeInterventionForInstitution()
            return {'status': 1}

    def manageAssuetudeActiviteProposeeForInstitution(self):
        """
              '(insertion ou update d'une assuetude activite proposee pour institution
        """
        fields = self.context.REQUEST
        operation = getattr(fields, 'operation')

        if operation =="insert":
            self.addAssuetudeActiviteProposeeForInstitution()
            return {'status': 1}

        if operation == "update":
            self.updateAssuetudeActiviteProposeeForInstitution()
            return {'status': 1}

    def manageAssuetudeThematiqueForInstitution(self):
        """
        insertion ou update d'une assuetude thematique pour institution
        """
        fields = self.context.REQUEST
        operation = getattr(fields, 'operation')

        if operation =="insert":
            self.addAssuetudeThematiqueForInstitution()
            return {'status': 1}

        if operation == "update":
            self.updateAssuetudeThematiqueForInstitution()
            return {'status': 1}

    def manageMotCle(self):
        """
        insertion ou update d'un mot-cle
        """
        fields = self.context.REQUEST
        operation = getattr(fields, 'operation')

        if operation =="insert":
            self.addMotCle()
            return {'status': 1}

        if operation == "update":
            self.updateMotCle()
            return {'status': 1}

    def manageTheme(self):
        """
        insertion ou update d'un theme
        """
        fields = self.context.REQUEST
        operation = getattr(fields, 'operation')

        if operation =="insert":
            self.addTheme()
            return {'status': 1}

        if operation == "update":
            self.updateTheme()
            return {'status': 1}

    def managePublic(self):
        """
        insertion ou update d'un public
        """
        fields = self.context.REQUEST
        operation = getattr(fields, 'operation')

        if operation =="insert":
            self.addPublic()
            return {'status': 1}

        if operation == "update":
            self.updatePublic()
            return {'status': 1}

    def managePlateForme(self):
        """
        insertion ou update d'un plateforme
        """
        fields = self.context.REQUEST
        operation = getattr(fields, 'operation')

        if operation =="insert":
            self.addPlateForme()
            return {'status': 1}

        if operation == "update":
            self.updatePlateForme()
            return {'status': 1}

    def manageSousPlateForme(self):
        """
        insertion ou update d'un plateforme
        """
        fields = self.context.REQUEST
        operation = getattr(fields, 'operation')

        if operation =="insert":
            self.addSousPlateForme()
            return {'status': 1}

        if operation == "update":
            self.updateSousPlateForme()
            return {'status': 1}

    def manageMilieuDeVie(self):
        """
        insertion ou update d'un milieu de vie
        """
        fields = self.context.REQUEST
        operation = getattr(fields, 'operation')

        if operation =="insert":
            self.addMilieuDeVie()
            return {'status': 1}

        if operation == "update":
            self.updateMilieuDeVie()
            return {'status': 1}

    def manageInstitutionType(self):
        """
        insertion ou update d'un type d'institution
        """
        fields = self.context.REQUEST
        operation = getattr(fields, 'operation')

        if operation =="insert":
            self.addInstitutionType()
            return {'status': 1}

        if operation == "update":
            self.updateInstitutionType()
            return {'status': 1}

    def manageInstitution(self):
        """
        insertion ou update d'une institution
        """
        fields = self.context.REQUEST
        operation = getattr(fields, 'operation')
        institutionSousPlateFormeFk = getattr(fields, 'institution_sousplateforme_fk', None)

        #creation de la liste des communes
        institutionCommuneCouverteFk = []
        institutionCommuneCouverteInBwFk = getattr(fields, 'institution_commune_couverte_inbw_fk', None)
        institutionCommuneCouverteOutBwFk = (getattr(fields, 'institution_commune_couverte_outbw_fk', None))
        if institutionCommuneCouverteInBwFk:
            for pk in institutionCommuneCouverteInBwFk:
                institutionCommuneCouverteFk.append(pk)
        if institutionCommuneCouverteOutBwFk:
            for pk in institutionCommuneCouverteOutBwFk:
                institutionCommuneCouverteFk.append(pk)

        assuetudeInterventionFk = getattr(fields, 'assuetude_intervention_fk', None)
        assuetudeActiviteProposeePublicFk = getattr(fields, 'assuetude_activite_proposee_public_fk', None)
        assuetudeActiviteProposeeProFk = getattr(fields, 'assuetude_activite_proposee_pro_fk', None)
        assuetudeThematiqueFk = getattr(fields, 'assuetude_thematique_fk', None)
        institutionClpsProprioFk = getattr(fields, 'institution_clps_proprio_fk', None)

        if operation =="insert":
            self.addInstitution()
            institutionFk = self.getInstitutionMaxPk()

            if assuetudeInterventionFk > 0:
                self.addLinkInstitutionAssuetudeIntervention(institutionFk)

            if assuetudeActiviteProposeePublicFk > 0:
                self.addLinkInstitutionAssuetudeActiviteProposeePublic(institutionFk, assuetudeActiviteProposeePublicFk)

            if assuetudeActiviteProposeeProFk > 0:
                self.addLinkInstitutionAssuetudeActiviteProposeePro(institutionFk, assuetudeActiviteProposeeProFk)

            if assuetudeThematiqueFk > 0:
                self.addLinkInstitutionAssuetudeThematique(institutionFk)

            if institutionSousPlateFormeFk:
                self.addLinkInstitutionSousPlateForme(institutionFk)

            if institutionCommuneCouverteFk:
                self.addLinkInstitutionCommuneCouverte(institutionFk, institutionCommuneCouverteFk)

            if institutionClpsProprioFk:                             #gestion du clps_proprio
                self.addLinkInstitutionClpsProprio(institutionFk)
            return {'status': 1}

        if operation == "update":
            institutionSousPlateFormeFk = getattr(fields, 'institution_sousplateforme_fk', None)
            institutionFk = getattr(fields, 'institution_pk')
            self.updateInstitution()

            self.deleteLinkInstitutionAssuetudeIntervention(institutionFk)
            if assuetudeInterventionFk > 0:
                self.addLinkInstitutionAssuetudeIntervention(institutionFk)

            self.deleteLinkInstitutionAssuetudeActiviteProposeePublic(institutionFk)
            if assuetudeActiviteProposeePublicFk > 0:
                self.addLinkInstitutionAssuetudeActiviteProposeePublic(institutionFk, assuetudeActiviteProposeePublicFk)

            self.deleteLinkInstitutionAssuetudeActiviteProposeePro(institutionFk)
            if assuetudeActiviteProposeeProFk > 0:
                self.addLinkInstitutionAssuetudeActiviteProposeePro(institutionFk, assuetudeActiviteProposeeProFk)

            self.deleteLinkInstitutionAssuetudeThematique(institutionFk)
            if assuetudeThematiqueFk > 0:
                self.addLinkInstitutionAssuetudeThematique(institutionFk)

            self.deleteLinkInstitutionSousPlateForme(institutionFk)
            if institutionSousPlateFormeFk > 0:
                self.addLinkInstitutionSousPlateForme(institutionFk)

            self.deleteLinkInstitutionCommuneCouverte(institutionFk)
            if institutionCommuneCouverteFk > 0:
                self.addLinkInstitutionCommuneCouverte(institutionFk, institutionCommuneCouverteFk)

            self.deleteLinkInstitutionClpsProprio(institutionFk)
            if institutionClpsProprioFk:
                self.addLinkInstitutionClpsProprio(institutionFk)
            return {'status': 1}

    def manageRessource(self):
        """
        insertion ou update d'une ressource
        """
        fields = self.context.REQUEST
        operation = getattr(fields, 'operation')
        ressourcePublicFk = getattr(fields, 'ressource_public_fk', None)
        ressourceSupportFk = getattr(fields, 'ressource_support_fk', None)
        ressourceThemeFk = getattr(fields, 'ressource_theme_fk', None)
        ressourceClpsProprioFk = getattr(fields, 'ressource_clps_proprio_fk', None)
        ressourceClpsDispoFk = getattr(fields, 'ressource_clps_dispo_fk', None)

        if operation =="insert":
            self.addRessource()
            ressourceFk = self.getRessourceMaxPk()
            if ressourcePublicFk > 0:
                self.addLinkRessourcePublic(ressourceFk)
            if ressourceSupportFk > 0:
                self.addLinkRessourceSupport(ressourceFk)
            if ressourceThemeFk > 0:
                self.addLinkRessourceTheme(ressourceFk)
            if ressourceClpsProprioFk:                          #gestion du clps proprio
                self.addLinkRessourceClpsProprio(ressourceFk)
            if ressourceClpsDispoFk:                            #gestion du clps proprio
                self.addLinkRessourceClpsDispo(ressourceFk)
            return {'status': 1}


        if operation == "update":
            ressourceFk = getattr(fields, 'ressource_pk')
            self.updateRessource()

            self.deleteLinkRessourcePublic(ressourceFk)
            if ressourcePublicFk > 0:
                self.addLinkRessourcePublic(ressourceFk)

            self.deleteLinkRessourceSupport(ressourceFk)
            if ressourceSupportFk > 0:
                self.addLinkRessourceSupport(ressourceFk)

            self.deleteLinkRessourceTheme(ressourceFk)
            if ressourceThemeFk > 0:
                self.addLinkRessourceTheme(ressourceFk)

            self.deleteLinkRessourceClpsProprio(ressourceFk)
            if ressourceClpsProprioFk:
                self.addLinkRessourceClpsProprio(ressourceFk)

            self.deleteLinkRessourceClpsDispo(ressourceFk)
            if ressourceClpsDispoFk:
                self.addLinkRessourceClpsDispo(ressourceFk)

            return {'status': 1}

    def manageSupport(self):
        """
        insertion ou update d'un support
        """
        fields = self.context.REQUEST
        operation = getattr(fields, 'operation')

        if operation =="insert":
            self.addSupport()
            return {'status': 1}

        if operation == "update":
            self.updateSupport()
            return {'status': 1}

    def manageAuteur(self):
        """
        insertion ou update d'un support
        """
        fields = self.context.REQUEST
        operation = getattr(fields, 'operation')

        login = getattr(fields, 'auteur_login')
        passw = getattr(fields, 'auteur_pass')
        role = 'RecitExperience'
        userId = getattr(fields, 'auteur_login')
        userEmail = getattr(fields, 'auteur_email')
        prenom = getattr(fields, 'auteur_prenom')
        nom = getattr(fields, 'auteur_nom')
        userName = ('%s %s')%(prenom, nom)

        if operation =="insert":
            self.addAuteur()
            self.addLoginAuteur(login, passw, role)
            self.addInfoAuteur(userId, userEmail, userName)
            return {'status': 1}

        if operation == "update":
            self.updateAuteur()
            return {'status': 1}

    def manageExperience(self):
        """
        insertion ou update d'une experience
        """
        fields = self.context.REQUEST
        operation = getattr(fields, 'operation')

        experienceInstitutionPorteurFk = getattr(fields, 'experience_institution_porteur_fk', None)
        experienceInstitutionPartenaireFk = getattr(fields, 'experience_institution_partenaire_fk', None)
        experienceInstitutionRessourceFk = getattr(fields, 'experience_institution_ressource_fk', None)
        experienceRessourceFk = getattr(fields, 'experience_ressource_fk', None)
        experienceSousPlateFormeFk = getattr(fields, 'experience_sousplateforme_fk', None)
        #experience_etat = getattr(fields, 'experience_etat', None)
        #experience_institution_outil_autre = getattr(fields, 'experience_institution_outil_autre', None)
        experienceClpsProprioFk = getattr(fields, 'experience_clps_proprio_fk', None)

 #ajout des nouvelles valeur des addremovewidget
        experienceMotCleFk = getattr(fields, 'experience_mot_cle_fk', None)
        if experienceMotCleFk is not None:
            experienceMotCleFk = self.addMotCleFkKeywordsIfNeededAndGetPks(experienceMotCleFk)

        experienceMilieuDeVieFk = getattr(fields, 'experience_milieu_vie_fk', None)
        if experienceMilieuDeVieFk is not None:
            experienceMilieuDeVieFk = self.addMilieuDeVieKeywordsIfNeededAndGetPks(experienceMilieuDeVieFk)

        experienceThemeFk = getattr(fields, 'experience_theme_fk', None)
        if experienceThemeFk is not None:
            experienceThemeFk = self.addThemeKeywordsIfNeededAndGetPks(experienceThemeFk)

        experiencePublicFk = getattr(fields, 'experience_public_fk', None)
        if experiencePublicFk is not None:
            experiencePublicFk = self.addPublicKeywordsIfNeededAndGetPks(experiencePublicFk)


        #creation de la liste des communes
        experienceCommuneFk = []
        experienceCommuneInBwFk = getattr(fields, 'experience_commune_inbw_fk', None)
        experienceCommuneOutBwFk = (getattr(fields, 'experience_commune_outbw_fk', None))
        if experienceCommuneInBwFk:
            for pk in experienceCommuneInBwFk:
                experienceCommuneFk.append(pk)
        if experienceCommuneOutBwFk:
            for pk in experienceCommuneOutBwFk:
                experienceCommuneFk.append(pk)

        if operation =="insert":
            self.addExperience()
            experienceFk = self.getExperienceMaxPk()

            if experienceCommuneFk > 0:
                self.addLinkExperienceCommune(experienceFk, experienceCommuneFk)

            if experienceInstitutionPorteurFk > 0:
                self.addLinkExperienceInstitutionPorteur(experienceFk)

            if experienceInstitutionPartenaireFk > 0:
                self.addLinkExperienceInstitutionPartenaire(experienceFk)

            if experienceInstitutionRessourceFk > 0:
                self.addLinkExperienceInstitutionRessource(experienceFk)

            if experienceRessourceFk > 0:
                self.addLinkExperienceRessource(experienceFk)

            if experienceSousPlateFormeFk > 0:
                self.addLinkExperienceSousPlateForme(experienceFk)

            if experienceMilieuDeVieFk > 0:
                self.addLinkExperienceMilieuDeVie(experienceFk, experienceMilieuDeVieFk)

            if experienceMotCleFk > 0:
                self.addLinkExperienceMotCle(experienceFk, experienceMotCleFk)

            if experienceThemeFk > 0:
                self.addLinkExperienceTheme(experienceFk, experienceThemeFk)

            if experiencePublicFk > 0:
                self.addLinkExperiencePublic(experienceFk, experiencePublicFk)

            if experienceClpsProprioFk:                             #gestion du clps proprio
                self.addLinkExperienceClpsProprio(experienceFk)

            self.sendMailForInsertExperience(experiencePk = experienceFk)

            # #self.addLinkRessourceSupport()
            return {'status': 1}

        if operation == "update":
            experienceFk = getattr(fields, 'experience_pk')
            self.updateExperience()

            self.deleteLinkExperienceCommune(experienceFk)
            if experienceCommuneFk > 0:
                self.addLinkExperienceCommune(experienceFk, experienceCommuneFk)

            self.deleteLinkExperienceInstitutionPorteur(experienceFk)
            if experienceInstitutionPorteurFk > 0:
                self.addLinkExperienceInstitutionPorteur(experienceFk)

            self.deleteLinkExperienceInstitutionPartenaire(experienceFk)
            if experienceInstitutionPartenaireFk > 0:
                self.addLinkExperienceInstitutionPartenaire(experienceFk)

            self.deleteLinkExperienceInstitutionRessource(experienceFk)
            if experienceInstitutionRessourceFk > 0:
                self.addLinkExperienceInstitutionRessource(experienceFk)

            self.deleteLinkExperienceRessource(experienceFk)
            if experienceRessourceFk > 0:
                self.addLinkExperienceRessource(experienceFk)

            self.deleteLinkExperienceMilieuDeVie(experienceFk)
            if experienceMilieuDeVieFk > 0:
                self.addLinkExperienceMilieuDeVie(experienceFk, experienceMilieuDeVieFk)

            self.deleteLinkExperienceMotCle(experienceFk)
            if experienceMotCleFk > 0:
                self.addLinkExperienceMotCle(experienceFk, experienceMotCleFk)

            self.deleteLinkExperienceTheme(experienceFk)
            if experienceThemeFk > 0:
                self.addLinkExperienceTheme(experienceFk, experienceThemeFk)

            self.deleteLinkExperiencePublic(experienceFk)
            if experiencePublicFk > 0:
                self.addLinkExperiencePublic(experienceFk, experiencePublicFk)

            self.deleteLinkExperienceClpsProprio(experienceFk)
            if experienceClpsProprioFk > 0:                             #gestion du clps proprio
                self.addLinkExperienceClpsProprio(experienceFk)


            #self.sendMailForUpdateExperience()

            #envoi d'un mail à SISS Prov BW lorsque etat experience est publie

            #if experience_etat == 'publish':
            #    etatPublicationForSiss = self.getExperienceStatutPublicationForSiss(experienceFk)
            #    if etatPublicationForSiss != True:
            #        self.setExperienceStatutPublicationForSissToTrue(experienceFk)

            return {'status': 1}
