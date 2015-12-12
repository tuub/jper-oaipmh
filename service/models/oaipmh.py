from octopus.core import app
from octopus.lib import dates
from octopus.modules.jper import client
import math

class OAIPMHRecord(object):

    def earliest_datestamp(self):
        return dates.before_now(app.config.get("OAI_MAX_LOOKBACK", 7776000)).strftime("%Y-%m-%dT%H:%M:%SZ")

    def identifier_exists(self, identifier):
        j = client.JPER()
        n = j.get_notification(identifier)
        return n is not None

    def list_sets(self):
        return []

    def list_records(self, from_date=None, until_date=None, oai_set=None, list_size=None, start_number=None, **kwargs):
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

        return nl.total, nl.notifications

class OAIPMHAll(OAIPMHRecord):
    pass

class OAIPMHRepo(OAIPMHRecord):
    def __init__(self, repo_id):
        self.repo_id = repo_id

    def list_records(self, from_date=None, until_date=None, oai_set=None, list_size=None, start_number=None, **kwargs):
        return super(OAIPMHRepo, self).list_records(from_date=from_date, until_date=until_date, oai_set=oai_set, list_size=list_size, start_number=start_number, repository_id=self.repo_id)