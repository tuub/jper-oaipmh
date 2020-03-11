"""
Blueprint that provides the web routes for the OAI endpoint for:

* The entire set of routed notifications
* The routed notifications for a specific repository
"""

from lxml import etree
from datetime import datetime, timedelta
from flask import Blueprint, request, make_response
from octopus.core import app
from service.models import OAIPMHAll, OAIPMHRepo
from octopus.lib import plugin
from service import oaitools

blueprint = Blueprint('oaipmh', __name__)

#####################################################################
## Web API endpoints
#####################################################################

@blueprint.route("/all", methods=["GET", "POST"])
@blueprint.route("/repo/<repository_id>", methods=["GET", "POST"])
def oaipmh(repository_id=None):
    """
    main web route for oai-pmh.  If the request is to /all this will be called
    with repository_id=None, otherwise, the repository_id will be taken from the url
    path

    :param repository_id: the repository account id in JPER for whom to provide the feed
    :return:
    """
    # work out which endpoint we're going to
    dao = None
    if repository_id is None:
        dao = OAIPMHAll()
    else:
        dao = OAIPMHRepo(repository_id)
    
    # work out the verb and associated parameters
    verb = request.values.get("verb")

    app.logger.info("Received request for Verb:{x} against Repository:{y}".format(x=verb, y=repository_id if repository_id is not None else "All"))

    # call the appropriate protocol operation
    result = None
    
    # if no verb supplied
    if verb is None:
        result = BadVerb(request.base_url)
    
    # Identify
    elif verb.lower() == "identify":
        result = identify(dao, request.base_url)
    
    # ListMetadataFormats
    elif verb.lower() == "listmetadataformats":
        params = list_metadata_formats_params(request)
        result = list_metadata_formats(dao, request.base_url, **params)
    
    # GetRecord
    elif verb.lower() == "getrecord":
        params = get_record_params(request)
        result = get_record(dao, request.base_url, **params)
    
    # ListSets
    elif verb.lower() == "listsets":
        params = list_sets_params(request)
        result = list_sets(dao, request.base_url, **params)
    
    # ListRecords
    elif verb.lower() == "listrecords":
        params = list_records_params(request)
        result = list_records(dao, request.base_url, **params)
    
    # ListIdentifiers
    elif verb.lower() == "listidentifiers":
        params = list_identifiers_params(request)
        result = list_identifiers(dao, request.base_url, **params)
    
    # A verb we didn't understand
    else:
        result = BadVerb(request.base_url)
    
    # serialise and return
    resp = make_response(result.serialise())
    resp.mimetype = "text/xml"
    return resp

#####################################################################
## Utility methods/objects
#####################################################################

def get_crosswalk(prefix):
    """
    Load an instance of the appropriate crosswalk object for the supplied metadataPrefix

    :param prefix: the metadataPrefix from the request
    :return: an instance of the crosswalk object
    """
    kn = app.config.get("OAI_CROSSWALKS", {}).get(prefix)
    if kn is not None:
        return plugin.load_class(kn)()
    return None

def list_metadata_formats_params(req):
    """
    Extract the appropriate request parameters for a ListMetadataFormats request

    :param req: flask request object
    :return: a dictionary of parameters
    """
    identifier = req.values.get("identifier")
    if identifier is not None:
        identifier = oaitools.extract_internal_id(identifier)
    return {"identifier" : identifier}

def get_record_params(req):
    """
    Extract the appropriate request parameters for a GetRecord request

    :param req: flask request object
    :return: a dictionary of parameters
    """
    identifier = req.values.get("identifier")
    metadata_prefix = req.values.get("metadataPrefix")
    if identifier is not None:
        identifier = oaitools.extract_internal_id(identifier)
    return {"identifier" : identifier, "metadata_prefix" : metadata_prefix}

def list_sets_params(req):
    """
    Extract the appropriate request parameters for a ListSets request

    :param req: flask request object
    :return: a dictionary of parameters
    """
    resumption = req.values.get("resumptionToken")
    return {"resumption_token" : resumption}

