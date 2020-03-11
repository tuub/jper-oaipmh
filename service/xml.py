"""
Some useful tools for dealing with the oddities of XML serialisation
"""

import re, sys
from octopus.core import app

###########################################################
# XML Character encoding hacks
###########################################################


_illegal_unichrs = [(0x00, 0x08), (0x0B, 0x0C), (0x0E, 0x1F),
                    (0x7F, 0x84), (0x86, 0x9F),
                    (0xFDD0, 0xFDDF), (0xFFFE, 0xFFFF)]
if sys.maxunicode >= 0x10000:  # not narrow build
    _illegal_unichrs.extend([(0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF),
                             (0x3FFFE, 0x3FFFF), (0x4FFFE, 0x4FFFF),
                             (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
                             (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF),
                             (0x9FFFE, 0x9FFFF), (0xAFFFE, 0xAFFFF),
                             (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
                             (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF),
                             (0xFFFFE, 0xFFFFF), (0x10FFFE, 0x10FFFF)])
_illegal_ranges = ["%s-%s" % (chr(low), chr(high))
                   for (low, high) in _illegal_unichrs]
_illegal_xml_chars_RE = re.compile('[%s]' % ''.join(_illegal_ranges))

def valid_XML_char_ordinal(i):
    """
    Is the character i an allowed XML character

    :param i: the character
    :return: True if allowed, False if not
    """
    return ( # conditions ordered by presumed frequency
        0x20 <= i <= 0xD7FF
        or i in (0x9, 0xA, 0xD)
        or 0xE000 <= i <= 0xFFFD
        or 0x10000 <= i <= 0x10FFFF
        )

def clean_unreadable(input_string):
    """
    Take the string and strip any illegal XML characters

    :param input_string: an unreadable XML string
    :return: a cleaned string - it will lose information, but what else can you do?
    """
    try:
        return _illegal_xml_chars_RE.sub("", input_string)
    except TypeError as e:
        app.logger.error("Unable to strip illegal XML chars from: {x}, {y}".format(x=input_string, y=type(input_string)))
        return None

def xml_clean(input_string):
    """
    Brute force clean all the characters in a string until they absolutely definitely will
    serialise in XML (slower than clean_unreadable, but more reliable)

    :param input_string: illegal XML string
    :return: legal XML string
    """
    cleaned_string = ''.join(c for c in input_string if valid_XML_char_ordinal(ord(c)))
    return cleaned_string

def set_text(element, input_string):
    """
    Set the given text on the given element, carrying out whatever XML cleanup is also requried.

    :param element: element to write to
    :param input_string: string to write
    :return:
    """
    if input_string is None:
        return
    input_string = clean_unreadable(input_string)
    try:
        element.text = input_string
    except ValueError:
        element.text = xml_clean(input_string)