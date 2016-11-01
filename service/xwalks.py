"""
Crosswalks from native JPER JSON metadata to supported formats by OAI
"""

from lxml import etree
from copy import deepcopy
from service.xml import set_text
from octopus.modules.jper import models
from service import oaitools

#####################################################################
## Crosswalks
#####################################################################

class OAI_Crosswalk(object):
    """
    Base class for all OAI crosswalks.  Provides stub methods and namespace declarations
    """

    PMH_NAMESPACE = "http://www.openarchives.org/OAI/2.0/"
    PMH = "{%s}" % PMH_NAMESPACE

    XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
    XSI = "{%s}" % XSI_NAMESPACE

    NSMAP = {None: PMH_NAMESPACE, "xsi": XSI_NAMESPACE}

    def crosswalk(self, record):
        """
        Convert the record to an etree.Element object which contains
        the appropriate metadata

        :param record: notification JSON
        :return: XML element
        """
        raise NotImplementedError()

    def header(self, record):
        """
        Convert the record to an etree.Element object representing the record's
        header information.

        :param record: notification JSON
        :return: XML element
        """
        raise NotImplementedError()

class OAI_DC(OAI_Crosswalk):
    """
    OAI_DC crosswalk from notification JSON
    """

    OAIDC_NAMESPACE = "http://www.openarchives.org/OAI/2.0/oai_dc/"
    OAIDC = "{%s}" % OAIDC_NAMESPACE

    DC_NAMESPACE = "http://purl.org/dc/elements/1.1/"
    DC = "{%s}" % DC_NAMESPACE

    NSMAP = deepcopy(OAI_Crosswalk.NSMAP)
    NSMAP.update({"oai_dc": OAIDC_NAMESPACE, "dc": DC_NAMESPACE})

    def crosswalk(self, record):
        metadata = etree.Element(self.PMH + "metadata", nsmap=self.NSMAP)
        oai_dc = etree.SubElement(metadata, self.OAIDC + "dc")
        oai_dc.set(self.XSI + "schemaLocation",
            "http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd")

        assert isinstance(record, models.OutgoingNotification)

        # metadata.title -> oai_dc:title
        if record.title is not None:
            title = etree.SubElement(oai_dc, self.DC + "title")
            set_text(title, record.title)

        # metadata.publisher -> oai_dc:publisher
        if record.publisher is not None:
            pub = etree.SubElement(oai_dc, self.DC + "publisher")
            set_text(pub, record.publisher)

        # metadata.source.name -> oai_dc:source
        if record.source_name is not None:
            sn = etree.SubElement(oai_dc, self.DC + "source")
            set_text(sn, record.source_name)

        # metadata.source.identifier -> oai_dc:source
        for ident in record.source_identifiers:
            si = etree.SubElement(oai_dc, self.DC + "source")
            set_text(si, ident.get("type", "") + ":" + ident.get("id", ""))

        # metadata.identifier -> oai_dc:identifier
        for ident in record.identifiers:
            id = etree.SubElement(oai_dc, self.DC + "identifier")
            set_text(id, ident.get("type", "") + ":" + ident.get("id", ""))

        # metadata.type -> oai_dc:type
        if record.type is not None:
            ty = etree.SubElement(oai_dc, self.DC + "type")
            set_text(ty, record.type)

        # metadata.author -> oai_dc:creator
        affs = []
        for a in record.authors:
            name = a.get("name")
            identifiers = []

            if name is not None:
                ael = etree.SubElement(oai_dc, self.DC + "creator")
                set_text(ael, name)

            for ident in a.get("identifier", []):
                id = ident.get("type", "") + ":" + ident.get("id", "")
                ael = etree.SubElement(oai_dc, self.DC + "creator")
                set_text(ael, id)

            aff = a.get("affiliation")
            if aff is not None:
                affs.append(aff)

        # metadata.author.affiliation -> oai_dc:contributor
        for aff in list(set(affs)):
            affel = etree.SubElement(oai_dc, self.DC + "contributor")
            set_text(affel, aff)

        # metadata.language -> oai_dc:langauage
        if record.language is not None:
            lan = etree.SubElement(oai_dc, self.DC + "language")
            set_text(lan, record.language)

        # metadata.publication_date -> oai_dc:date
        if record.publication_date is not None:
            pd = etree.SubElement(oai_dc, self.DC + "date")
            set_text(pd, record.publication_date)

        # metadata.license_ref.title -> oai_dc:rights
        lic = record.license
        if lic is not None and lic.get("title") is not None:
            lt = etree.SubElement(oai_dc, self.DC + "rights")
            set_text(lt, lic.get("title"))

        # metadata.subject -> oai_dc:subject
        for s in record.subjects:
            sub = etree.SubElement(oai_dc, self.DC + "subject")
            set_text(sub, s)

        return metadata

    def header(self, record):
        head = etree.Element(self.PMH + "header", nsmap=self.NSMAP)

        identifier = etree.SubElement(head, self.PMH + "identifier")
        set_text(identifier, oaitools.make_oai_identifier(record.id, "notification"))

        datestamp = etree.SubElement(head, self.PMH + "datestamp")
        set_text(datestamp, oaitools.normalise_date(record.analysis_date))

        return head