def list_records_params(req):
    """
    Extract the appropriate request parameters for a ListRecords request

    :param req: flask request object
    :return: a dictionary of parameters
    """
    from_date = req.values.get("from")
    until_date = req.values.get("until")
    oai_set = req.values.get("set")
    resumption_token = req.values.get("resumptionToken")
    metadata_prefix = req.values.get("metadataPrefix")
    return {
        "from_date" : from_date,
        "until_date" : until_date,
        "oai_set" : oai_set,
        "resumption_token" : resumption_token,
        "metadata_prefix" : metadata_prefix
    }

def list_identifiers_params(req):
    """
    Extract the appropriate request parameters for a ListIdentifiers request

    :param req: flask request object
    :return: a dictionary of parameters
    """
    from_date = req.values.get("from")
    until_date = req.values.get("until")
    oai_set = req.values.get("set")
    resumption_token = req.values.get("resumptionToken")
    metadata_prefix = req.values.get("metadataPrefix")
    return {
        "from_date" : from_date,
        "until_date" : until_date,
        "oai_set" : oai_set,
        "resumption_token" : resumption_token,
        "metadata_prefix" : metadata_prefix
    }

#####################################################################
## OAI-PMH protocol operations implemented
#####################################################################

def identify(dao, base_url):
    """
    Action a request to Identify

    :param dao: OAIPMHRecord implementation object to back the request
    :param base_url: base url of the service
    :return: An Identify object which can be serialised and returned
    """
    app.logger.info("Processing Identify request")

    repo_name = app.config.get("OAI_REPO_NAME")
    admin_email = app.config.get("OAI_ADMIN_EMAIL")
    idobj = Identify(base_url, repo_name, admin_email)
    idobj.earliest_datestamp = dao.earliest_datestamp()
    return idobj

def list_sets(dao, base_url, resumption_token=None):
    """
    Action a request to ListSets

    :param dao: OAIPMHRecord implementation object to back the request
    :param base_url: base url of the service
    :param resumption_token: resumption token for paging - not supported or necessary in this version
    :return: a ListSets object which can be serialised and returned
    """
    app.logger.info("Processing ListSets request")

    # This implementation does not support resumption tokens for this operation
    if resumption_token is not None:
        app.logger.debug("Resumption token supplied to ListSets - unsupported operation")
        return BadResumptionToken(base_url)

    # just ask the DAO to get a list of all the sets for us, then we
    # give the set spec and set name as the same string
    ls = ListSets(base_url)
    sets = dao.list_sets()
    for s in sets:
        ls.add_set(oaitools.make_set_spec(s), s)
    return ls

def list_metadata_formats(dao, base_url, identifier=None):
    """
    Action a request to ListMetadataFormats

    :param dao: OAIPMHRecord implementation object to back the request
    :param base_url:  base url of the service
    :param identifier: The record identifier for which we want to know the metadata formats
    :return: a ListMetadataFormats object which can be serialised and returned
    """
    app.logger.info("Processing ListMetadataFormats request for Notification:{x}".format(x=identifier))

    # if we are given an identifier, it has to be valid
    if identifier is not None:
        if not dao.identifier_exists(identifier):
            app.logger.debug("Notification:{x} does not exist - bad request".format(x=identifier))
            return IdDoesNotExist(base_url)

    # get the configured formats - there should always be some, but just in case
    # the service is mis-configured, this will throw the correct error
    formats = app.config.get("OAIPMH_METADATA_FORMATS", [])
    if formats is None or len(formats) == 0:
        app.logger.error("No Metadata Formats configured - you should fix this in configuration")
        return NoMetadataFormats(base_url)

    # create and return the list metadata formats response
    oai_id = None
    if identifier is not None:
        oai_id = oaitools.make_oai_identifier(identifier, "notification")
    lmf = ListMetadataFormats(base_url=base_url, identifier=oai_id)
    for f in formats:
        lmf.add_format(f.get("metadataPrefix"), f.get("schema"), f.get("metadataNamespace"))
    return lmf

