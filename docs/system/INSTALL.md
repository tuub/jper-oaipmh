# JPER OAI-PMH Install

Clone the project:

    git clone https://github.com/JiscPER/jper-oaipmh.git

get all the submodules

    cd jper-oaipmh
    git submodule update --init --recursive

This will initialise and clone the esprit, and maginficent-octopus submodules, and all their submodules in turn.

Create your virtualenv and activate it

    virtualenv /path/to/venv
    source /path/tovenv/bin/activate

Install Esprit, Magnificent Octopus and this application in that order:

To do them all as one, use

    pip install -r requirements.txt

or to do them individually use

    cd myapp/esprit
    pip install -e .
    
    cd myapp/magnificent-octopus
    pip install -e .
    
    cd myapp
    pip install -e .
    
Create your local config

    cd myapp
    touch local.cfg

Then you can override any config values that you need to

Then, start your app with

    python service/web.py

    
