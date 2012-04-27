# -*- coding: utf-8 -*-
import re
from zope.interface import implements
from interfaces import IPdfGenerator
from zope.component import getMultiAdapter

#generer le pdf
from cStringIO import StringIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import portrait, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT

from Products.Five import BrowserView

hrefPattern = re.compile('href="([a-zA-Z_0-9\-\?\/\\:.=\+]*)"')


class PdfGenerator(BrowserView):
    implements(IPdfGenerator)

    def createStyles(self):
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='TitleLeft',
                                  alignment=TA_LEFT,
                                  textColor="#4e0022",
                                  leftIndent=0,
                                  fontName='Helvetica-Bold',
                                  fontSize=12,
                                  spaceAfter=3))
        styles.add(ParagraphStyle(name='Left',
                                  alignment=TA_JUSTIFY,
                                  textColor="#666666",
                                  leftIndent=20,
                                  rightIndent=52*mm,
                                  fontName='Helvetica',
                                  fontSize=11,
                                  spaceAfter=6,
                                  allowWidows=1,
                                  allowOrphans=0,
                                  wordWrap=1))
        styles.add(ParagraphStyle(name='LeftBulletPoint',
                                  parent=styles['Left'],
                                  leftIndent = 30,
                                  bulletIndent = 20))
        styles.add(ParagraphStyle(name='TitleRight',
                                  alignment=TA_LEFT,
                                  textColor="#333333",
                                  leftIndent=10,
                                  fontName='Helvetica',
                                  fontSize=9,
                                  bulletColor = colors.orange,
                                  bulletIndent = -3,
                                  bulletOffsetY = -1.5,
                                  bulletFontSize = 13))
        styles.add(ParagraphStyle(name='Right',
                                  alignment=TA_LEFT,
                                  textColor="#666666",
                                  leftIndent=5,
                                  fontName='Helvetica',
                                  fontSize=9,
                                  spaceAfter=6))
        styles.add(ParagraphStyle(name='RightBulletPoint',
                                  parent=styles['Right'],
                                  bulletIndent = 0,
                                  bulletOffsetY = -1.5,
                                  leftIndent = 10))
        self._styles = styles

    def cleanHtml(self, text):
        """
        Problèmes avec :
         OK <a href=".">www.clps-bw.be</a> --> ValueError: format not resolved
         OK remplacer les <li>
         OK fix class="..."
         OK fix title="..."
         OK fix internal links hrefs
        """
        text = text.strip()
        # change '.' and internal links
        text = text.replace('href="."', 'href="http://www.clps-bw.be"')
        text = text.replace('href="."', 'href="http://www.clps-bw.be"')
        hrefs = hrefPattern.findall(text)
        for href in hrefs:
            if not href.startswith('http') and not href.startswith('www'):
                text = text.replace(href, 'http://www.clps-bw.be/%s' % href)
        # remove tags classes
        text = re.sub('class="[a-zA-Z_0-9\-]*"', '', text)
        text = re.sub('title="[a-zA-Z_0-9\- ]*"', '', text)
        return text

    def makeFlowablesForBulletList(self, text):
        flow = []
        for part in re.split('<ul>|</ul>|<ol>|</ol>|<p>|</p>', text):
            part = part.strip()
            if part.count('<li>') > 0:
                for item in re.split('<li>|</li>', part):
                    item = item.strip()
                    if len(item) > 0:
                        flow.append(Paragraph(item, self._styles['LeftBulletPoint'],
                                    bulletText=u'-'))
            else:
                flow.append(Paragraph(part, self._styles['Left']))
        return flow

    def drawBackgroundAndFooter(self, canvas, doc):
        canvas.setFillColor(colors.lemonchiffon)
        canvas.setStrokeColor(colors.orange)
        canvas.setLineWidth(1)
        canvas.rect(145*mm, 25*mm, 50*mm, 247*mm, fill=True, stroke=False)
        canvas.rect(15*mm, 25*mm, 180*mm, 247*mm, fill=False)

        canvas.setStrokeColor(colors.black)
        canvas.setFillColor(colors.black)
        canvas.setLineWidth(0.40)
        canvas.line(20*mm, 12*mm, 190*mm, 12*mm)
        canvas.setFont('Helvetica', 8)
        canvas.drawString(20*mm, 8*mm, "Projets partagés : CLPS-Bw - CLPS-Lux        www.projets-partages.be")
        canvas.drawString(180*mm, 8*mm, "Page %d" % doc.page)

    def drawExperienceRightColumn(self, canvas, doc):
        clpsView = getMultiAdapter((self.context, self.request), name="manageInterClps")
        #colonne de droite
        institutionPorteur = ""
        institutionPorteurs = clpsView.getInstitutionPorteur(self._pdfdata.experience_pk)
        for i in institutionPorteurs:
            institutionPorteur = institutionPorteur + '%s<br />' % i.institution_porteur.institution_nom.strip()

        institutionPartenaire = ""
        institutionPartenaires = clpsView.getInstitutionPartenaire(self._pdfdata.experience_pk)
        for i in institutionPartenaires:
            institutionPartenaire = (institutionPartenaire + '- %s <br />')%(i.institution_partenaire.institution_nom, )

        institutionRessource = ""
        institutionRessources = clpsView.getInstitutionRessource(self._pdfdata.experience_pk)
        for i in institutionRessources:
            institutionRessource = (institutionRessource + '- %s <br />')%(i.institution_ressource.institution_nom, )

        periodeDeroulement = self._pdfdata.experience_periode_deroulement

        territoire=""
        brabantWallon = self._pdfdata.experience_territoire_tout_brabant_wallon
        if brabantWallon:
            territoire="%s<br />"%("Tout le Brabant Wallon", )
        communes = clpsView.getCommuneNomByExperiencePk(self._pdfdata.experience_pk)
        for i in communes:
            territoire = (territoire + '- %s <br />')%(i, )

        outil = ""
        outils = clpsView.getRessourceByExperiencePk(self._pdfdata.experience_pk)
        for i in outils:
            if len(i[1])>0:
                outil = ('%s ')%(i[1],)

        autreOutil = ('%s')%(self._pdfdata.experience_institution_outil_autre)
        if autreOutil:
            outil = ('%s<br /><li>%s</li>')%(outil, autreOutil)

        formation = ('%s')%(self._pdfdata.experience_formation_suivie)

        nomContact = ('%s')%(self._pdfdata.experience_personne_contact)
        emailContact = ('%s')%(self._pdfdata.experience_personne_contact_email)
        telephoneContact = ('%s')%(self._pdfdata.experience_personne_contact_telephone)
        contact = ('%s<br />%s<br />%s')%(nomContact, emailContact, telephoneContact)

        rightFields = [("Institution porteur(s) de l'expérience", institutionPorteur),
                       ("Institution partenaire(s) de l'expérience", institutionPartenaire),
                       ("Institution ressource(s) de l'expérience", institutionRessource),
                       ("Période de déroulement", periodeDeroulement),
                       ("Territoire", territoire),
                       ("Outils", outil),
                       ("Formations", formation),
                       ("Contacts", contact)
                       ]

        self.overflowFields = []
        offset = 0
        for field in rightFields:
            if not field[1]:
                continue
            if self.overflowFields:
                self.overflowFields.append(field)
                continue
            title = Paragraph(field[0], self._styles["TitleRight"], bulletText='•')
            text = Paragraph(self.cleanHtml(field[1]), self._styles["Right"])
            w, h = title.wrapOn(canvas, 45*mm, 0*mm)
            w2, h2 = text.wrapOn(canvas, 45*mm, 0*mm)
            if w2 > 45*mm:
                # XXX force crop ?
                pass
            if offset + h + h2 > 689:
                self.overflowFields.append(field)
                continue
            offset += h
            title.drawOn(canvas, 148*mm, 760-offset)
            offset += h2
            text.drawOn(canvas, 148*mm, 760-offset)
            offset += 15

    def drawInstitutionRightColumn(self, canvas, doc):
        clpsView = getMultiAdapter((self.context, self.request), name="manageInterClps")
        #colonne de droite
        sigle = self._pdfdata.institution_sigle
        adresse = self._pdfdata.institution_adresse
        localite = ('%s %s')%(self._pdfdata.commune.com_localite_cp, self._pdfdata.commune.com_localite_nom)
        personneRessource = self._pdfdata.institution_nom_contact
        fonction = self._pdfdata.institution_fonction_contact
        email = self._pdfdata.institution_email_contact
        tel = self._pdfdata.institution_tel_contact

        #cadre projet partage
        projet = ""

        projetsPorteurs = clpsView.getExperienceFromInstitutionPorteur(self._pdfdata.institution_pk)
        for elem in projetsPorteurs:
            projet = projet + '%s<br />' % elem[1].strip()

        projetsPartages = clpsView.getExperienceFromInstitutionPartenaire(self._pdfdata.institution_pk)
        for elem in projetsPartages:
            projet = projet + '%s<br />' % elem[1].strip()

        projetsRessources = clpsView.getExperienceFromInstitutionRessource(self._pdfdata.institution_pk)
        for elem in projetsRessources:
            projet = projet + '%s<br />' % elem[1].strip()

        rightFields = [("Sigle", sigle),
                       ("Adresse", adresse),
                       ("Localité", localite),
                       ("Personne ressource", personneRessource),
                       ("Fonction", fonction),
                       ("E-mail", email),
                       ("Tél", tel),
                       ("Projets", projet),
                       ]

        self.overflowFields = []
        offset = 0
        for field in rightFields:
            if not field[1]:
                continue
            if self.overflowFields:
                self.overflowFields.append(field)
                continue
            title = Paragraph(field[0], self._styles["TitleRight"], bulletText='•')
            text = Paragraph(self.cleanHtml(field[1]), self._styles["Right"])
            w, h = title.wrapOn(canvas, 45*mm, 0*mm)
            w2, h2 = text.wrapOn(canvas, 45*mm, 0*mm)
            if w2 > 45*mm:
                # XXX force crop ?
                pass
            if offset + h + h2 > 689:
                self.overflowFields.append(field)
                continue
            offset += h
            title.drawOn(canvas, 148*mm, 760-offset)
            offset += h2
            text.drawOn(canvas, 148*mm, 760-offset)
            offset += 15

    def drawOverflowedFields(self, canvas, doc):
        offset = 0
        for field in self.overflowFields:
            title = Paragraph(field[0], self._styles["TitleRight"], bulletText='•')
            text = Paragraph(self.cleanHtml(field[1]), self._styles["Right"])
            w, h = title.wrapOn(canvas, 45*mm, 0*mm)
            w2, h2 = text.wrapOn(canvas, 45*mm, 0*mm)
            if w2 > 45*mm:
                # XXX force crop ?
                pass
            offset += h
            title.drawOn(canvas, 148*mm, 760-offset)
            offset += h2
            text.drawOn(canvas, 148*mm, 760-offset)
            offset += 15
        self.overflowFields = []

    def drawFirstPage(self, canvas, doc):
        canvas.saveState()
        self.drawBackgroundAndFooter(canvas, doc)
        titleStyle = self._styles["Title"]
        titleStyle.textColor = colors.HexColor(0x820031)
        titreTxt = self._pdfdata.titre
        titre = Paragraph('<b><i>%s</i></b>' % titreTxt, titleStyle)
        w, h = titre.wrapOn(canvas, 145*mm, 25*mm)
        titre.drawOn(canvas, (600/2-w/2), 280*mm)
        if self._pdftype == 'experience':
            self.drawExperienceRightColumn(canvas, doc)
        else:
            self.drawInstitutionRightColumn(canvas, doc)
        # 210 × 297
        canvas.restoreState()

    def drawLaterPage(self, canvas, doc):
        canvas.saveState()
        self.drawBackgroundAndFooter(canvas, doc)
        if self.overflowFields:
            self.drawOverflowedFields(canvas, doc)
        canvas.restoreState()

    def printExperience(self, experiencePk):
        """
        genere le pdf d'une experience selon sa pk
        """
        self.createStyles()
        clpsView = getMultiAdapter((self.context, self.request), name="manageInterClps")
        pdfFile = StringIO()  # ecrit dans un buffer comme un fichier

        doc = SimpleDocTemplate(pdfFile,
                                pagesize=portrait(A4),
                                bottomMargin=25*mm,
                                topMargin=25*mm,
                                leftMargin=15*mm,
                                rightMargin=15*mm,
                                allowSplitting=1)

        story = []
        experiences = clpsView.getExperienceByPk(experiencePk, experienceEtat=None)
        if not experiences:
            return
        self._pdftype = 'experience'
        self._pdfdata = experiences[0]
        self._pdfdata.titre = self._pdfdata.experience_titre

        #colonne de gauche
        resume = self._pdfdata.experience_resume
        contexte = self._pdfdata.experience_element_contexte
        objectif = self._pdfdata.experience_objectif
        public = self._pdfdata.experience_public_vise
        milieux = clpsView.getMilieuDeVieByExperiencePk(self._pdfdata.experience_pk, 'nom')
        milieu = milieux[0]
        demarche = ('%s')%(self._pdfdata.experience_demarche_actions)
        moyen = ('%s')%(self._pdfdata.experience_moyens)
        evaluation = ('%s')%(self._pdfdata.experience_evaluation_enseignement)
        perspective = ('%s')%(self._pdfdata.experience_perspective_envisagee)

        leftFields = [("Résumé", resume),
                      ("Eléments de contexte", contexte),
                      ("Objectifs", objectif),
                      ("Public", public),
                      ("Milieu de vie", milieu),
                      ("Démarches et actions", demarche),
                      ("Moyens", moyen),
                      ("Evaluation et enseignement", evaluation),
                      ("Prespectives envisagées", perspective)
                     ]

        for field in leftFields:
            if not field[1]:
                continue
            title = Paragraph("&bull; &nbsp;%s" % field[0], self._styles["TitleLeft"])
            story.append(title)
            paragraphs = self.makeFlowablesForBulletList(self.cleanHtml(field[1]))
            for p in paragraphs:
                story.append(p)
            story.append(Spacer(1, 12))

        doc.build(story, onFirstPage=self.drawFirstPage, onLaterPages=self.drawLaterPage)

        self.request.response.setHeader('Content-Type', 'application/pdf')
        self.request.response.addHeader("Content-Disposition", "filename=experience.pdf")
        return pdfFile.getvalue()

    def printInstitution(self, institutionPk):
        """
        genere le pdf d'une institution selon sa pk
        """
        self.createStyles()
        clpsView = getMultiAdapter((self.context, self.request), name="manageInterClps")
        pdfFile = StringIO()  # ecrit dans un buffer comme un fichier

        doc = SimpleDocTemplate(pdfFile,
                                pagesize=portrait(A4),
                                bottomMargin=25*mm,
                                topMargin=25*mm,
                                leftMargin=15*mm,
                                rightMargin=15*mm,
                                allowSplitting=1)

        story = []
        institutions = clpsView.getInstitutionByPk(institutionPk)
        if not institutions:
            return
        self._pdftype = 'institution'
        self._pdfdata = institutions[0]
        self._pdfdata.titre = self._pdfdata.institution_nom

        #colonne de gauche
        public = self._pdfdata.institution_public
        mission = self._pdfdata.institution_mission

        territoire = ""
        communes = clpsView.getInstitutionCommuneCouverte(institutionPk)
        for i in communes:
            territoire = (territoire + '- %s <br />')%(i, )

        activite = self._pdfdata.institution_activite
        commentaire = self._pdfdata.institution_commentaire
        siteWeb = self._pdfdata.institution_url_site
        autreInfo = self._pdfdata.institution_autre_info

        leftFields = [("Public", public),
                      ("Missions", mission),
                      ("Territoire couvert par l'institution", territoire),
                      ("Activités", activite),
                      ("Commentaires", commentaire),
                      ("Site web", siteWeb),
                      ("Autre info", autreInfo)
                     ]

        for field in leftFields:
            if not field[1]:
                continue
            title = Paragraph("&bull; &nbsp;%s" % field[0], self._styles["TitleLeft"])
            story.append(title)
            paragraphs = self.makeFlowablesForBulletList(self.cleanHtml(field[1]))
            for p in paragraphs:
                story.append(p)
            story.append(Spacer(1, 12))

        doc.build(story, onFirstPage=self.drawFirstPage, onLaterPages=self.drawLaterPage)

        self.request.response.setHeader('Content-Type', 'application/pdf')
        self.request.response.addHeader("Content-Disposition", "filename=institution.pdf")
        return pdfFile.getvalue()