def list_records(dao, base_url, metadata_prefix=None, from_date=None, until_date=None, oai_set=None, resumption_token=None):
    """
    Actions a request to ListRecords

    If resumption_token is provided, all other parameters must be left as None.

    :param dao: OAIPMHRecord implementation object to back the request
    :param base_url: base url of the service
    :param metadata_prefix: The metadata prefix for the format requested
    :param from_date: The earliest date from which to harvest
    :param until_date: The latest date until which to harvest
    :param oai_set: The Set from which to harvest
    :param resumption_token: resumption token for paging
    :return: a ListRecords object which can be serialised and returned
    """
    app.logger.info("Processing ListRecords request for Metadata Prefix:{x} From:{y} To:{z} ResumptionToken:{a}".format(x=metadata_prefix, y=from_date, z=until_date, a=resumption_token))

    if resumption_token is None:
        # do an initial list records
        return _parameterised_list_records(dao, base_url, metadata_prefix=metadata_prefix, from_date=from_date, until_date=until_date, oai_set=oai_set)
    else:
        # resumption of previous request
        if (metadata_prefix is not None or from_date is not None or until_date is not None
                or oai_set is not None):
            return BadArgument(base_url)
        return _resume_list_records(dao, base_url, resumption_token=resumption_token)

def _parameterised_list_records(dao, base_url, metadata_prefix=None, from_date=None, until_date=None, oai_set=None, start_number=0):
    """
    Carry out a ListRecords request based on the set of actual paramters (i.e. not via a resumption token)

    :param dao: OAIPMHRecord implementation object to back the request
    :param base_url: base url of the service
    :param metadata_prefix: The metadata prefix for the format requested
    :param from_date: The earliest date from which to harvest
    :param until_date: The latest date until which to harvest
    :param oai_set: The Set from which to harvest
    :param start_number: The record number in the total set which you want as the start record for this page of results.
    :return:
    """
    # metadata prefix is required
    if metadata_prefix is None:
        app.logger.debug("No metadata prefix provided - bad request")
        return BadArgument(base_url)

    # get the formats and check that we have formats that we can disseminate
    formats = app.config.get("OAIPMH_METADATA_FORMATS", [])
    if formats is None or len(formats) == 0:
        app.logger.error("No Metadata Formats configured - you should fix this in configuration")
        return CannotDisseminateFormat(base_url)

    # check that the dates are formatted correctly
    fl = True
    ul = True
    if from_date is not None:
        fl = oaitools.DateFormat.legitimate_granularity(from_date)
    if until_date is not None:
        ul = oaitools.DateFormat.legitimate_granularity(until_date)

    if not fl or not ul:
        app.logger.debug("One or both of From/Until dates are incorrectly formatted: From:{x} To:{y} - bad request".format(x=from_date, y=until_date))
        return BadArgument(base_url)

    # get the result set size
    list_size = app.config.get("OAIPMH_LIST_RECORDS_PAGE_SIZE", 25)

    # decode the oai_set to something we can query with
    decoded_set = oaitools.decode_set_spec(oai_set) if oai_set is not None else None

    for f in formats:
        if f.get("metadataPrefix") == metadata_prefix:
            # do the query and set up the response object
            total, results = dao.list_records(from_date, until_date, decoded_set, list_size, start_number)

            # if there are no results, PMH requires us to throw an error
            if len(results) == 0:
                return NoRecordsMatch(base_url)

            # work out if we need a resumption token.  It can have one of 3 values:
            # - None = do not include the rt in the response
            # - some value = include in the response
            # - the empty string = include in the response
            resumption_token = None
            if total > start_number + len(results):
                new_start = start_number + len(results)
                resumption_token = oaitools.make_resumption_token(metadata_prefix=metadata_prefix, from_date=from_date,
                                        until_date=until_date, oai_set=oai_set, start_number=new_start)
            #else:
            #    resumption_token = ""

            lr = ListRecords(base_url, from_date=from_date, until_date=until_date, oai_set=oai_set, metadata_prefix=metadata_prefix)
            if resumption_token is not None:
                expiry = app.config.get("OAIPMH_RESUMPTION_TOKEN_EXPIRY", -1)
                lr.set_resumption(resumption_token, complete_list_size=total, cursor=start_number, expiry=expiry)

            for r in results:
                # do the crosswalk
                xwalk = get_crosswalk(f.get("metadataPrefix"))
                metadata = xwalk.crosswalk(r)
                header = xwalk.header(r)

                # add to the response
                lr.add_record(metadata, header)
            return lr

    # if we have not returned already, this means we can't disseminate this format
    return CannotDisseminateFormat(base_url)

