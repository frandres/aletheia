#!/bin/bash

# exécutable en ligne de commande sous linux pour compiler le code latex correspondant au rapport du master ECD
# attention, ce code devra probablement être modifié en fonction de votre environnement de développement

bibtex report_template
latex report_template.tex
bibtex report_template
latex report_template.tex
bibtex report_template
latex report_template.tex

dvips -t a4 report_template.dvi -o report_template.ps

ps2pdf report_template.ps

