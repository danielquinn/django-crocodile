import logging, os, re, urllib2

from abc import ABCMeta, abstractmethod
from hashlib import md5

from cssmin import cssmin
from django import template
from django.conf import settings
from django.contrib.staticfiles.finders import FileSystemFinder, AppDirectoriesFinder

from ..import __version__

register = template.Library()

@register.tag
def aggregate_js(parser, token):
    """
    Sample:
      {% aggregate_css %}
        {% block css %}
          <link rel="stylesheet" type="text/css" media="screen" href="{{ STATIC_URL }}appname/css/somefile.css" />
          <link rel="stylesheet" type="text/css" media="screen" href="{{ MEDIA_URL }}path/to/something/else.css" />
          <link rel="stylesheet" type="text/css" media="screen" href="https://www.somedomain.ca/path/to/remote/file.css" />
          <style>
            .classname {
              background-image: url("awesome.png");
            }
          </style>
        {% endblock css %}
      {% endaggregate_css %}
    """
    nodelist = parser.parse(('endaggregate_js',))
    parser.delete_first_token()

    return JavascriptNode(nodelist)



@register.tag
def aggregate_css(parser, token):
    """
    Sample:
      {% aggregate_js %}
        {% block js %}
          <script type="text/javascript" src="{{ STATIC_URL }}appname/js/somefile.js"></script>
          <script type="text/javascript" src="{{ MEDIA_URL }}path/to/something/else.js"></script>
          <script type="text/javascript" src="https://www.somedomain.ca/path/to/remote/file.js"></script>
          <script>
            alert("Keep being awesome!");
          </script>
        {% endblock js %}
      {% endaggregate_js %}
    """
    nodelist = parser.parse(('endaggregate_css',))
    parser.delete_first_token()

    return CSSNode(nodelist)



class StaticfileNode(template.Node):

    __metaclass__ = ABCMeta

    def __init__(self, nodelist):
        self.type = ""
        self.nodelist = nodelist


    def render(self, context):

        source_markup = self.nodelist.render(context)

        if not source_markup.strip():
            return ""

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

        if settings.DEBUG or not os.path.exists(cache_filename):

            try:
                output = self._compile(context)
                output = self._compress(output)
            except Exception as e:
                logging.warn("[django-crocodile] Aggregation failure: %s" % e)
                return source_markup

            try:
                os.makedirs(os.path.dirname(cache_filename))
            except OSError:
                pass

            open(cache_filename, "w").write(output.encode("utf-8"))

        return self._markup(cache_filename.replace(
            settings.MEDIA_ROOT,
            settings.MEDIA_URL
        ))


    def _detect_enabled(self):

        if hasattr(settings, "CROCODILE_ENABLE"):
            return settings.CROCODILE_ENABLE
        else:
            return not settings.DEBUG


    def _getfile(self, filename):

        if filename.startswith("http") or filename.startswith("//"):
            return self._fetch_url(filename)

        return self._get_local_file(filename)


    def _get_local_file(self, filename):

        stripped_filename = filename.replace(settings.STATIC_URL, "").replace(settings.MEDIA_URL, "")

        r = FileSystemFinder().find(stripped_filename)

        if not r:
            r = AppDirectoriesFinder().find(stripped_filename)

        if not r:
            logging.warn("[django-crocodile] File not found: %s" % filename)
            return ""

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

        request = urllib2.Request(
            re.sub(r"^//(.*)", r"https://\1", url),
            None,
            {"User-Agent": "django-crocodile %s" % __version__}
        )
        return urllib2.urlopen(request).read().decode("utf-8")



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
                js += self._getfile(path.group(1))
            elif not ignore:
                js += line + "\n"

        return js


    def _compress(self, uncompressed):
        """
        We don't have compression yet.
        """
        return uncompressed


    def _markup(self, file_contents):
        return '<script language="javascript" src="%s?release=%s"></script>' % (
            file_contents,
            urllib2.quote(settings.RELEASE)
        )



class CSSNode(StaticfileNode):

    _fetch_regex = re.compile("url\(\"?'?(.*?)\"?'?\)")
    _current_filename = None  # Hack to work around the passing of an additional argument to self._fix_remote_reference_in_local_file()

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
                    css += self._getfile(source.group(1))
            elif not ignore:
                css += line + "\n"

        return css


    def _compress(self, uncompressed):
        if getattr(settings, "CROCODILE_ENABLE_COMPRESSION", True):
            return cssmin(uncompressed)
        return uncompressed


    def _markup(self, file_contents):
        return '<link rel="stylesheet" href="%s?release=%s" type="text/css" />' % (
            file_contents,
            urllib2.quote(settings.RELEASE)
        )


    def _fetch_url(self, url):
        """
        Assuming the remote URLs contain reasonably-formed CSS using url()
        where appropriate, rework the paths to use complete URLs instead of
        relative ones.
        """

        url = urllib2.urlparse.urlparse(url)
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
            super(CSSNode, self)._fetch_url(url.geturl())
        )


    def _get_local_file(self, filename):

        self._current_filename = filename

        return re.sub(
            self._fetch_regex,
            self._fix_remote_reference_in_local_file,
            super(CSSNode, self)._get_local_file(filename)
        )


    def _fix_remote_reference_in_local_file(self, match):

        url = match.group(1)
        if re.match(r"^https?://.*", url):
            return "url('%s')" % url

        return "url('%s')" % (
            os.path.normpath(
                os.path.join(
                    os.path.dirname(self._current_filename),
                    url
                )
            )
        )
