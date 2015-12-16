"""
A set of useful functions for working with OAI-PMH data
"""

from datetime import datetime
import base64, json
from octopus.core import app

class DateFormat(object):
    """
    Class which helps us manage the date formats allowed by the standard
    """

    @classmethod
    def granularity(self):
        """
        What is the date granularity of the service

        :return: The date granularity
        """
        return "YYYY-MM-DDThh:mm:ssZ"

    @classmethod
    def default_earliest(cls):
        """
        What is the earliest date, if no other date is available

        :return: default earliest date (start of unix epoch)
        """
        return "1970-01-01T00:00:00Z"

    @classmethod
    def now(cls):
        """
        String representation of current timestamp

        :return: string timestamp
        """
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    @classmethod
    def format(cls, date):
        """
        Format the given datestamp to the correct OAI-PMH date format

        :param date: datestamp
        :return: string
        """
        return date.strftime("%Y-%m-%dT%H:%M:%SZ")

    @classmethod
    def legitimate_granularity(cls, datestr):
        """
        Check whether the supplied date is of an allowed granularity

        :param datestr: the supplied date
        :return: True if allowed, False if not
        """
        formats = ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ"]
        success = False
        for f in formats:
            try:
                datetime.strptime(datestr, f)
                success = True
                break
            except Exception:
                pass
        return success

def make_set_spec(setspec):
    """
    Convert the setspec into something that can be included in a ListSets response

    :param setspec: the name of the set
    :return: the encoded name of the set
    """
    return base64.urlsafe_b64encode(setspec).replace("=", "~")

def decode_set_spec(setspec):
    """
    Decode the setspec into something usable by the system

    :param setspec: the encoded name of the set
    :return: the decoded name of the set
    """
    return base64.urlsafe_b64decode(str(setspec).replace("~", "="))

def make_resumption_token(metadata_prefix=None, from_date=None, until_date=None, oai_set=None, start_number=None):
    """
    Create a resumption token that can represent the supplied request parameters

    :param metadata_prefix: the metadata prefix of the request
    :param from_date: the from date of the request
    :param until_date: the until date of the request
    :param oai_set: the oai set name of the request
    :param start_number: the start number for the record cursor
    :return: an encoded resumption token suitable for providing the page of results from the parameters
    """
    d = {}
    if metadata_prefix is not None:
        d["m"] = metadata_prefix
    if from_date is not None:
        d["f"] = from_date
    if until_date is not None:
        d["u"] = until_date
    if oai_set is not None:
        d["s"] = oai_set
    if start_number is not None:
        d["n"] = start_number
    j = json.dumps(d)
    b = base64.urlsafe_b64encode(j)
    return b

class ResumptionTokenException(Exception):
    """
    Exception class for any issues with Resumption Tokens
    """
    pass

def decode_resumption_token(resumption_token):
    """
    Take the encoded resumption token, and convert it back into a set of parameters suitable for
    use as **kwargs

    :param resumption_token: the resumption token from the request
    :return: dict containing the parameters of the request
    """
    # attempt to parse the resumption token out of base64 encoding and as a json object
    try:
        j = base64.urlsafe_b64decode(str(resumption_token))
    except TypeError:
        raise ResumptionTokenException()
    try:
        d = json.loads(j)
    except ValueError:
        raise ResumptionTokenException()

    # if we succeed read out the parameters
    params = {}
    if "m" in d: params["metadata_prefix"] = d.get("m")
    if "f" in d: params["from_date"] = d.get("f")
    if "u" in d: params["until_date"] = d.get("u")
    if "s" in d: params["oai_set"] = d.get("s")
    if "n" in d: params["start_number"] = d.get("n")
    return params

def make_oai_identifier(identifier, qualifier):
    """
    Make a suitable tag identifier for records in the OAI response.

    Identifiers are of the form:

    ::

        oai:[namespace]/[qualifier]:[identifier]

    Namespace is taken from configuration (OAIPMH_IDENTIFIER_NAMESPACE)

    :param identifier: the system identifier to incorporate
    :param qualifier: the qualifier for the identifier
    :return:
    """
    return "oai:" + app.config.get("OAIPMH_IDENTIFIER_NAMESPACE") + "/" + qualifier + ":" + identifier

def extract_internal_id(oai_identifier):
    """
    Extract the internal identifier from the full tag identifier from the OAI request

    :param oai_identifier: the full OAI identifier for a record
    :return: the internal identifier
    """
    # most of the identifier is for show - we only care about the hex string at the end
    return oai_identifier.split(":")[-1]

def get_response_date():
    """
    Date of response to include in responses

    :return: the current time, correctly formatted
    """
    # return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    return DateFormat.now()

def normalise_date(date):
    """
    Normalise the date provided into something we can use

    :param date: the supplied date
    :return: the normalised date
    """
    # FIXME: do we need a more powerful date normalisation routine?
    try:
        datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
        return date
    except:
        return "T".join(date.split(" ")) + "Z"
