# django-crocodile

A simple CSS and Javascript aggregator for django

If you're looking for a simple way to aggregate all of your various style
sheets into a single download, and do the same for your JavaScript files, this
is a good start.  Here's how it works:

This is what you probably have on your site.  If you don't, then you probably
don't need an aggregator:

``` xml
{% block css %}
  <link rel="stylesheet" type="text/css" media="screen" href="{{ STATIC_URL }}appname/css/somefile.css" />
  <link rel="stylesheet" type="text/css" media="screen" href="{{ MEDIA_URL }}path/to/something/else.css" />
  <link rel="stylesheet" type="text/css" media="screen" href="https://www.somedomain.ca/path/to/remote/file.css" />
  <style>
    .classname {
      background-image: url("{{ STATIC_URL }}awesome.png");
    }
  </style>
{% endblock css %}

{% block js %}
  <script type="text/javascript" src="{{ STATIC_URL }}appname/js/somefile.js"></script>
  <script type="text/javascript" src="{{ MEDIA_URL }}path/to/something/else.js"></script>
  <script type="text/javascript" src="https://www.somedomain.ca/path/to/remote/file.js"></script>
  <script>
    alert("Keep being awesome!");
  </script>
{% endblock js %}
```

This isn't ideal, since you're left with multiple server hits, sometimes to
remote servers.  In some of the more complex setups, your site could have 10 or
even 20 CSS and/or JS files.  What's more, you probably have `{% block css %}`
and `{% block js %}` subclassed elsewhere on your site, so this list of files
is variable.

Crocodile is setup with a simple template tag:

``` xml
{% aggregate_css %}
  {% block css %}
    <link rel="stylesheet" type="text/css" media="screen" href="{{ STATIC_URL }}appname/css/somefile.css" />
    <link rel="stylesheet" type="text/css" media="screen" href="{{ MEDIA_URL }}path/to/something/else.css" />
    <link rel="stylesheet" type="text/css" media="screen" href="https://www.somedomain.ca/path/to/remote/file.css" />
    <style>
      .classname {
        background-image: url("{{ STATIC_URL }}awesome.png");
      }
    </style>
  {% endblock css %}
{% endaggregate_css %}

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
```

And the output looks something like this:

``` xml
<script src="YOUR_MEDIA_URL/cache/js/md5-sum-of-markup.js?release=YOUR_RELEASE_TAG" />
<script src="YOUR_MEDIA_URL/cache/css/md5-sum-of-markup.css?release=YOUR_RELEASE_TAG" />
```

The contents of `file.css` and `file.js` are the combined payloads of every
file listed between the `{% aggregate_* %} and {% endaggregate_* %}` tags.
This will even include remote files and literal blocks if you put them in
there.


## But What if I Don't Want to Aggregate Everything?

It's entirely possible that you may not want all of these files to be loaded at
once, as in cases where you may want to force the remote loading of some files.
To do that, you just keep those definitions out of the aggregate block:

``` xml
{% aggregate_css %}
  {% block css %}
    <link rel="stylesheet" type="text/css" media="screen" href="{{ STATIC_URL }}appname/css/somefile.css" />
    <link rel="stylesheet" type="text/css" media="screen" href="{{ MEDIA_URL }}path/to/something/else.css" />
    <style>
      .classname {
        background-image: url("{{ STATIC_URL }}awesome.png");
      }
    </style>
  {% endblock css %}
{% endaggregate_css %}

{% block my_special_case_css %}
  <link rel="stylesheet" type="text/css" media="screen" href="https://www.somedomain.ca/path/to/remote/file.css" />
{% endblock my_special_case_css %}
```

Everything outside of the aggregation block is left alone.


## Setup & Installation

To install it into your project, just use `pip`.  Either using pypi:

``` bash
$ pip install django-crocodile
```

Or you can grab the development version through GitHub:

``` bash
$ pip install git+git://github.com/danielquinn/django-crocodile.git#egg=django-crocodile
```

Once you've got it, you'll need to add it to your `INSTALLED_APPS` in your
`settings.py` file.  Some additional values you might want to tinker with are:

* `RELEASE`
  * This is the release version of your project.  `django-crocodile` will
    append this value in the form of `?release=RELEASE` so you don't have to
    worry about users caching your old CSS values.
* `CROCODILE_ENABLE`
  * If this is set to `True`, aggregation will occur even when `DEBUG = True`.
* `CROCODILE_ENABLE_COMPRESSION`
  * CSS compression is enabled by default.  Setting this value to `False`
    will disable it.

And that's it, now go about wrapping your markup and see what happens!


## TODO

* A management script to blow away the cache files.  Just to make things a
  little cleaner than forcing you to run `rm /path/to/media/root/cache/{css,js}/*`
* Medium-aware CSS is still sketchy.  Basically it currently grabs all CSS
  files that aren't set to `media="print"` and dumps them into the aggregated
  `.css` file.  If you have a printable .css file, it's best to keep it out of
  your aggregation block for this reason.
  * Other media types are just rolled into the aggregated file, so that may
    cause some headaches.
* Exploder-specific CSS tags (`<!-- if IE lt 8>`) are also ignored.  *Ew*.


## But Why "Crocodile"?

Because it's an *aggregator*, which is like *alligator*... get it?  Shut up,
I'm hilarious.


## Disclaimers

This is all still pretty new, so use at your own risk.