def _resume_list_records(dao, base_url, resumption_token=None):
    """
    Carry out a ListRecords request based on a resumption token

    :param dao: OAIPMHRecord implementation object to back the request
    :param base_url: base url of the service
    :param resumption_token: resumption token for paging
    :return:
    """
    try:
        params = oaitools.decode_resumption_token(resumption_token)
    except oaitools.ResumptionTokenException:
        app.logger.debug("Problem interpreting ResumptionToken:{x} - bad request".format(x=resumption_token))
        return BadResumptionToken(base_url)
    return _parameterised_list_records(dao, base_url, **params)


def list_identifiers(dao, base_url, metadata_prefix=None, from_date=None, until_date=None, oai_set=None, resumption_token=None):
    """
    Actions a request to ListIdentifiers

    If resumption_token is provided, all other parameters must be left as None.

    :param dao: OAIPMHRecord implementation object to back the request
    :param base_url: base url of the service
    :param metadata_prefix: The metadata prefix for the format requested
    :param from_date: The earliest date from which to harvest
    :param until_date: The latest date until which to harvest
    :param oai_set: The Set from which to harvest
    :param resumption_token: resumption token for paging
    :return: a ListRecords object which can be serialised and returned
    """
    app.logger.info("Processing ListIdentifiers request for Metadata Prefix:{x} From:{y} To:{z} ResumptionToken:{a}".format(x=metadata_prefix, y=from_date, z=until_date, a=resumption_token))

    if resumption_token is None:
        # do an initial list records
        return _parameterised_list_identifiers(
            dao, base_url,
            metadata_prefix=metadata_prefix, from_date=from_date,
            until_date=until_date, oai_set=oai_set
        )
    else:
        # resumption of previous request
        if (metadata_prefix is not None or from_date is not None or until_date is not None
                or oai_set is not None):
            return BadArgument(base_url)
        return _resume_list_identifiers(dao, base_url, resumption_token=resumption_token)

def _parameterised_list_identifiers(dao, base_url, metadata_prefix=None, from_date=None, until_date=None, oai_set=None, start_number=0):
    """
    Carry out a ListIdentifiers request based on the set of actual paramters (i.e. not via a resumption token)

    :param dao: OAIPMHRecord implementation object to back the request
    :param base_url: base url of the service
    :param metadata_prefix: The metadata prefix for the format requested
    :param from_date: The earliest date from which to harvest
    :param until_date: The latest date until which to harvest
    :param oai_set: The Set from which to harvest
    :param start_number: The record number in the total set which you want as the start record for this page of results.
    :return: a ListRecords object which can be serialised and returned
    """
    # metadata prefix is required
    if metadata_prefix is None:
        app.logger.debug("No metadata prefix provided - bad request")
        return BadArgument(base_url)

    # get the formats and check that we have formats that we can disseminate
    formats = app.config.get("OAIPMH_METADATA_FORMATS", [])
    if formats is None or len(formats) == 0:
        app.logger.error("No Metadata Formats configured - you should fix this in configuration")
        return CannotDisseminateFormat(base_url)

    # check that the dates are formatted correctly
    fl = True
    ul = True
    if from_date is not None:
        fl = oaitools.DateFormat.legitimate_granularity(from_date)
    if until_date is not None:
        ul = oaitools.DateFormat.legitimate_granularity(until_date)

    if not fl or not ul:
        app.logger.debug("One or both of From/Until dates are incorrectly formatted: From:{x} To:{y} - bad request".format(x=from_date, y=until_date))
        return BadArgument(base_url)

    # get the result set size
    list_size = app.config.get("OAIPMH_LIST_IDENTIFIERS_PAGE_SIZE", 25)

    # decode the oai_set to something we can query with
    decoded_set = oaitools.decode_set_spec(oai_set) if oai_set is not None else None

    for f in formats:
        if f.get("metadataPrefix") == metadata_prefix:
            # do the query and set up the response object
            total, results = dao.list_records(from_date, until_date, decoded_set, list_size, start_number)

            # if there are no results, PMH requires us to throw an error
            if len(results) == 0:
                return NoRecordsMatch(base_url)

            # work out if we need a resumption token.  It can have one of 3 values:
            # - None = do not include the rt in the response
            # - some value = include in the response
            # - the empty string = include in the response
            resumption_token = None
            if total > start_number + len(results):
                new_start = start_number + len(results)
                resumption_token = oaitools.make_resumption_token(metadata_prefix=metadata_prefix, from_date=from_date,
                                        until_date=until_date, oai_set=oai_set, start_number=new_start)
            #else:
            #    resumption_token = ""

            li = ListIdentifiers(base_url, from_date=from_date, until_date=until_date, oai_set=oai_set, metadata_prefix=metadata_prefix)
            if resumption_token is not None:
                expiry = app.config.get("OAIPMH_RESUMPTION_TOKEN_EXPIRY", -1)
                li.set_resumption(resumption_token, complete_list_size=total, cursor=start_number, expiry=expiry)

            for r in results:
                # do the crosswalk (header only in this operation)
                xwalk = get_crosswalk(f.get("metadataPrefix"))
                header = xwalk.header(r)

                # add to the response
                li.add_record(header)
            return li

    # if we have not returned already, this means we can't disseminate this format
    return CannotDisseminateFormat(base_url)

