This is where more advanced topics are mentioned with maybe where you can
look for more info if you really need them. These topics should be things
that you only need to know if it has been requested as part of a feature,
rather than an implicit requirement to completing a feature.

### Analytics (Not available in the example code)

Look around for `self.track_event` or `def track_event`.

### Turning a page into a Modal

This can be a very advanced thing to need to do, and there are a few ways of
doing it:

1. Simply load a modal with a deferred `Component` as it's content. Deferred
   `Component`s are actually not loaded until they come into view (you
   unhide them or scroll down to them), so this is actually rather
   efficient.

2. If you need to convert an advanced page that already has several
   interconnected `Component`s on it into a model (for instance, the problem
   solving interface) you'll probably actually want to specially load a
   special stripped down version of the page that doesn't contain a header
   or footer, but does contain multiple components. In order for this to
   work, you need to use the `?force_full_page=true` parameter so that
   framework knows to display not just the `Component` associated with the
   url, but also the `Page`.

##### Back to [Component Framework Tutorial](tutorial/00_intro.md)

For more info, check out the [Component Framework overview doc](README.md)
and possibly more informatively, the doc-strings and comments in the
[base/views.py](../components/views.py) file itself.
