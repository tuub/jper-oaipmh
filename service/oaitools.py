from datetime import datetime
import base64, json
from octopus.core import app

class DateFormat(object):
    @classmethod
    def granularity(self):
        return "YYYY-MM-DDThh:mm:ssZ"

    @classmethod
    def default_earliest(cls):
        return "1970-01-01T00:00:00Z"

    @classmethod
    def now(cls):
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    @classmethod
    def format(cls, date):
        return date.strftime("%Y-%m-%dT%H:%M:%SZ")

    @classmethod
    def legitimate_granularity(cls, datestr):
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
    return base64.urlsafe_b64encode(setspec).replace("=", "~")

def decode_set_spec(setspec):
    return base64.urlsafe_b64decode(str(setspec).replace("~", "="))

def make_resumption_token(metadata_prefix=None, from_date=None, until_date=None, oai_set=None, start_number=None):
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
    pass

def decode_resumption_token(resumption_token):
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
    return "oai:" + app.config.get("OAIPMH_IDENTIFIER_NAMESPACE") + "/" + qualifier + ":" + identifier

def extract_internal_id(oai_identifier):
    # most of the identifier is for show - we only care about the hex string at the end
    return oai_identifier.split(":")[-1]

def get_response_date():
    # return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    return DateFormat.now()

def normalise_date(date):
    # FIXME: do we need a more powerful date normalisation routine?
    try:
        datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
        return date
    except:
        return "T".join(date.split(" ")) + "Z"