def _resume_list_identifiers(dao, base_url, resumption_token=None):
    """
    Carry out a ListIdentifiers request based on a resumption token

    :param dao: OAIPMHRecord implementation object to back the request
    :param base_url: base url of the service
    :param resumption_token: resumption token for paging
    :return: a ListRecords object which can be serialised and returned
    """
    try:
        params = oaitools.decode_resumption_token(resumption_token)
    except oaitools.ResumptionTokenException:
        app.logger.debug("Problem interpreting ResumptionToken:{x} - bad request".format(x=resumption_token))
        return BadResumptionToken(base_url)
    return _parameterised_list_identifiers(dao, base_url, **params)


def get_record(dao, base_url, identifier=None, metadata_prefix=None):
    """
    Action a reuest to GetRecord

    :param dao: OAIPMHRecord implementation object to back the request
    :param base_url: base url of the service
    :param identifier: The record identifier for which we want the metadata
    :param metadata_prefix: metadata prefix for the format we want the record in
    :return: a GetRecord object which can be serialised and returned
    """
    app.logger.info("Processing GetRecord request for Notification:{x} Metadata Prefix:{y}".format(x=identifier, y=metadata_prefix))

    # check that we have both identifier and prefix - they are both required
    if identifier is None or metadata_prefix is None:
        app.logger.debug("One of metadata prefix or identifier missing - bad request")
        return BadArgument(base_url)
    
    # get the formats and check that we have formats that we can disseminate
    formats = app.config.get("OAIPMH_METADATA_FORMATS", [])
    if formats is None or len(formats) == 0:
        app.logger.error("No Metadata Formats configured - you should fix this in configuration")
        return CannotDisseminateFormat(base_url)
    
    # look for our record of the format we've been asked for
    for f in formats:
        if f.get("metadataPrefix") == metadata_prefix:
            # obtain the record from the dao
            record = dao.pull(identifier)
            if record is None:
                app.logger.debug("Notification:{x} does not exist in JPER".format(x=identifier))
                return IdDoesNotExist(base_url)

            # do the crosswalk
            xwalk = get_crosswalk(f.get("metadataPrefix"))
            metadata = xwalk.crosswalk(record)
            header = xwalk.header(record)

            # make the response
            oai_id = oaitools.make_oai_identifier(identifier, "notification")
            gr = GetRecord(base_url, oai_id, metadata_prefix)
            gr.metadata = metadata
            gr.header = header
            return gr
    
    # if we have not returned already, this means we can't disseminate this format
    return CannotDisseminateFormat(base_url)



#####################################################################
## Model Objects
#####################################################################

class OAI_PMH(object):
    """
    Base class for all OAI-PMH serialisable objects to extend from
    """

    VERSION = "2.0"
    
    PMH_NAMESPACE = "http://www.openarchives.org/OAI/2.0/"
    PMH = "{%s}" % PMH_NAMESPACE
    
    XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
    XSI = "{%s}" % XSI_NAMESPACE
    
    NSMAP = {None : PMH_NAMESPACE, "xsi" : XSI_NAMESPACE}
    
    def __init__(self, base_url):
        self.base_url = base_url
        self.verb = None
    
    def _to_xml(self):
        """
        Convert the object to an etree.Element object

        :return: etree.Element XML doc
        """
        oai = etree.Element(self.PMH + "OAI-PMH", nsmap=self.NSMAP)
        oai.set(self.XSI + "schemaLocation", 
            "http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd")
        
        respdate = etree.SubElement(oai, self.PMH + "responseDate")
        respdate.text = oaitools.get_response_date()
        
        req = etree.SubElement(oai, self.PMH + "request")
        if self.verb is not None:
            req.set("verb", self.verb)
        req.text = self.base_url
        self.add_request_attributes(req)
        
        element = self.get_element()
        oai.append(element)
        
        return oai
    
    def serialise(self):
        """
        Serialise the object to an XML string

        :return: a string containing the XML
        """
        xml = self._to_xml()
        return etree.tostring(xml, xml_declaration=True, encoding="UTF-8")
        
    def get_element(self):
        """
        Get the etree.Element for the inner, type-specific portion of the document
        """
        raise NotImplementedError()
        
    def add_request_attributes(self, element):
        """
        Add attributes to the element that define the type-specific request information
        to be reflected back to the caller
        """
        return

