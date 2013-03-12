import os, re

from abc import ABCMeta, abstractmethod
from hashlib import md5
from urllib import quote
from urllib2 import urlopen, urlparse

from cssmin import cssmin
from django import template
from django.conf import settings
from django.contrib.staticfiles.finders import FileSystemFinder, AppDirectoriesFinder

register = template.Library()

@register.tag
def aggregate_js(parser, token):
    """
    """
    nodelist = parser.parse(('endaggregate_js',))
    parser.delete_first_token()

    return JavascriptNode(nodelist)



@register.tag
def aggregate_css(parser, token):
    """
    """
    nodelist = parser.parse(('endaggregate_css',))
    parser.delete_first_token()

    return CSSNode(nodelist)



class StaticfileNode(template.Node):

    __metaclass__ = ABCMeta

    def __init__(self, nodelist):
        self.type = ""
        self.nodelist = nodelist


    def _detect_enabled(self):

        if hasattr(settings, "ENABLE_AGGREGATION"):
            return settings.ENABLE_AGGREGATION
        else:
            return not settings.DEBUG


    def render(self, context):

        source_markup = self.nodelist.render(context)

        if not self._detect_enabled():
            return source_markup

        cache_filename = os.path.join(
            settings.MEDIA_ROOT,
            "cache",
            self.type,
            "%s.%s" % (
                md5(
                    getattr(settings, "RELEASE", "") + source_markup
                ).hexdigest(),
                self.type
            )
        )

        if not os.path.exists(cache_filename):

            output = self._compile(context)
            output = self._compress(output)

            try:
                os.makedirs(os.path.dirname(cache_filename))
            except OSError:
                pass

            open(cache_filename, "w").write(output.encode("utf-8"))

        return self._markup(cache_filename.replace(
            settings.MEDIA_ROOT,
            settings.MEDIA_URL
        ))


    def _getfile (self, filename):

        r = FileSystemFinder().find(filename)

        if not r:
            r = AppDirectoriesFinder().find(filename)

        if not r and filename.startswith("http"):
            return self._fetch_url(filename)

        if not r:
            return "<!-- FILE NOT FOUND: %s -->\n" % filename

        return open(r).read().decode("utf-8", "replace") + "\n"


    @abstractmethod
    def _compile(self, context):
        pass


    @abstractmethod
    def _compress(self, uncompressed):
        pass


    @abstractmethod
    def _markup(self, f):
        pass


    def _fetch_url(self, url):
        return ""



class JavascriptNode(StaticfileNode):

    def __init__(self, *a, **kwa):
        super(JavascriptNode, self).__init__(*a, **kwa)
        self.type = "js"


    def _compile(self, context):

        js = unicode()
        for line in self.nodelist.render(context).split("\n"):

            path = re.match(r"^.*<script.*src=.([^'\"]+).*$", line) # Import js files
            ignore = re.match(r"^.*</?script.*", line)              # Ignore the <script> tags when we're writing straight into the file

            if path:
                js += self._getfile(path.group(1).replace(settings.STATIC_URL, ""))
            elif not ignore:
                js += line + "\n"

        return js


    def _compress(self, uncompressed):
        return uncompressed


    def _markup(self, file_contents):
        return '<script language="javascript" src="%s?release=%s"></script>' % (
            file_contents,
            quote(settings.RELEASE)
        )



class CSSNode(StaticfileNode):

    _fetch_regex = re.compile("url\(\"?'?(.*?)\"?'?\)")

    def __init__(self, *a, **kwa):
        super(CSSNode, self).__init__(*a, **kwa)
        self.type = "css"


    def _determine_file_list(self):
        pass


    def _compile(self, context):

        css = ""

        comment = False
        for line in self.nodelist.render(context).split("\n"):

            if not comment and "<!--" in line:
                comment = True

            if comment:
                if "-->" in line:
                    comment = False
                continue

            source = re.match(r"^.*<link.*href=.([^'\"]+).*$", line) # Import css files
            ignore = re.match(r"^.*</?style.*", line)                # Ignore the <style> tags when we're writing straight into the file

            if source:
                if not re.search(r"media=('|\")?print('|\")?", line):
                    source = source.group(1).replace(settings.STATIC_URL, "")
                    css += self._getfile(source).replace("{{ STATIC_URL }}", settings.STATIC_URL)
            elif not ignore:
                css += line + "\n"

        return css


    def _compress(self, uncompressed):
        return cssmin(uncompressed)


    def _markup(self, file_contents):
        return '<link rel="stylesheet" href="%s?release=%s" type="text/css" />' % (
            file_contents,
            quote(settings.RELEASE)
        )


    def _fetch_url(self, url):
        """
        Assuming the remote URLs contain reasonably-formed CSS using url()
        where appropriate, rework the paths to use complete URLs instead of
        relative ones.
        """

        url = urlparse.urlparse(url)
        return re.sub(
            self._fetch_regex,
            lambda m: "url('%s://%s%s')" % (
                url.scheme,
                url.netloc,
                os.path.normpath(
                    os.path.join(
                        os.path.dirname(url.path),
                        m.group(1)
                    )
                )
            ),
            urlopen(url.geturl()).read().decode("utf-8")
        )
