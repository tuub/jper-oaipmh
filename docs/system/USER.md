# JPER OAI-PMH endpoint

This document describes how to interact with the JPER OAI-PMH endpoint to retrieve the metadata records of successfully
routed notifications.

You may also wish to read the [OAI-PMH documentation](http://www.openarchives.org/OAI/openarchivesprotocol.html).

This endpoint only supports oai_dc formatted metadata, and can only access notifications going back 3 months.

## All routed notifications

You can retrieve metadata records for all routed notifications by sending requests to

    https://www.oa-deepgreen.de/oaipmh/all

For example:

    GET https://www.oa-deepgreen.de/oaipmh/all?verb=ListRecords&from=2016-01-01&metadataPrefix=oai_dc
    
## Routed notifications for a specific repository

You can retrieve metadata records for all routed notifications for a specific repository by sending requests to

    https://www.oa-deepgreen.de/oaipmh/repo/<repo id>

Where "repo_id" is the account id of the repository whose notifications to retrieve.

For example:

    GET https://www.oa-deepgreen.de/oaipmh/repo/123456789?verb=ListRecords&from=2016-01-01&metadataPrefix=oai_dc