class GetRecord(OAI_PMH):
    """
    Serialisable object representing a GetRecord response
    """

    def __init__(self, base_url, identifier, metadata_prefix):
        super(GetRecord, self).__init__(base_url)
        self.verb = "GetRecord"
        self.identifier = identifier
        self.metadata_prefix = metadata_prefix
        self.metadata = None
        self.header = None
    
    def get_element(self):
        gr = etree.Element(self.PMH + "GetRecord", nsmap=self.NSMAP)
        record = etree.SubElement(gr, self.PMH + "record")
        
        record.append(self.header)
        record.append(self.metadata)
        
        return gr
        
    def add_request_attributes(self, element):
        if self.identifier is not None:
            element.set("identifier", self.identifier)
        if self.metadata_prefix is not None:
            element.set("metadataPrefix", self.metadata_prefix)

class Identify(OAI_PMH):
    """
    Serialisable object representing an Identify response
    """
    def __init__(self, base_url, repo_name, admin_email):
        super(Identify, self).__init__(base_url)
        self.verb = "Identify"
        self.repo_name = repo_name
        self.admin_email = admin_email
        self.earliest_datestamp = None
    
    def get_element(self):
        identify = etree.Element(self.PMH + "Identify", nsmap=self.NSMAP)
        
        repo_name = etree.SubElement(identify, self.PMH + "repositoryName")
        repo_name.text = self.repo_name
        
        base = etree.SubElement(identify, self.PMH + "baseURL")
        base.text = self.base_url
        
        protocol = etree.SubElement(identify, self.PMH + "protocolVersion")
        protocol.text = self.VERSION
        
        admin_email = etree.SubElement(identify, self.PMH + "adminEmail")
        admin_email.text = self.admin_email
        
        earliest = etree.SubElement(identify, self.PMH + "earliestDatestamp")
        if self.earliest_datestamp is not None:
            earliest.text = self.earliest_datestamp
        else:
            # earliest.text = "1970-01-01T00:00:00Z" # beginning of the unix epoch
            oaitools.DateFormat.default_earliest()
        
        deletes = etree.SubElement(identify, self.PMH + "deletedRecord")
        deletes.text = "transient" # keep the door open
        
        granularity = etree.SubElement(identify, self.PMH + "granularity")
        # granularity.text = "YYYY-MM-DD"
        granularity.text = oaitools.DateFormat.granularity()
        
        return identify

