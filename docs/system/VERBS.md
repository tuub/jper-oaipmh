# OAI-PMH Verb to JPER API mapping

This document describes the mapping that this application provides from the [OAI-PMH](http://www.openarchives.org/OAI/openarchivesprotocol.html) verbs and their associated parameters
to the JPER API.

There are 2 possible forms for the OAI endpoint:

1. For the entire set of routed notifications
2. For a specific repository's set of routed notifications

These are mounted at separate web routes, of the following forms:

1. Entire set: /all
2. Repo-specific: /repo/repo_id where repo_id is the account identifier for the repository

Note that these are not made available as OAI-PMH sets because the account ids should not be published explicitly.

## Identify

This request asks the OAI-PMH server to identify itself and provide some useful information for the client

Incoming parameters:

* verb: Identify

Returned information:

* Repository Name: from configuration
* Email address: from configuration
* Earliest datestamp: 3 months before current date

JPER API request: None

## ListSets

This request asks the OAI-PMH server to list the sets that are available to the client

Incoming parameters:

* verb: ListSets

Returned information

* An empty list - sets are not supported by this endpoint

JPER API request: None

## ListMetadataFormats

This request asks the OAI-PMH server to list the metadata formats that are available to the client

Incoming parameters:

* verb: ListMetadataFormats
* identifier: notification id (optional)

Returned information:

* Metadata Format: oai_dc (schema: http://www.openarchives.org/OAI/2.0/oai_dc.xsd, namespace: http://www.openarchives.org/OAI/2.0/oai_dc/)

JPER API request: None

## ListIdentifiers

This request asks the OAI-PMH server to list the identifiers of all records which match the parameters of the request:

* verb: ListIdentifiers
* from: lower bound for request (optional)
* until: upper bound for request (optional)
* metadataPrefix: metadata format supported by identifier
* set: set to retrieve from
* resumptionToken: paging control from the previous request (exclusive)

Returned information:

* Identifiers: notification id
* Resumption Token: base64 encoded request parameters for next page

JPER API request:

Params:

* since: provided "from" date, or earliest available datestamp
* page: 1, or from resumptionToken
* pageSize: 100

    GET /routed/<repo id>?<params>

If the client provides an "until" date, once the requests to the API pass that date, the OAI-PMH server will filter 
results from the current request, and cease issuing resumption tokens.


## ListRecords

This request asks the OAI-PMH server to list the full metadata records of all records which match the parameters of the request:

* verb: ListRecords
* from: lower bound for request (optional)
* until: upper bound for request (optional)
* metadataPrefix: metadata format supported by record
* set: set to retrieve from
* resumptionToken: paging control from the previous request (exclusive)

Returned information:

* Records: notification metadata, only oai_dc metadata prefix is supported
* Resumption Token: base64 encoded request parameters for next page

JPER API request:

Params:

* since: provided "from" date, or earliest available datestamp
* page: 1, or from resumptionToken
* pageSize: 100

    GET /routed/<repo id>?<params>

If the client provides an "until" date, once the requests to the API pass that date, the OAI-PMH server will filter 
results from the current request, and cease issuing resumption tokens


## GetRecord

This request asks the OAI-PMH server to provide the full metadata record for the identifier received:

* verb: GetRecord
* identifier: notification id
* metadataPrefix: metadata format supported by record

Returned information:

* Record: notification metadata, only oai_dc metadata prefix is supported

JPER API request:

    GET /notification/<notification id>

