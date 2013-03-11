django-crocodile
================

A simple CSS and Javascript aggregator for django

If you're looking for a simple way to aggregate all of your various style sheets into a single download, and do the same for your JavaScript files, this is a good start.  Here's how it works:

This is what you probably have on your site.  If you don't, then you probably don't need an aggregator:

``` xml
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

    {% block js %}
      <script type="text/javascript" src="{{ STATIC_URL }}appname/js/somefile.js"></script>
      <script type="text/javascript" src="{{ MEDIA_URL }}path/to/something/else.js"></script>
      <script type="text/javascript" src="https://www.somedomain.ca/path/to/remote/file.js"></script>
      <script>
        alert("Keep being awesome!");
      </script>
    {% endblock js %}
```

This isn't ideal, since you're left with multiple server hits, sometimes to remote servers.  In some of the more complex setups, your site could have 10 or even 20 CSS and/or JS files.  What's more, you probably have `{% block css %}` and `{% block js %}` subclassed elsewhere on your site, so this list of files is variable.

Crocodile is setup with a simple template tag:

``` xml
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
    <script src="YOUR_MEDIA_URL/path/to/cached/file.js?release=YOUR_RELEASE_TAG" />
```

The contents of `file.css` and `file.js` are the combined payloads of every file listed between the `{% aggregate_* %} and {% endaggregate_* %}` tags.  This will even include remote files and literal blocks if you put them in there.

It's entirely possible that you may not want all of these files to be loaded at once, as in cases where you may want to force the remote loading of come files.  To do that, you just keep those definitions out of the aggregate block:

``` xml
    {% aggregate_css %}
      {% block css %}
        <link rel="stylesheet" type="text/css" media="screen" href="{{ STATIC_URL }}appname/css/somefile.css" />
        <link rel="stylesheet" type="text/css" media="screen" href="{{ MEDIA_URL }}path/to/something/else.css" />
        <style>
          .classname {
            background-image: url("awesome.png");
          }
        </style>
      {% endblock css %}
    {% endaggregate_css %}

    {% block remote_css %}
      <link rel="stylesheet" type="text/css" media="screen" href="https://www.somedomain.ca/path/to/remote/file.css" />
    {% endblock remote_css %}
```

Everything outside of the aggregation block is left alone.

## Setup & installation

To install it into your project, just use `pip`:

``` bash
    $ pip install git+git://github.com/danielquinn/django-crocodile.git
```

Once you've got it, you'll need to add it to your `INSTALLED_APPS` in your `settings.py` file.  Note as crocodile won't automatically run when `DEBUG` is set to `True`, you can force it to run by setting `ENABLE_AGGREGATION = True` in your `settings.py` file.

That's it, now go about wrapping your markup and see what happens!


## TODO

* Medium-aware CSS is still sketchy.  Basically it currently grabs all CSS files that aren't set to `media="print"` and dumps them into the aggregated `.css` file.  If you have a printable .css file, it's best to keep it out of your aggregation block for this reason.
  * Other media types are just rolled into the aggregated file, so that may cause some headaches.
* Exploder-specific CSS tags (`<!-- if IE lt 8>`) are also ignored.  Ew.

This is all still pretty new, so use at your own risk.