class ListIdentifiers(OAI_PMH):
    """
    Serialisable object representing a ListIdentifiers response
    """

    def __init__(self, base_url, from_date=None, until_date=None, oai_set=None, metadata_prefix=None):
        super(ListIdentifiers, self).__init__(base_url)
        self.verb = "ListIdentifiers"
        self.from_date = from_date
        self.until_date = until_date
        self.oai_set = oai_set
        self.metadata_prefix = metadata_prefix
        self.records = []
        self.resumption = None

    def set_resumption(self, resumption_token, complete_list_size=None, cursor=None, expiry=-1):
        self.resumption = {"resumption_token" : resumption_token, "expiry" : expiry}
        if complete_list_size is not None:
            self.resumption["complete_list_size"] = complete_list_size
        if cursor is not None:
            self.resumption["cursor"] = cursor

    def add_record(self, header):
        self.records.append(header)

    def add_request_attributes(self, element):
        if self.from_date is not None:
            element.set("from", self.from_date)
        if self.until_date is not None:
            element.set("until", self.until_date)
        if self.oai_set is not None:
            element.set("set", self.oai_set)
        if self.metadata_prefix is not None:
            element.set("metadataPrefix", self.metadata_prefix)
        
    def get_element(self):
        lr = etree.Element(self.PMH + "ListIdentifiers", nsmap=self.NSMAP)
        
        for header in self.records:
            lr.append(header)
        
        if self.resumption is not None:
            rt = etree.SubElement(lr, self.PMH + "resumptionToken")
            if "complete_list_size" in self.resumption:
                rt.set("completeListSize", str(self.resumption.get("complete_list_size")))
            if "cursor" in self.resumption:
                rt.set("cursor", str(self.resumption.get("cursor")))
            expiry = self.resumption.get("expiry", -1)
            expire_date = None
            if expiry >= 0:
                # expire_date = (datetime.now() + timedelta(0, expiry)).strftime("%Y-%m-%dT%H:%M:%SZ")
                expire_date = oaitools.DateFormat.format(datetime.now() + timedelta(0, expiry))
                rt.set("expirationDate", expire_date)
            rt.text = self.resumption.get("resumption_token")
        
        return lr

class ListMetadataFormats(OAI_PMH):
    """
    Serialisable object representing a ListMetadataFormats response
    """

    def __init__(self, base_url, identifier=None):
        super(ListMetadataFormats, self).__init__(base_url)
        self.verb = "ListMetadataFormats"
        self.identifier = identifier
        self.formats = []
    
    def add_format(self, metadata_prefix, schema, metadata_namespace):
        self.formats.append(
            {
                "metadataPrefix" : metadata_prefix,
                "schema" : schema,
                "metadataNamespace" : metadata_namespace
            }
        )
    
    def add_request_attributes(self, element):
        if self.identifier is not None:
            element.set("identifier", self.identifier)
        
    def get_element(self):
        lmf = etree.Element(self.PMH + "ListMetadataFormats", nsmap=self.NSMAP)
        
        for f in self.formats:
            mdf = etree.SubElement(lmf, self.PMH + "metadataFormat")
            
            mdp = etree.SubElement(mdf, self.PMH + "metadataPrefix")
            mdp.text = f.get("metadataPrefix")
            
            sch = etree.SubElement(mdf, self.PMH + "schema")
            sch.text = f.get("schema")
            
            mdn = etree.SubElement(mdf, self.PMH + "metadataNamespace")
            mdn.text = f.get("metadataNamespace")
        
        return lmf

class ListRecords(OAI_PMH):
    """
    Serialisable object representing a ListRecords response
    """

    def __init__(self, base_url, from_date=None, until_date=None, oai_set=None, metadata_prefix=None):
        super(ListRecords, self).__init__(base_url)
        self.verb = "ListRecords"
        self.from_date = from_date
        self.until_date = until_date
        self.oai_set = oai_set
        self.metadata_prefix = metadata_prefix
        self.records = []
        self.resumption = None
        self.resumption_expiry = -1

    def set_resumption(self, resumption_token, complete_list_size=None, cursor=None, expiry=-1):
        self.resumption = {"resumption_token" : resumption_token, "expiry" : expiry}
        if complete_list_size is not None:
            self.resumption["complete_list_size"] = complete_list_size
        if cursor is not None:
            self.resumption["cursor"] = cursor

    def add_record(self, metadata, header):
        self.records.append((metadata, header))

    def add_request_attributes(self, element):
        if self.from_date is not None:
            element.set("from", self.from_date)
        if self.until_date is not None:
            element.set("until", self.until_date)
        if self.oai_set is not None:
            element.set("set", self.oai_set)
        if self.metadata_prefix is not None:
            element.set("metadataPrefix", self.metadata_prefix)
        
    def get_element(self):
        lr = etree.Element(self.PMH + "ListRecords", nsmap=self.NSMAP)
        
        for metadata, header in self.records:
            r = etree.SubElement(lr, self.PMH + "record")
            r.append(header)
            r.append(metadata)
        
        if self.resumption is not None:
            rt = etree.SubElement(lr, self.PMH + "resumptionToken")
            if "complete_list_size" in self.resumption:
                rt.set("completeListSize", str(self.resumption.get("complete_list_size")))
            if "cursor" in self.resumption:
                rt.set("cursor", str(self.resumption.get("cursor")))
            expiry = self.resumption.get("expiry", -1)
            expire_date = None
            if expiry >= 0:
                # expire_date = (datetime.now() + timedelta(0, expiry)).strftime("%Y-%m-%dT%H:%M:%SZ")
                expire_date = oaitools.DateFormat.format(datetime.now() + timedelta(0, expiry))
                rt.set("expirationDate", expire_date)
            rt.text = self.resumption.get("resumption_token")
        
        return lr

