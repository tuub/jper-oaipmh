#!/usr/bin/env bash
# In order to run this you need to have epydoc (http://epydoc.sourceforge.net/) installed, which can be done
# on Ubuntu with
#
# sudo apt-get install python-epydoc

rm docs/code/*
epydoc --html -o docs/code/ --name "Jisc Publications Router - OAI-PMH endpoint" --url https://github.com/JiscPER/jper-oaipmh --graph all --inheritance grouped --docformat restructuredtext service config
