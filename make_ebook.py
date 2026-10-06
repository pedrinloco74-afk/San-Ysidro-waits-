from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas
import re

OUT='the-human-advantage.pdf'
source=open('ebook_source.md', encoding='utf-8').read()

PAGE_W, PAGE_H = LETTER
navy=colors.HexColor('#102A43')
teal=colors.HexColor('#0F766E')
coral=colors.HexColor('#F97362')
cream=colors.HexColor('#FBF8F1')
slate=colors.HexColor('#334E68')

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='CoverTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=34, leading=38, textColor=navy, alignment=TA_LEFT, spaceAfter=14))
styles.add(ParagraphStyle(name='CoverSub', parent=styles['Normal'], fontName='Helvetica', fontSize=14, leading=20, textColor=slate, alignment=TA_LEFT))
styles.add(ParagraphStyle(name='Chapter', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=25, leading=30, textColor=navy, spaceBefore=10, spaceAfter=16, keepWithNext=True))
styles.add(ParagraphStyle(name='H2x', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=teal, spaceBefore=12, spaceAfter=6, keepWithNext=True))
styles.add(ParagraphStyle(name='Bodyx', parent=styles['BodyText'], fontName='Helvetica', fontSize=10.5, leading=16, textColor=slate, spaceAfter=9))
styles.add(ParagraphStyle(name='Bulletx', parent=styles['BodyText'], fontName='Helvetica', fontSize=10.5, leading=15, leftIndent=17, firstLineIndent=-9, textColor=slate, spaceAfter=5))
styles.add(ParagraphStyle(name='Smallx', parent=styles['BodyText'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=slate))
styles.add(ParagraphStyle(name='TOC', parent=styles['BodyText'], fontName='Helvetica', fontSize=11, leading=20, textColor=slate))

# escape while preserving basic emphasis by applying after escaping
from xml.sax.saxutils import escape
def para(text, style='Bodyx'):
    text=escape(text)
    text=re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    return Paragraph(text, styles[style])

def header_footer(canvas, doc):
    canvas.saveState()
    if doc.page>1:
        canvas.setStrokeColor(colors.HexColor('#D9E2EC')); canvas.setLineWidth(.5)
        canvas.line(.7*inch, .62*inch, PAGE_W-.7*inch, .62*inch)
        canvas.setFont('Helvetica',8); canvas.setFillColor(colors.HexColor('#627D98'))
        canvas.drawString(.7*inch, .42*inch, 'THE HUMAN ADVANTAGE')
        canvas.drawRightString(PAGE_W-.7*inch, .42*inch, str(doc.page))
    canvas.restoreState()

story=[]
# Cover
story += [Spacer(1, .85*inch), Paragraph('THE<br/>HUMAN<br/>ADVANTAGE', styles['CoverTitle']), Spacer(1,.18*inch), Paragraph('A practical guide to using AI without losing what makes you human', styles['CoverSub']), Spacer(1,2.4*inch), Paragraph('YOUR NAME', ParagraphStyle('author', parent=styles['CoverSub'], fontName='Helvetica-Bold', fontSize=12, textColor=coral)), Spacer(1,.1*inch), Paragraph('2026 EDITION', styles['Smallx']), PageBreak()]
# title page
story += [Spacer(1,1.2*inch), Paragraph('THE HUMAN ADVANTAGE', styles['Chapter']), Paragraph('A Practical Guide to Using AI Without Losing What Makes You Human', styles['CoverSub']), Spacer(1,.35*inch), Paragraph('Your Name', ParagraphStyle('author2', parent=styles['CoverSub'], fontName='Helvetica-Bold', fontSize=14, textColor=teal)), Spacer(1,3.2*inch), para('An original, accessible guide for curious people who want to work with AI while keeping their judgment, creativity, and humanity.', 'Smallx'), PageBreak()]
# copyright
story += [Paragraph('Copyright', styles['Chapter']), para('Copyright © 2026 Your Name. All rights reserved.'), para('This book is an original work created as an educational guide. It is not affiliated with, endorsed by, or derived from any other book, author, company, or technology brand. Technology changes quickly; verify important information and use your judgment.'), PageBreak()]
# parse markdown
lines=source.splitlines()
in_contents=False
for line in lines:
    if line.startswith('# THE HUMAN') or line.startswith('## A Practical') or line.startswith('**Your Name**') or line.startswith('---') or line.startswith('## Copyright'):
        continue
    if line.startswith('## Contents'):
        in_contents=True; story.append(Paragraph('Contents', styles['Chapter'])); continue
    if in_contents:
        if line.startswith('# '): in_contents=False
        elif line.strip(): story.append(para(line.replace('1. ','1. ').replace('2. ','2. ').replace('3. ','3. ').replace('4. ','4. ').replace('5. ','5. ').replace('6. ','6. ').replace('7. ','7. ').replace('8. ','8. '), 'TOC'))
        if in_contents: continue
    if line.startswith('# '):
        story += [PageBreak(), Paragraph(escape(line[2:]), styles['Chapter'])]
    elif line.startswith('## '): story.append(Paragraph(escape(line[3:]), styles['H2x']))
    elif line.startswith('- '): story.append(para('• '+line[2:], 'Bulletx'))
    elif re.match(r'^\d+\. ', line): story.append(para(line, 'Bulletx'))
    elif line.strip().startswith('> '): story.append(para(line.strip()[2:], 'Bodyx'))
    elif line.strip(): story.append(para(line.strip(), 'Bodyx'))

doc=SimpleDocTemplate(OUT, pagesize=LETTER, rightMargin=.78*inch, leftMargin=.78*inch, topMargin=.72*inch, bottomMargin=.78*inch, title='The Human Advantage', author='Your Name', subject='A practical guide to using AI without losing what makes you human')
doc.build(story, onFirstPage=lambda c,d: None, onLaterPages=header_footer)
print(OUT)
