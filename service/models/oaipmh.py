"""
Model objects which bind the OAI-PMH records to the JPER API
"""
from octopus.core import app
from octopus.lib import dates
from octopus.modules.jper import client
import math

class OAIPMHRecord(object):
    """
    Base class for communicating with the JPER API for the key operations required by
    the OAI interface.
    """

    def earliest_datestamp(self):
        """
        What is the earliest datestamp available to the user.  This is calculated based on a
        time period before the current time (defined by OAI_MAX_LOOKBACK).

        :return: timestamp of the earliest supported date
        """
        return dates.before_now(app.config.get("OAI_MAX_LOOKBACK", 7776000)).strftime("%Y-%m-%dT%H:%M:%SZ")

    def identifier_exists(self, identifier):
        """
        Does the supplied identifier exist in JPER as a notification?

        :param identifier: JPER notification id
        :return: True if exists, False if not
        """
        n = self.pull(identifier)
        return n is not None

    def list_sets(self):
        """
        List of sets supported by the endpoint.  This is always an empty list

        :return: an empty list
        """
        return []

    def list_records(self, from_date=None, until_date=None, oai_set=None, list_size=None, start_number=None, **kwargs):
        """
        List the records which match the current set of parameters.

        Note that this function ignores the until_date and the oai_set, because:

        * until_date - there is no equivalent operation in JPER, so it is not possible to give an accurate count of a time-boxed request
        * oai_set - This interface does not implement sets

        :param from_date: The date to request notifications from
        :param until_date: DO NOT USE
        :param oai_set: DO NOT USE
        :param list_size: number of results per page (subject to limitation by JPER)
        :param start_number: record number to start this page with
        :param kwargs: additional kewyword arguments to pass to JPER.list_notifications
        :return: a tuple of the total count, and the list of notifications on this page: (count, this_page)
        """
        j = client.JPER()

        # sanitise the from_date to a suitable format for the jper api
        if from_date is None:
            from_date = self.earliest_datestamp()
        else:
            from_date = dates.reformat(from_date, out_format="%Y-%m-%dT%H:%M:%SZ")

        # calculate the page number
        page = 1
        if list_size is not None and start_number is not None:
            page = int(math.ceil((start_number + 1.0) / list_size))

        nl = j.list_notifications(from_date, page=page, page_size=list_size, **kwargs)

        ## app.logger.debug(u"##### list_records: JPER client found {y} notification(s): from={f}, page={p}, page_size={s}".format(y=nl.total, f=from_date, p=page, s=list_size))

        return nl.total, nl.notifications

    def pull(self, identifier):
        """
        Retrieve the notification associated with the provided identifier

        :param identifier: JPER notification id
        :return: the notification object
        """
        j = client.JPER()
        n = j.get_notification(identifier)
        return n

class OAIPMHAll(OAIPMHRecord):
    """
    Class to use when querying the entire set of routed JPER notifications
    """
    pass

class OAIPMHRepo(OAIPMHRecord):
    """
    Class to use when querying a specific repository's routed JPER notifications
    """

    def __init__(self, repo_id):
        """
        Create a new record interface for a repo-specific OAI endpoint

        :param repo_id: JPER accound id for the desired repository
        :return:
        """
        self.repo_id = repo_id

    def list_records(self, from_date=None, until_date=None, oai_set=None, list_size=None, start_number=None, **kwargs):
        return super(OAIPMHRepo, self).list_records(from_date=from_date, until_date=until_date, oai_set=oai_set, list_size=list_size, start_number=start_number, repository_id=self.repo_id)
