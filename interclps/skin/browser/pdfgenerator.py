# -*- coding: utf-8 -*-
from zope.interface import implements
from interfaces import IPdfGenerator
from zope.component import getMultiAdapter

#generer le pdf
from cStringIO import StringIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import portrait, A4 
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from Products.Five import BrowserView


class PdfGenerator(BrowserView):
    implements(IPdfGenerator)


    def drawFooter(self, canvas, doc):
        canvas.saveState()
        canvas.setLineWidth(0.40)
        canvas.line(20*mm,12*mm, 190*mm,12*mm)
        canvas.setFont('Helvetica', 8)
        canvas.drawString(20*mm, 8*mm, "CLPS-Bw - Projets partagés")
        canvas.drawString(180*mm, 8*mm, "Page %d" % doc.page)
        canvas.restoreState()

    def printExperience(self, experiencePk):
        """
        genere le pdf d'une experience selon sa pk
        """
        clpsView = getMultiAdapter((self.context, self.request), name="manageInterClpsbw")
        pdfFile = StringIO() #ecrit dans un buffer comme un fichier
        doc = SimpleDocTemplate(pdfFile,
                                pagesize = portrait(A4),
                                bottomMargin = 10*mm,
                                topMargin = 10*mm,
                                leftMargin = 15*mm,
                                rightMargin = 15*mm)
        story = []
        experiences = clpsView.getExperienceByPk(experiencePk, experienceEtat=None)

        for experience in experiences:
            #colonne de gauche
            titre = experience.experience_titre
            resume = experience.experience_resume
            contexte = experience.experience_element_contexte
            objectif = experience.experience_objectif
            public = experience.experience_public_vise
            #milieu = 'Milieu de vie'
            #demarche = ('%s')%(experience.experience_demarche_actions)
            #moyen = ('%s')%(experience.experience_moyens)

            #colonne de droite
            periodeDeroulement = experience.experience_periode_deroulement
            #brabantWallon = experience.experience_territoire_tout_luxembourg
            #communes = self.getCommuneNomByExperiencePk(experience.experience_pk)
            #outils = self.getRessourceByExperiencePk(experience.experience_pk)
            #autreOutil = ('%s')%(experience.experience_institution_outil_autre)
            #formation = ('%s')%(experience.experience_formation_suivie)
            #nomContact = ('%s')%(experience.experience_personne_contact)
            #emailContact = ('%s')%(experience.experience_personne_contact_email)
            #telephoneContact = ('%s')%(experience.experience_personne_contact_telephone)

        styles=getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

        titleStyle = styles["Title"]
        titleStyle.textColor = colors.HexColor(0x820031)
        story.append(Paragraph(titre, titleStyle))
        story.append(Spacer(1, 12))

        data = [[Paragraph("Résumé", styles["Heading3"]), Paragraph("Institution porteur(s) de l'expérience", styles["Heading3"])],
                [Paragraph(resume, styles["Justify"]), Paragraph("institution porteur(s) de lexpérience", styles["Justify"])],
                
                [Paragraph("Eléments de contexte", styles["Heading3"]), Paragraph("Institution partenaire(s) de l'expérience", styles["Heading3"])],
                [Paragraph(contexte, styles["Justify"]), Paragraph("Institution partenaire(s) de l'expérience", styles["Justify"])],
               
                [Paragraph("Objectifs", styles["Heading3"]), Paragraph("Institution ressource(s) de l'expérience", styles["Heading3"])],
                [Paragraph(objectif, styles["Justify"]), Paragraph("Institution ressource(s) de l'expérience", styles["Justify"])],
               
                [Paragraph("Public", styles["Heading3"]), Paragraph("Période de déroulement", styles["Heading3"])],
                [Paragraph(public, styles["Justify"]), Paragraph(periodeDeroulement, styles["Justify"])],
               
                [Paragraph("Milieu de vie", styles["Heading3"]), Paragraph("Territoire", styles["Heading3"])],]
                #[Paragraph(milieu, styles["Justify"]), Paragraph(brabantWallon, styles["Justify"])],
               
                #[Paragraph("Démarches et actions", styles["Heading3"]), Paragraph("Outils", styles["Heading3"])],
                #[Paragraph(demarche, styles["Justify"]), Paragraph(outils, styles["Justify"])],
               
                #[Paragraph("Moyens", styles["Heading3"]), Paragraph("Formations", styles["Heading3"])],
                #[Paragraph(moyen, styles["Justify"]), Paragraph(formation, styles["Justify"])],
               
                #[Paragraph("x"), Paragraph("Formations", styles["Heading3"])],
                #[Paragraph("x"), Paragraph(nomContact, styles["Justify"])],
                #[Paragraph("x"), Paragraph(emailContact, styles["Justify"])],
                #[Paragraph("x"), Paragraph(telephoneContact, styles["Justify"])]
        #      ]
        
        t=Table(data, colWidths=[130*mm, 50*mm])
        t.setStyle(TableStyle([('LINEABOVE', (0,0), (-1,0), 2, colors.orange),
                               ('LINEBELOW', (0,-1), (-1,-1), 2, colors.orange),
                               ('BOX', (0,0), (1,-1), 1 ,colors.orange),
                               ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
                               ('VALIGN', (1,1), (-1,-1), 'TOP'),
                               ('BACKGROUND', (2,0), (-2,-1), colors.lemonchiffon),
                               ('BACKGROUND', (1,0), (-2,-1), colors.black),
                               ]))

        story.append(t)
        doc.build(story, onFirstPage=self.drawFooter, onLaterPages=self.drawFooter)

        self.request.response.setHeader('Content-Type', 'application/pdf')
        self.request.response.addHeader("Content-Disposition", "filename=experience.pdf")
        return pdfFile.getvalue()
