
import re

from django.utils.functional import memoize
from django.utils.crypto import get_random_string
from django.conf import settings
from django.core.urlresolvers import (
    RegexURLResolver, NoReverseMatch,
    get_callable, normalize, force_unicode,
    get_urlconf, get_script_prefix,
    get_ns_resolver, iri_to_uri,
)

def random_session_key(session, prefix=''):
    key = None
    while not key or (prefix + key) in session:
        key = get_random_string(12)
    return key

_b_resolver_cache = {} # Maps URLconf modules to RegexURLResolver instances.

class BRegexURLResolver(RegexURLResolver):
    """
    from django/core/urlresolvers.py
    modified as noted
    """
    def _reverse_with_prefix(self, lookup_view, _prefix, *args, **kwargs):
        if args and kwargs:
            raise ValueError("Don't mix *args and **kwargs in call to reverse()!")
        try:
            lookup_view = get_callable(lookup_view, True)
        except (ImportError, AttributeError), e:
            raise NoReverseMatch("Error importing '%s': %s." % (lookup_view, e))
        possibilities = self.reverse_dict.getlist(lookup_view)
        prefix_norm, prefix_args = normalize(_prefix)[0]
        for possibility, pattern, defaults in possibilities:
            for result, params in possibility:
                if args:
                    # ## START MODS
                    expected_length = len(params) + len(prefix_args)
                    if len(args) < expected_length:
                        continue
                    args = args[:expected_length]
                    # ## END MODS

                    unicode_args = [force_unicode(val) for val in args]
                    candidate = (prefix_norm + result) % dict(zip(prefix_args + params, unicode_args))
                else:
                    # ## START MODS
                    if set(params + defaults.keys() + prefix_args) - set(kwargs.keys() + defaults.keys()):
                        continue
                    # ## END MODS
                    matches = True
                    for k, v in defaults.items():
                        if kwargs.get(k, v) != v:
                            matches = False
                            break
                    if not matches:
                        continue
                    unicode_kwargs = dict([(k, force_unicode(v)) for (k, v) in kwargs.items()])
                    candidate = (prefix_norm + result) % unicode_kwargs
                if re.search(u'^%s%s' % (_prefix, pattern), candidate, re.UNICODE):
                    return candidate
        # lookup_view can be URL label, or dotted path, or callable, Any of
        # these can be passed in at the top, but callables are not friendly in
        # error messages.
        m = getattr(lookup_view, '__module__', None)
        n = getattr(lookup_view, '__name__', None)
        if m is not None and n is not None:
            lookup_view_s = "%s.%s" % (m, n)
        else:
            lookup_view_s = lookup_view
        raise NoReverseMatch("Reverse for '%s' with arguments '%s' and keyword "
                             "arguments '%s' not found."
                             % (lookup_view_s, args, kwargs))

def get_resolver(urlconf):
    """
    from django/core/urlresolvers.py
    use BRegexURLResolver
    """
    if urlconf is None:
        urlconf = settings.ROOT_URLCONF
    return BRegexURLResolver(r'^/', urlconf)
get_resolver = memoize(get_resolver, _b_resolver_cache, 1)

def fuzzy_reverse(viewname, urlconf=None, args=None, kwargs=None, prefix=None, current_app=None):
    """
    from django/core/urlresolvers.py
    Unmodified reverse (just need to use our modified version of get_resolver)

    With the modified BRegexURLResolver retrieved through get_resolver this will
    not error when you pass in extra args (it assumes proper order and ignores
    trailing "extra" args) OR kwargs (it assumes you are passing at least the
    required keyworded arguments)

    It will still error if you pass both args AND kwargs at the same time.
    """
    if urlconf is None:
        urlconf = get_urlconf()
    resolver = get_resolver(urlconf)
    args = args or []
    kwargs = kwargs or {}

    if prefix is None:
        prefix = get_script_prefix()

    if not isinstance(viewname, basestring):
        view = viewname
    else:
        parts = viewname.split(':')
        parts.reverse()
        view = parts[0]
        path = parts[1:]

        resolved_path = []
        ns_pattern = ''
        while path:
            ns = path.pop()

            # Lookup the name to see if it could be an app identifier
            try:
                app_list = resolver.app_dict[ns]
                # Yes! Path part matches an app in the current Resolver
                if current_app and current_app in app_list:
                    # If we are reversing for a particular app,
                    # use that namespace
                    ns = current_app
                elif ns not in app_list:
                    # The name isn't shared by one of the instances
                    # (i.e., the default) so just pick the first instance
                    # as the default.
                    ns = app_list[0]
            except KeyError:
                pass

            try:
                extra, resolver = resolver.namespace_dict[ns]
                resolved_path.append(ns)
                ns_pattern = ns_pattern + extra
            except KeyError, e:
                if resolved_path:
                    raise NoReverseMatch(
                        "%s is not a registered namespace inside '%s'" %
                        (e, ':'.join(resolved_path)))
                else:
                    raise NoReverseMatch("%s is not a registered namespace" %
                                         e)
        if ns_pattern:
            resolver = get_ns_resolver(ns_pattern, resolver)

    return iri_to_uri(resolver._reverse_with_prefix(view, prefix, *args, **kwargs))