class ListSets(OAI_PMH):
    """
    Serialisable object representing a ListSets response
    """

    def __init__(self, base_url):
        super(ListSets, self).__init__(base_url)
        self.verb = "ListSets"
        self.sets = []
    
    def add_set(self, spec, name):
        self.sets.append((spec, name))
    
    def get_element(self):
        ls = etree.Element(self.PMH + "ListSets", nsmap=self.NSMAP)
        
        for spec, name in self.sets:
            s = etree.SubElement(ls, self.PMH + "set")
            specel = etree.SubElement(s, self.PMH + "setSpec")
            specel.text = spec
            nameel = etree.SubElement(s, self.PMH + "setName")
            nameel.text = name
        
        return ls
        

#####################################################################
## Error Handling
#####################################################################

class OAIPMHError(OAI_PMH):
    """
    Base class to represent a serialisable error document
    """
    def __init__(self, base_url):
        super(OAIPMHError, self).__init__(base_url)
        self.code = None
        self.description = None
    
    def get_element(self):
        error = etree.Element(self.PMH + "error", nsmap=self.NSMAP)
        
        if self.code is not None:
            error.set("code", self.code)
        
        if self.description is not None:
            error.text = self.description
        
        return error

class BadArgument(OAIPMHError):
    """
    Serialisable object representing a BadArgument response
    """
    def __init__(self, base_url):
        super(BadArgument, self).__init__(base_url)
        self.code = "badArgument"
        self.description = "The request includes illegal arguments, is missing required arguments, includes a repeated argument, or values for arguments have an illegal syntax."

class BadResumptionToken(OAIPMHError):
    """
    Serialisable object representing a BadResumptionToken response
    """
    def __init__(self, base_url):
        super(BadResumptionToken, self).__init__(base_url)
        self.code = "badResumptionToken"
        self.description = "The value of the resumptionToken argument is invalid or expired."

class BadVerb(OAIPMHError):
    """
    Serialisable object representing a BadVerb response
    """
    def __init__(self, base_url):
        super(BadVerb, self).__init__(base_url)
        self.code = "badVerb"
        self.description = "Value of the verb argument is not a legal OAI-PMH verb, the verb argument is missing, or the verb argument is repeated."

class CannotDisseminateFormat(OAIPMHError):
    """
    Serialisable object representing a CannotDisseminateFormat response
    """
    def __init__(self, base_url):
        super(CannotDisseminateFormat, self).__init__(base_url)
        self.code = "cannotDisseminateFormat"
        self.description = "The metadata format identified by the value given for the metadataPrefix argument is not supported by the item or by the repository."

class IdDoesNotExist(OAIPMHError):
    """
    Serialisable object representing an IdDoesNotExist response
    """
    def __init__(self, base_url):
        super(IdDoesNotExist, self).__init__(base_url)
        self.code = "idDoesNotExist"
        self.description = "The value of the identifier argument is unknown or illegal in this repository."

class NoRecordsMatch(OAIPMHError):
    """
    Serialisable object representing a NoRecordsMatch response
    """
    def __init__(self, base_url):
        super(NoRecordsMatch, self).__init__(base_url)
        self.code = "noRecordsMatch"
        self.description = "The combination of the values of the from, until, set and metadataPrefix arguments results in an empty list."

class NoMetadataFormats(OAIPMHError):
    """
    Serialisable object representing a NoMetadataFormats response
    """
    def __init__(self, base_url):
        super(NoMetadataFormats, self).__init__(base_url)
        self.code = "noMetadataFormats"
        self.description = "There are no metadata formats available for the specified item."

class NoSetHierarchy(OAIPMHError):
    """
    Serialisable object representing a NoSetHierarchy response
    """
    def __init__(self, base_url):
        super(NoSetHierarchy, self).__init__(base_url)
        self.code = "noSetHierarchy"
        self.description = "The repository does not support sets."
