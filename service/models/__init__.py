"""
This module contains all the model objects used by the OAI to JPER connector.

All objects contained in sub-modules are also imported here, so that they can be imported elsewhere directly from this
module.

For example, instead of

::

    from service.models.oaipmh import OAIPMHAll

you can do

::

    from service.models import OAIPMHAll

"""

from service.models.oaipmh import OAIPMHAll, OAIPMHRepo