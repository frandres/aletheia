#!/bin/bash

# exécutable en ligne de commande sous linux pour compiler le code latex correspondant au rapport du master ECD
# attention, ce code devra probablement être modifié en fonction de votre environnement de développement

pdflatex francisco_rodriguez_drumond_mastes-thesis.tex
bibtex francisco_rodriguez_drumond_mastes-thesis
pdflatex francisco_rodriguez_drumond_mastes-thesis.tex
pdflatex francisco_rodriguez_drumond_mastes-thesis.tex

