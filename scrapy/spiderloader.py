# -*- coding: utf-8 -*-
from __future__ import absolute_import
from collections import defaultdict
import traceback
import warnings

from zope.interface import implementer

from scrapy.interfaces import ISpiderLoader
from scrapy.utils.misc import walk_modules
from scrapy.utils.spider import iter_spider_classes


@implementer(ISpiderLoader)
class SpiderLoader(object):
    """
    SpiderLoader is a class which locates and loads spiders
    in a Scrapy project.
    """
    def __init__(self, settings):
        self.spider_modules = settings.getlist('SPIDER_MODULES')
        self._spiders = {}
        self._found = defaultdict(list)
        self._load_all_spiders()

    def _load_spiders(self, module):
        for spcls in iter_spider_classes(module):
            self._found[spcls.name].append((module.__name__, spcls.__name__))
            if spcls.name in self._spiders.keys():
                import warnings
                msg = ("There are several spiders with the same name {!r}:\n"
                       "{}\n    This can cause unexpected behavior.".format(
                            spcls.name,
                            "\n".join(
                                "        {1} (in {0})".format(mod, cls)
                                for (mod, cls) in self._found[spcls.name])))
                warnings.warn(msg, UserWarning)
            self._spiders[spcls.name] = spcls

    def _load_all_spiders(self):
        for name in self.spider_modules:
            try:
                for module in walk_modules(name):
                    self._load_spiders(module)
            except ImportError as e:
                msg = ("\n{tb}Could not load spiders from module '{modname}'. "
                       "Check SPIDER_MODULES setting".format(
                            modname=name, tb=traceback.format_exc()))
                warnings.warn(msg, RuntimeWarning)

    @classmethod
    def from_settings(cls, settings):
        return cls(settings)

    def load(self, spider_name):
        """
        Return the Spider class for the given spider name. If the spider
        name is not found, raise a KeyError.
        """
        try:
            return self._spiders[spider_name]
        except KeyError:
            raise KeyError("Spider not found: {}".format(spider_name))

    def find_by_request(self, request):
        """
        Return the list of spider names that can handle the given request.
        """
        return [name for name, cls in self._spiders.items()
                if cls.handles_request(request)]

    def list(self):
        """
        Return a list with the names of all spiders available in the project.
        """
        return list(self._spiders.keys())
