# -*- coding: utf-8 -*-
import re
from zope.interface import implements
from interfaces import IPdfGenerator
from zope.component import getMultiAdapter

#generer le pdf
from cStringIO import StringIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, \
                               TableStyle
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
        for part in re.split('<ul>|</ul>|<ol>|</ol>', text):
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

    def drawRightColumn(self, canvas, doc):
        clpsView = getMultiAdapter((self.context, self.request), name="manageInterClps")
        #colonne de droite
        institutionPorteur = ""
        institutionPorteurs = clpsView.getInstitutionPorteur(self._experience.experience_pk)
        for i in institutionPorteurs:
            institutionPorteur = institutionPorteur + '%s<br />' % i.institution_porteur.institution_nom.strip()

        institutionPartenaire = ""
        institutionPartenaires = clpsView.getInstitutionPartenaire(self._experience.experience_pk)
        for i in institutionPartenaires:
            institutionPartenaire = (institutionPartenaire + '- %s <br />')%(i.institution_partenaire.institution_nom, )

        institutionRessource = ""
        institutionRessources = clpsView.getInstitutionRessource(self._experience.experience_pk)
        for i in institutionRessources:
            institutionRessource = (institutionRessource + '- %s <br />')%(i.institution_ressource.institution_nom, )

        periodeDeroulement = self._experience.experience_periode_deroulement

        territoire=""
        brabantWallon = self._experience.experience_territoire_tout_brabant_wallon
        if brabantWallon:
            territoire="%s<br />"%("Tout le Brabant Wallon", )
        communes = clpsView.getCommuneNomByExperiencePk(self._experience.experience_pk)
        for i in communes:
            territoire = (territoire + '- %s <br />')%(i, )

        outil = ""
        outils = clpsView.getRessourceByExperiencePk(self._experience.experience_pk)
        for i in outils:
            if len(i[1])>0:
                outil = ('%s ')%(i[1],)

        autreOutil = ('%s')%(self._experience.experience_institution_outil_autre)
        if autreOutil:
            outil = ('%s<br /><li>%s</li>')%(outil, autreOutil)

        formation = ('%s')%(self._experience.experience_formation_suivie)

        nomContact = ('%s')%(self._experience.experience_personne_contact)
        emailContact = ('%s')%(self._experience.experience_personne_contact_email)
        telephoneContact = ('%s')%(self._experience.experience_personne_contact_telephone)
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
        titreTxt = self._experience.experience_titre
        titre = Paragraph('<b><i>%s</i></b>' % titreTxt, titleStyle)
        w, h = titre.wrapOn(canvas, 145*mm, 25*mm)
        titre.drawOn(canvas, (600/2-w/2), 280*mm)
        self.drawRightColumn(canvas, doc)
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
        self._experience = experiences[0]

        #colonne de gauche
        resume = self._experience.experience_resume
        contexte = self._experience.experience_element_contexte
        objectif = self._experience.experience_objectif
        public = self._experience.experience_public_vise
        milieux = clpsView.getMilieuDeVieByExperiencePk(self._experience.experience_pk, 'nom')
        milieu = milieux[0]
        demarche = ('%s')%(self._experience.experience_demarche_actions)
        moyen = ('%s')%(self._experience.experience_moyens)
        evalautaion = ('%s')%(self._experience.experience_evaluation_enseignement)
        perspective = ('%s')%(self._experience.experience_perspective_envisagee)

        leftFields = [("Résumé", resume),
                      ("Eléments de contexte", contexte),
                      ("Objectifs", objectif),
                      ("Public", public),
                      ("Milieu de vie", milieu),
                      ("Démarches et actions", demarche),
                      ("Moyens", moyen),
                      ("Evaluation et enseignement", evalautaion),
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
        clpsView = getMultiAdapter((self.context, self.request), name="manageInterClps")
        pdfFile = StringIO() #ecrit dans un buffer comme un fichier
        doc = SimpleDocTemplate(pdfFile,
                                pagesize = portrait(A4),
                                bottomMargin = 10*mm,
                                topMargin = 10*mm,
                                leftMargin = 15*mm,
                                rightMargin = 15*mm)
        story = []
        data =[]
        institutions = clpsView.getInstitutionByPk(institutionPk)

        for institution in institutions:
            #colonne de gauche
            nom = institution.institution_nom
            public = institution.institution_public
            mission = institution.institution_mission

            territoire = ""
            communes = clpsView.getInstitutionCommuneCouverte(institutionPk)
            for i in communes:
                territoire = (territoire + '- %s <br />')%(i, )

            activite = institution.institution_activite
            commentaire = institution.institution_commentaire
            siteWeb = institution.institution_url_site
            lienSiss = institution.institution_lien_siss
            autreInfo = institution.institution_autre_info

            #colonne de droite
            sigle = institution.institution_sigle
            adresse = institution.institution_adresse
            localite = ('%s %s')%(institution.commune.com_localite_cp, institution.commune.com_localite_nom)
            personneRessource = institution.institution_nom_contact
            fonction = institution.institution_fonction_contact
            email = institution.institution_email_contact
            tel = institution.institution_tel_contact

            #cadre projet partage
            projetsPorteurs = clpsView.getExperienceFromInstitutionPorteur(institutionPk)
            projet = ""
            for elem in projetsPorteurs:
                projet = (projet + "&bull; %s <br />")%(elem[1], )

            projetsPartages = clpsView.getExperienceFromInstitutionPartenaire(institutionPk)
            projet = ""
            for elem in projetsPartages:
                projet = (projet + "&bull; %s <br />")%(elem[1], )

            projetsRessources = clpsView.getExperienceFromInstitutionRessource(institutionPk)
            projet = ""
            for elem in projetsRessources:
                projet = (projet + "&bull; %s <br />")%(elem[1], )

            #cadre assuetude
            intervention =""
            interventions = clpsView.getAssuetudeInterventionForInstituion(institutionPk, 'nom')
            for elem in interventions:
                intervention = (intervention + "&bull; %s <br />")%(elem, )

            activiteProposee = ""
            activiteProposees = clpsView.getAssuetudeActiviteProposeePublicForInstituion(institutionPk, 'nom')
            for elem in activiteProposees:
                activiteProposee = (activiteProposee + "&bull; %s <br />")%(elem, )
            precisionActiviteProposee = institution.institution_assuet_activite_proposee_precision

            thematique = ""
            thematiques = clpsView.getAssuetudeThematiqueForInstituion(institutionPk, 'nom')
            for elem in thematiques:
                thematique = (thematique + "&bull; %s <br />")%(elem, )
            precisionThematique = institution.institution_assuet_thematique_precision

        leftFields = [("Public", public),
                      ("Missions", mission),
                      ("Territoire couvert par l'institution", territoire),
                      ("Activités", activite),
                      ("Commentaires", commentaire),
                      ("Site web", siteWeb),
                      ("Lien SISS", lienSiss),
                      ("Autre info", autreInfo)
                     ]
        rightFields = [("Sigle", sigle),
                       ("Adresse", adresse),
                       ("Localité", localite),
                       ("Personne ressource", personneRessource),
                       ("Fonction", fonction),
                       ("E-mail", email),
                       ("Tél", tel),
                       ]
        assuetudeFields = [("Intervention", intervention),
                           ("Activités proposées", activiteProposee),
                           ("Précision sur les activités proposées", precisionActiviteProposee),
                           ("Thématique", thematique),
                           ("Précision sur les thématiques", precisionThematique),
                           ("Précision", precisionThematique),
                          ]

        leftColumn = []
        rightColumn = []
        assuetude = []

        styles=getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        styles.add(ParagraphStyle(name='TitleLeft',
                                  alignment=TA_LEFT,
                                  textColor="#4e0022",
                                  leftIndent=0,
                                  fontName='Helvetica-Bold',
                                  fontSize=12,
                                  spaceAfter=3))
        styles.add(ParagraphStyle(name='Left',
                                  alignment=TA_LEFT,
                                  textColor="#666666",
                                  leftIndent=20,
                                  fontName='Helvetica',
                                  fontSize=11,
                                  spaceAfter=6))
        styles.add(ParagraphStyle(name='TitleRight',
                                  alignment=TA_LEFT,
                                  textColor="#333333",
                                  leftIndent=0,
                                  fontName='Helvetica',
                                  fontSize=9))
        styles.add(ParagraphStyle(name='Right',
                                  alignment=TA_LEFT,
                                  textColor="#666666",
                                  leftIndent=5,
                                  fontName='Helvetica',
                                  fontSize=9,
                                  spaceAfter=6))

        titleStyle = styles["Title"]
        titleStyle.textColor = colors.HexColor(0x007bdd)
        story.append(Paragraph(nom, titleStyle))
        story.append(Spacer(1, 12))

        data = [[leftColumn, rightColumn],]
        for field in leftFields:
            if field[1]:
                title = Paragraph("&bull; %s" % field[0], styles["TitleLeft"])
                text = Paragraph(field[1], styles["Left"])
                leftColumn.append(title)
                leftColumn.append(text)

        for field in rightFields:
            if field[1]:
                title = Paragraph("&bull; %s" % field[0], styles["TitleRight"])
                text = Paragraph(field[1], styles["Right"])
                rightColumn.append(title)
                rightColumn.append(text)

        t=Table(data, colWidths=[130*mm, 50*mm])
        t.setStyle(TableStyle([('BOX', (0,0), (1,-1), 1 ,colors.HexColor(0x007bdd)),
                               #('LINEABOVE', (0,0), (-1,0), 2, colors.orange),
                               #('LINEBELOW', (0,-1), (-1,-1), 2, colors.orange),
                               ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
                               ('VALIGN', (0,0), (-1,0), 'TOP'),
                               ('BACKGROUND', (-1,0), (-1,0), colors.HexColor(0xedffff)),
                               ('BACKGROUND', (-1,0), (0,0), colors.grey),
                              ]))

        story.append(t)
        story.append(Spacer(1, 12))

        blocAssuetude = [[assuetude]]

        assuetude.append(Paragraph("ASSUETUDE", styles["TitleRight"]))

        for field in assuetudeFields:
            if field[1]:
                title = Paragraph("&bull; %s" % field[0], styles["TitleLeft"])
                text = Paragraph(field[1], styles["Left"])
                assuetude.append(title)
                assuetude.append(text) 
        t01 = Table(blocAssuetude, colWidths=[160*mm,])
        t01.setStyle(TableStyle([('BOX', (0,0), (1,-1), 1 ,colors.HexColor(0x007bdd)),
                                #('LINEABOVE', (0,0), (-1,0), 2, colors.orange),
                                #('LINEBELOW', (0,-1), (-1,-1), 2, colors.orange),
                                ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
                                ('VALIGN', (0,0), (-1,0), 'TOP'),
                                ('BACKGROUND', (-1,0), (-1,0), colors.HexColor(0xedffff)),
                                ('BACKGROUND', (-1,0), (0,0), colors.HexColor(0xdfe5ff)),
                               ]))
        story.append(t01)

        doc.build(story, onFirstPage=self.drawFooter, onLaterPages=self.drawFooter)

        self.request.response.setHeader('Content-Type', 'application/pdf')
        self.request.response.addHeader("Content-Disposition", "filename=experience.pdf")
        return pdfFile.getvalue()
