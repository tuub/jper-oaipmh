"""
Main configuration file for the application

On deployment, desired configuration can be overridden by the provision of a local.cfg file
"""

##################################################
# overrides for the webapp deployment

DEBUG = True
"""is the web server in debug mode"""

PORT = 5030
"""port to start the webserver on"""

SSL = False
"""support SSL requests"""

THREADED = True
"""is the web server in threaded mode"""

############################################
# important overrides for the ES module

# elasticsearch back-end connection settings
INITIALISE_INDEX = False
"""Shoud the ES index be initialised - in this case, there is no indexing component, so no need"""

#ELASTIC_SEARCH_HOST = "http://localhost:9200"
#ELASTIC_SEARCH_INDEX = "db"
#ELASTIC_SEARCH_VERSION = "1.4.4"

# Classes from which to retrieve ES mappings to be used in this application
ELASTIC_SEARCH_MAPPINGS = []
"""type-specific mappings to be used when initialising - currently there are none"""

############################################
# important overrides for account module

ACCOUNT_ENABLE = False
"""disable user accounts"""

SECRET_KEY = "super-secret-key"
"""secret key for session management - only used if user accounts are enabled"""

############################################
## JPER Client information

# Base URL for requests to the JPER API
JPER_BASE_URL = "https://pubrouter.jisc.ac.uk/api/v1"
"""API base url for communicating with JPER"""

# API key to use for authenticated requests against JPER API
JPER_API_KEY = ""
"""API key for making requests against JPER - not needed here, as incoming user's own API keys will be used"""


##############################################
## OAI-PMH server configuration

OAI_REPO_NAME = "Jisc Publications Router OAI-PMH Endpoint"

OAI_ADMIN_EMAIL = "admin@jisc.ac.uk"

OAI_MAX_LOOKBACK = 7776000

OAI_DC_METADATA_FORMAT = {
    "metadataPrefix": "oai_dc",
    "schema": "http://www.openarchives.org/OAI/2.0/oai_dc.xsd",
    "metadataNamespace": "http://www.openarchives.org/OAI/2.0/oai_dc/"
}

OAIPMH_METADATA_FORMATS = [
    OAI_DC_METADATA_FORMAT
]

OAIPMH_IDENTIFIER_NAMESPACE = "pubrouter.jisc.ac.uk"

OAIPMH_LIST_RECORDS_PAGE_SIZE = 100

OAIPMH_LIST_IDENTIFIERS_PAGE_SIZE = 100

OAIPMH_RESUMPTION_TOKEN_EXPIRY = 86400

OAI_CROSSWALKS = {
    "oai_dc" : "service.xwalks.OAI_DC"
}