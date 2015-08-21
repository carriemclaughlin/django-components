
import json
import urllib
from hashlib import md5

from django.contrib import messages
from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.shortcuts import render
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseNotFound,
    HttpResponseBadRequest,
    QueryDict,
)
from django.views.generic import View
from django.template.loader import render_to_string
from django.template import RequestContext, Context
from django.utils.safestring import mark_safe
from django.utils.functional import cached_property

from .utils import fuzzy_reverse, random_session_key
from .forms import BForm

COMPONENT_KEYS = {'to_component_class': {}, 'from_component_class': {}}
PAGE_KEYS = {'to_page_class': {}, 'from_page_class': {}}

def should_load_partial_page(request):
    """
    Return True if this request should return a partial page, ie only
        renders of updated components
    Return False if this request should return a full page render

    In the usual case, ajax requests return partial pages, and non-ajax
    requests render full pages. However, in very rare cases we want to
    load a full page via ajax for use in a modal box or something like
    that. In which case, we will add the `force_full_page` parameter to
    the request.

    An example of this are modal solvables on any of the feed pages.
    """
    if not request.is_ajax() and request.REQUEST.get('redirect_if_not_ajax'):
        # in this case, we're likely redirecting because the page render
        # would be too much trouble, so don't bother rendering it
        return True
    else:
        return request.is_ajax() and request.REQUEST.get('force_full_page', 'false') != 'true'

class StrippedRequestInfo(object):
    def __init__(self, request_obj, page_key, kwargs, POST=None, passive=False):
        # request_obj can be a requests or a StrippedRequestInfo

        self.user = request_obj.user
        self.method = request_obj.method

        # Passes the following bound functions to the other object.
        # Should stay bound to the original object:
        self.is_ajax = request_obj.is_ajax
        self.is_secure = request_obj.is_secure

        self.is_execute_request = getattr(request_obj, 'is_execute_request', False)

        self.page_key = page_key
        self.passive = passive
        self.GET = request_obj.GET
        self.META = request_obj.META
        if hasattr(request_obj, 'LANGUAGE_CODE'):
            self.LANGUAGE_CODE = request_obj.LANGUAGE_CODE
        self.session = request_obj.session
        self.path = request_obj.path
        if hasattr(request_obj, 'get_full_path'):
            # probably the same as checking isinstance(StrippedRequestInfo)
            # but I don't want to change logic at this point.
            self.full_path = request_obj.get_full_path()
        else:
            self.full_path = request_obj.full_path

        self._kwargs = kwargs

        # make sure we didn't just put None in one of these
        # This test may be outdated now that we're passing GET around for passive
        assert self.passive or POST is not None

        if POST is not None:  # remember {} is not the same as None
            self.POST = POST

class ComponentBadRequestData(BaseException):
    pass

class ComponentError(BaseException):
    pass

class ObjectCache(object):
    def __init__(self, init=None):
        self.data = {}
        if init:
            for key in init:
                if init[key] is not None:
                    self.data[key] = init[key]


    def __call__(self, key, func):
        if key not in self.data:
            self.data[key] = func()
        return self.data[key]

    def reset(self, key):
        if key in self.data:
            del self.data[key]

    def set(self, key, val):
        """
        Like __call__, but doesn't take a function.
        Useful if you already have the object (example: when it's initially created)
        """
        self.data[key] = val
        return val

    @staticmethod
    def get_key_for_child_component(raw_key, kwargs):
        kwargs = kwargs or {}
        return u"%s[%s]" % (raw_key, md5(unicode(sorted(kwargs.items()))).hexdigest())

class AttributeDict(dict):
    """
    Subclass of dict to support attribute-based value assignment:
    > my_dict.foo_bar = "binbaz"
    > print my_dict.foo_bar
    binbaz
    """
    def __setattr__(self, key, val):
        if key in ATTRIBUTE_DICT_RESTRICTED_ARGS:
            raise KeyError("'%s' is a restricted argument for AttributeDict")
        self[key] = val

    def __getattr__(self, key):
        return self[key]

ATTRIBUTE_DICT_RESTRICTED_ARGS = dir(AttributeDict)

class ComponentsRenderDict(dict):
    """
    Subclass of dict to throw a different exception so that
    it will throw an exception in the template
    """
    def __init__(self, *args, **kwargs):
        super(ComponentsRenderDict, self).__init__(*args, **kwargs)
        self.not_added_component_keys = []
        self.non_existent_component_keys = []
        self.accessed_keys = []

    def __getitem__(self, key):
        try:
            value = super(ComponentsRenderDict, self).__getitem__(key)
        except KeyError:
            if key not in COMPONENT_KEYS['to_component_class']:
                self.non_existent_component_keys.append(key)
            else:
                self.not_added_component_keys.append(key)
            raise
        self.accessed_keys.append(key)
        return value


class FrameworkBaseMixin(object):
    def check_guard(self, component):
        if self.guard_fail:
            # if the deferred component has a "worse" guard failure use it
            if (not self.guard_fail['always_redirect']
                    and component.guard_fail
                    and component.guard_fail['always_redirect']):
                self.guard_fail = component.guard_fail
        else:
            self.guard_fail = component.guard_fail

    @property
    def is_moderator(self):
        return (self.user.is_active
                and (self.user.is_staff
                     or self.user.profile.flags.is_discussions_moderator))

    def get_param_key(self, component_key, kwargs):
        return md5(reverse(component_key, kwargs=kwargs)).hexdigest()

class Component(FrameworkBaseMixin):
    """
    A `Component` represents a chunk of content on our site and allows for
    advanced manipulation and interaction of the content in a structured and
    standardized way.

    `Component`s each have their own url specified by a `component_url`, but
    you can't point a browser to a `Component`'s url unless the `component_url`
    is also given a `PageClass`.

    `Component`s who don't have `PageClass`es can still be used in a variety
    of ways:

        1)  They can be added as a *secondary component* to a `Page` using the
            `add_component` method on `Page`.

        2)  If used on a `Page` with any other `Component` that has a `handler`
            method that `Component` can add another `Component` as a
            *dependent component* by using the `add_dependent_component`
            method on `Component` (Note, you must `guard_dependent_component`
            first)

        3)  They can be added as a *child component* to another `Component`
            by using the `add_child_component` method on `Component`

    Note that any `Component` is basically the same as any other `Component`
    and the only thing that determines how they can be used is how you use them.

    For example, it is possible to use a component as both a secondary
    component and a child component on two different pages.


    Independent of all of above ways `Component`s can be used, you can also
    alter the behaviour:

        1)  The main way being converting it into a *deferred component*
            which can simply be done by setting the `deferred` attribute
            to True on the `Component`. This makes it so that where possible,
            the *Component Framework* will not render the `Component` in the
            same request as any other `Component`s and will instead have the
            *Component Framework* javascript dispatch a request to grab the
            contexts of that `Component` independently. This is typically
            done for `Component` that have poor performance and aren't the
            primary information that the user wants to look at when they end up
            on the page.
        2)  A more advanced thing is to use `override_page_key` which is only
            used if you are working on a `Component` that has a `PageClass`
            attached but is used on other `Page`s also. What it does is make
            it so that if you POST to the `Component` from another `Page`
            it will ignore the other page and instead use the guards/page
            template of it's own `Page` where applicable (for instance if there
            are form errors on a non-ajax POST and the `Page` needs to be
            rerendered with the error messages shown).

    """

    ###########
    # attributes to set/change to Customize your Component
    ###########
    template_name = None

    # Set to True to defer a component.
    deferred = False

    # Set to True if POSTing to this component should use this Component's
    # page_key (aka component_key) rather than the page_key passed in through
    # the form.
    override_page_key = False

    def __init__(self, request_info, obj_cache, response_message=None, guard_only=False, param_key=None):
        self.component_key = self.get_component_key()

        self.request_info = request_info
        self.user = request_info.user
        self.kwargs = request_info._kwargs
        self.dependent_request_info = StrippedRequestInfo(self.request_info,
                                                          self.request_info.page_key,
                                                          self.request_info._kwargs,
                                                          passive=True)
        self.ctx = AttributeDict()
        self.response_message = response_message or {}
        self.extra_response_headers = {}

        # This stands for 'parameterized key', it consists of an md5
        # of the url of the component with url arguments
        # included. It's for components where we need to specify kwargs
        # rather than just using the ones from the original request.
        self.param_key = param_key

        self.blank = False

        self.dependent_components = []
        self.dependent_component_classes = []
        self.guarded_dependent_component_classes = []
        self.child_component_classes = []
        self.child_components = []

        self.obj_cache = obj_cache

        self.run_guards()
        if not self.guard_fail and not guard_only and not self.defer_this_request(request_info):
            self.init()

    ###########
    # Methods to override to customize your component
    ###########

    def is_deferred(self):
        """
            The way the framework user defers a component conditionally.
            This method is only called once per component by the framework.
        """
        return self.deferred

    def guard(self):
        """
            This method "guards" the component from being run in a situation
            that it shouldn't be run for.

            See `guard_active_user` for an example of what to return.

            Returns `None` when there were no failures.
        """
        pass
    guard.original = True

    def init(self):
        """
            Use `init` to initialize variables for use in the handler and
            the template context.

            If you just need something for the component's other methods, you
            can store stuff to `self` (`self.my_variable = True`)

            If you need something for the template (and possibly the component)
            you can store it to `self.ctx` (`self.ctx.my_variable = True`)
        """
        pass

    def handler(self, request):
        """
            This method should contain the actions that happen given a POST
            request to this component's url.

            It should return True if the POST succeeded, and None if the POST
            form validation failed. Can also return an HttpResponseRedirect
            for the view to return if you have a special case.

            You can also `self.add_dependent_component` here,
            and also alter `self.ctx` as desired.
        """
        pass

    def final(self):
        """
            Runs after init and handler. This is to do any calculations  and
            set any template context that should come after handler but needs
            to happen even when handler isn't run.
        """
        pass

    def login_redirect_next_url(self, include_get=False):
        """
        After logging in, what is the URL the user should be forwarded
        to? This is meant to be overridden by certain components,
        particularly ones whose kwargs don't match up with the Page's.
        """
        get_string = ''
        if include_get:
            get_string = '?%s' % self.request_info.GET.urlencode()
        try:
            return "%s%s" % (fuzzy_reverse(self.request_info.page_key,
                                           kwargs=self.kwargs),
                             get_string)
        except NoReverseMatch:
            raise BaseException('Page required kwargs not used in the Component')

    ###########
    # Methods you can call from your components
    ###########

    def is_post(self):
        return not self.request_info.passive and self.request_info.method == "POST"

    def guard_dependent_component(self, DependentComponentClass):
        """
            This method should be called from a component's `guard` method only
            when the component is NOT passive to guard Components who will
            possibly be added as dependent components in this request.

            Example:
            def guard(self):
                guard_response = self.guard_active_user()
                if (not self.request_info.passive) and guard_response is None:
                    self.guard_dependent_component(PointsComponent)
                return guard_response
        """
        if self.request_info.passive:
            raise ComponentError("Passive components shouldn't guard dependent components. "
                                 "This prevents infinite loops.")
        else:
            self.guarded_dependent_component_classes.append(DependentComponentClass)

    def add_dependent_component(self, DependentComponentClass):
        """
            Use this method to tell the framework that a component has content
            that may have changed based on the handler of the `self` component.

            Dependent components should should be passive (read-only).

            Note: Make sure the component is properly guarded with
            `guard_dependent_component` first.
        """
        if (DependentComponentClass not in self.guarded_dependent_component_classes
                and DependentComponentClass.has_guard()):
            raise ComponentError(
                "Tried adding %s as a dependent component for %s, "
                "without guarding it first (and it has a guard defined)." %
                (DependentComponentClass.get_component_key(), self.component_key)
            )
            return
        if self.request_info.passive:
            raise ComponentError("You shouldn't add a dependent component if you're passive. "
                                 "This prevents infinite loops.")
        else:
            self.dependent_component_classes.append(DependentComponentClass)

    def add_child_component(self, ChildComponentClass, kwargs=None, obj_cache_init=None):
        """
            Adds the child component, and initializes the obj_cache keys for
            this child component's particular set of args/kwargs
        """
        if obj_cache_init:
            for raw_key, val in obj_cache_init.iteritems():
                child_specific_key = self.obj_cache.get_key_for_child_component(raw_key, kwargs)
                self.obj_cache.set(child_specific_key, val)
        self.child_component_classes.append((ChildComponentClass, kwargs))

    def form_init(self):
        """
            When you create a form with BForm (which is standard practice) it
            requires 'page_key' be added to the initialization
            of the form so that they can be added as hidden fields.

            Example:
                self.ctx.form = BForm(**self.form_init())
        """
        if not hasattr(self, '_form_init_cached'):
            self._form_init_cached = {'page_key': self.request_info.page_key}
            if self.param_key is not None:
                self._form_init_cached['param_key'] = self.param_key
        return self._form_init_cached

    def set_message(self, message_type, message_text=''):
        self.response_message['message_type'] = message_type
        self.response_message['message_text'] = message_text

    def this_url(self):
        return self.component_reverse(kwargs=self.kwargs)

    @classmethod
    def component_reverse(cls, kwargs=None):
        kwargs = kwargs or {}
        return reverse(cls.get_component_key(), kwargs=kwargs)

    def this_url_fuzzy(self):
        return self.fuzzy_component_reverse(kwargs=self.kwargs)

    @classmethod
    def fuzzy_component_reverse(cls, kwargs=None):
        kwargs = kwargs or {}
        return fuzzy_reverse(cls.get_component_key(), kwargs=kwargs)

    @classmethod
    def get_component_key(cls):
        return COMPONENT_KEYS['from_component_class'][cls]

    # Guards that can be used in other guards

    def guard_active_user(self, include_get=False):
        """
            Example:
            def guard(self):
                return self.guard_active_user()
        """
        if not self.user.is_active:
            return self.login_redirect_dict(include_get=include_get)

    def guard_active_user_on_post(self):
        if self.is_post():
            return self.guard_active_user()

    def guard_staff_user(self):
        if not self.user.is_staff:
            return self.login_redirect_dict(str_error='You must be Staff to do that')

    ### Guard helper functions

    def login_redirect_url(self, include_get=False):
        login_url = getattr(settings, 'LOGIN_URL', '/')
        next_url = self.login_redirect_next_url(include_get=include_get)
        if next_url:
            return "%s?next=%s" % (login_url, urllib.quote_plus(next_url))
        else:
            return login_url

    def login_redirect_dict(self,
                            str_error='You must be logged in to view that page',
                            include_get=False):
        return {'str_error': str_error,
                'redirect_url': self.login_redirect_url(include_get=include_get),
                'always_redirect': True}

    ###########
    # Internal methods
    ###########

    @cached_property
    def component_is_deferred(self):
        """
            The way the framework checks if a component is deferred.
        """
        # bool to make it safe to return None
        return bool(self.is_deferred())

    def run_guards(self):
        self.guard_fail = self.guard()

        for ComponentClass in self.guarded_dependent_component_classes:
            component = ComponentClass(self.dependent_request_info, self.obj_cache, guard_only=True)
            self.check_guard(component)

    def get_response_action_tuple(self, request):
        return ((self.param_key or self.component_key), self.response_action_dict(request))

    def response_action_dict(self, request):
        return {
            'new_html': self.render(request),
            'component_key': self.component_key
        }

    def _get_context(self, request):
        final_context = self.ctx

        message_type = self.response_message.get('message_type')
        message_text = self.response_message.get('message_text')
        if message_type is not None:
            final_context['message_type'] = message_type
        if message_text is not None:
            final_context['message_text'] = message_text

        final_context['request_info'] = self.request_info
        final_context['components'] = ComponentsRenderDict(self.render_child_components(request))
        final_context['component_info'] = self._get_component_info()

        return final_context

    def _get_component_info(self):
        """
        Used in the template context for the component and also for
        the deferred template message.
        """
        return {
            'url': lambda: fuzzy_reverse(self.component_key, kwargs=self.kwargs),
            'page_url': lambda: fuzzy_reverse(self.request_info.page_key, kwargs=self.kwargs),
            'component_key': self.component_key,
            'param_key': self.param_key,
            'page_key': self.request_info.page_key,
        }

    def render_debug_extra(self):
        return mark_safe("""<div class="debug_component_info" style="display:none">
                                component_key: %s; template_name: %s
                            </div>""" % (self.component_key, self.template_name))

    def render(self, request, is_child=False):
        if self.blank:
            render_output = self._render_blank(request)
        elif self.defer_this_request(request, is_child):
            render_output = self._render_deferred(request)
        else:
            render_output = self._render(request)
        if getattr(settings, 'DEBUG', False) and getattr(settings, 'COMPONENT_DEBUG_INFO', True):
            render_output = self.render_debug_extra() + render_output
        return render_output

    def _render(self, request):
        context = RequestContext(request, self._get_context(request))
        return render_to_string(self.template_name, context_instance=context)

    def _render_deferred(self, request):
        uastr = request.META.get('HTTP_USER_AGENT', '').lower()
        # don't show the no-js warning to search bots -- they see it 5 times
        # on a page and think it's important
        bots = (
            'googlebot', 'mediapartners', 'adsbot', # google
            'bingbot', 'adidxbot', 'msnbot', 'bingpreview', # bing, yahoo
        )
        search_bot = any(bot in uastr for bot in bots)
        context = Context({
            'component_info': self._get_component_info(),
            'get_params': request.META.get('QUERY_STRING', '').replace('force_full_page=true', '_=_'),
            'search_bot': search_bot,
        })
        return render_to_string('includes/defer_loading.html', context_instance=context)

    def _render_blank(self, request):
        """Render blank (or show debug info) if a component
        fails to be showable. This is usually an error state."""

        debug_str = "No render available for %s - %s - %s" % (
            self.component_key, self.param_key, self.request_info._kwargs
        )
        if getattr(settings, 'DEBUG', False):
            return debug_str
        if not self.user.is_staff:
            # Staff may see blank things that are incomplete
            raise ComponentError(debug_str)
        return ""

    def render_child_components(self, request):
        child_renders = []
        for child in self.child_components:
            key = child.param_key or child.component_key
            child_renders.append((key, child.render(request, is_child=True)))
        return child_renders

    def run_handler(self, request):
        return self.handler(request)

    def defer_this_request(self, request, is_child=False):
        if not self.component_is_deferred:
            return False

        if is_child and getattr(self, 'defer_as_child', False):
            return True

        # Not deferred if this component is being POSTed to or is no_js
        # request or deferred is set.
        # Note: The frontend sends `deferred=true` when it is requesting
        # the content for a previously deferred component
        return (not self.is_post()
                and not request.GET.get('no_js', False)
                and not request.GET.get('deferred') == 'true')

    def init_child_components(self, request_info):
        """
        Initialize child components. This must happen after this
        component's init and before render.

        The idea is that this function may be called from Page or
        ComponentView to recursively elaborate all child components
        """
        for ComponentClass, kwargs in self.child_component_classes:
            component_key = ComponentClass.get_component_key()

            if kwargs is not None:
                param_key = self.get_param_key(component_key, kwargs)
            else:
                kwargs = request_info._kwargs
                param_key = None

            # We don't want to accidently post to one of the children here.
            request_info = StrippedRequestInfo(request_info, request_info.page_key,
                                               kwargs, passive=True)

            component = ComponentClass(request_info, self.obj_cache, param_key=param_key)

            if component.guard_fail:
                component.blank = True
            elif not component.defer_this_request(request_info, is_child=True):
                component.final()
                component.init_child_components(request_info)

            self.child_components.append(component)

    def init_dependent_components(self, request):
        """
        Initialize dependent components that have been added via
        the handler. This is deferred to make sure it runs after both
        the handler has done any relevant updates on data in obj_cache.
        """
        if should_load_partial_page(request):
            for ComponentClass in self.dependent_component_classes:
                new_component = ComponentClass(self.dependent_request_info, self.obj_cache)

                new_component.final()
                new_component.init_child_components(self.request_info)
                self.dependent_components.append(new_component)

    @classmethod
    def has_guard(cls):
        return not getattr(cls.guard, 'original', False)

class BasicFormComponent(Component):
    """
    For components that handle a basic form

    You can extend form_class if you want and even use a form that takes extra
    kwargs using `extra_form_init_kwargs`

    NOTE: instead of `init` use `final` or make sure you include `super`
    Similarly, use `success_handler` instead of `handler`

    The template will get `form` initially and on form validation failure (and
    also if you don't return True or HttpResponseRedirect from `success_handler`)
    and also it will have `this_url` for POSTing to.
    """
    form_class = BForm

    def extra_form_init_kwargs(self):
        """
        Extend this if you want to use a form that requires extra initialization
        """
        return {}

    def _get_kwargs(self):
        kwargs = self.form_init()
        kwargs.update(self.extra_form_init_kwargs())
        return kwargs

    def extra_init(self):
        pass

    def init(self):
        self.extra_init()
        self.ctx.this_url = self.this_url_fuzzy()
        if not self.is_post():
            self.ctx.form = self.form_class(**self._get_kwargs())

    def success_handler(self, request):
        raise NotImplementedError('Please implement a success_handler(self, request)')

    def handler(self, request):
        self.ctx.form = self.form_class(request.POST, request.FILES, **self._get_kwargs())
        if self.ctx.form.is_valid():
            return self.success_handler(request)

class Page(FrameworkBaseMixin):
    """
    `Component`s define subsections of html on a page. The renderings are
    typically displayed inside of a div tag. `Component`s do not deal with
    items such as the header and footer, typically those elements are part
    of the `Page`s template.

    `Page`s only exist for urls that will be rendered synchronously.
    urls that exist only to support ajax loading don't have `Page`s attached
    to them. You attach a `Page` to a `Component` (and thus give it a url that
    can be navigated to) by adding it using the `PageClass` keyword argument
    on the `Component`'s `component_url` definition in a urls file.

    Note: Both `Page`'s and `Component`'s  don't use traditional `url`
    definition methods, they both need `component_url`.

    If we consider a django view, which is referenced by a url and renders
    a single main template as a single part, the ComponentFramework renders
    multiple parts separately:
    1) a primary component referenced in the url spec
    2) ancillary components specified by the page or by other components
    3) the page, also referenced in the url spec; glues everything together

    `Page`s should not depend on changes in the request, if you want something
    to change, it should be made into another Component so that it can be
    updated using `add_dependent_component`.

    Similarly, you can't `POST` to a page.
    """

    template_name = None

    def __init__(self, obj_cache, component=None, request_info=None,
                 response_message=None, guard_only=False, **kwargs):
        # The else can probably never happen anymore; get_page always
        # acts on a component
        if component:
            self.request_info = component.request_info
        else:
            self.request_info = request_info

        self.user = self.request_info.user
        self.kwargs = self.request_info._kwargs

        # The key of the Page's principal component. This may be different
        # from component.component_key if, for instance, a ancillary component
        # is being posted to.
        self.page_key = PAGE_KEYS['from_page_class'][self.__class__]

        self.new_component_request_info = StrippedRequestInfo(
            self.request_info, self.request_info.page_key,
            self.request_info._kwargs, passive=True)
        self.response_message = response_message or {}

        self.obj_cache = obj_cache
        self.ctx = AttributeDict()

        self.guard_only = guard_only
        self.guard_done = False

        self.set_components_full(requested_component=component)

        self.run_guards()
        if not self.guard_only:
            if self.guard_fail:
                raise ComponentError("By the time non-guard_only Page comes around, "
                                     "Page should have passed all guards.")
            self.guard_done = True
            self.init()

        self.components_render_dict = ComponentsRenderDict()

    ##########
    # Methods you can override in your `Page` class
    ##########

    def set_components(self):
        """
            Override set_components to add secondary components to the page
            using the `add_component` method.
        """
        pass

    def init(self):
        """
            Same as Component.init basically.
        """
        pass

    def get_page_context(self):
        """
            Add variables to the template context.
            NOTE: Depricated, use self.ctx.template_var_name = value in `init`.
        """
        return {}

    ##########
    # Methods to call from your `Page` class methods:
    ##########

    def add_component(self, NewComponentClass, kwargs=None):
        """
        This takes a component class, initializes it, and adds the
        initialized object to self.components, also adding the class
        to self.component_classes

        Add the component iff it has not already been added.
        """
        if self.guard_done:
            raise ComponentError("You should add components in set_components, not init")

        if NewComponentClass not in COMPONENT_KEYS['from_component_class']:
            raise ComponentError("%s not registered (via urls.py)" % NewComponentClass.__name__)

        new_component_key = COMPONENT_KEYS['from_component_class'][NewComponentClass]

        if kwargs is not None:
            lookup_key = md5(reverse(new_component_key, kwargs=kwargs)).hexdigest()
        else:
            lookup_key = new_component_key

        if lookup_key in self.components:
            return

        if self.response_message.get('component_key') == new_component_key:
            component_response_message = self.response_message
        else:
            component_response_message = {}

        if kwargs is not None:
            param_key = lookup_key
            ncri = self.new_component_request_info
            request_info = StrippedRequestInfo(
                ncri, ncri.page_key, kwargs,
                POST=None, passive=ncri.passive)
        else:
            param_key = None
            request_info = self.new_component_request_info

        new_component = NewComponentClass(
            request_info, self.obj_cache,
            response_message=component_response_message,
            guard_only=self.guard_only, param_key=param_key)

        if not self.guard_only and not new_component.defer_this_request(self.request_info):
            new_component.final()
            new_component.init_child_components(self.request_info)

        self.components[lookup_key] = new_component
        self.component_classes[lookup_key] = NewComponentClass

    def this_url(self):
        return self.page_reverse(kwargs=self.kwargs)

    @classmethod
    def page_reverse(cls, kwargs=None):
        kwargs = kwargs or {}
        page_key = PAGE_KEYS['from_page_class'][cls]
        return reverse(page_key, kwargs=kwargs)

    ############
    # Internal methods:
    ############

    def set_components_full(self, requested_component):
        """
            Adds all the components for the Page, including those explicitly
            specified by the derived class, and also some added by default.
            This is not designed for overriding.
        """

        self.components = {}
        self.component_classes = {}
        if requested_component:
            self.components[requested_component.component_key] = requested_component
            self.component_classes[requested_component.component_key] = requested_component.__class__

        self.set_components()

        # always add the page's primary component by default, if it hasn't been added
        primary_component_class = COMPONENT_KEYS['to_component_class'][self.page_key]
        self.add_component(primary_component_class)

    def _get_context(self, request):
        final_context = self.ctx
        final_context.update(self.get_page_context())
        final_context['components'] = self.components_render_dict
        final_context['has_component'] = dict.fromkeys(self.components.keys(), True)
        for key, component in self.components.items():
            final_context['components'][key] = component.render(request)
        final_context['request_info'] = self.request_info
        return final_context

    def run_guards(self):
        self.guard_fail = None

        for component in self.components.itervalues():
            self.check_guard(component)

    @staticmethod
    def _add_component_class_name(component_key):
        return "%s (%s)" % (COMPONENT_KEYS['to_component_class'][component_key].__name__,
                            component_key)

    def handle_component_key_errors(self):
        if self.components_render_dict.non_existent_component_keys:
            msg = ("Undefined component key(s): %s \n\n Make sure you add them in urlconf "
                   "or check your spelling. Available ones are: \n\n %s"
                   % ("\n".join(self.components_render_dict.non_existent_component_keys),
                      "\n".join(map(self._add_component_class_name,
                                    COMPONENT_KEYS['to_component_class'].keys()))))
            raise ComponentError(msg)

        if self.components_render_dict.not_added_component_keys:
            msg = ("Attempting to display unprocessed component(s): %s. \n\n "
                   "Make sure you add them in set_components of your Page"
                   % ("\n".join(map(self._add_component_class_name,
                                    self.components_render_dict.not_added_component_keys))))
            raise ComponentError(msg)

        if (getattr(settings, 'DEBUG', False)
                and not getattr(settings, 'SKIP_UNUSED_COMPONENTS_EXCEPTION', False)):
            unused_components = []
            for key, component in self.components.items():
                if key not in self.components_render_dict.accessed_keys:
                    unused_components.append(component.component_key)
            if unused_components:
                msg = ("You added the following components which were not used "
                       "in the template for this request:\n\n%s"
                       % "\n".join(map(self._add_component_class_name, unused_components)))
                raise ComponentError(msg)

def get_page_key(request, component_class):
    page_key = request.REQUEST.get('page_key')
    if isinstance(page_key, list):
        page_key = page_key[0]

    is_main_component = ((not page_key)
                         and request.method in ['GET', 'HEAD']
                         and (not should_load_partial_page(request)))

    if is_main_component or component_class.override_page_key:
        # presuming this component is the main component of a page,
        # it should share the same key as the page
        page_key = component_class.get_component_key()

    if page_key not in PAGE_KEYS['to_page_class']:
        if "Googlebot" not in request.META.get('HTTP_USER_AGENT', ''):
            raise ComponentBadRequestData("Didn't get a valid page_key! got: %s at %s"
                                          % (page_key, request.path))

        # Signal to return 404 without the exception so DebugIssue gets
        # saved into the DB without a rollback. Also, perhaps we shouldn't
        # 404 for non-post + non-ajax cases? Or there still may be no choice
        # since we'd need the page key?
        return None

    return page_key

def get_page(request,
             obj_cache,
             component=None,
             component_class=None,
             request_info=None,
             response_message=None,
             guard_only=False):
    if component:
        component_class = component.__class__
        request_info = component.request_info

    PageClass = PAGE_KEYS['to_page_class'][get_page_key(request, component_class)]

    return PageClass(obj_cache,
                     component=component,
                     request_info=request_info,
                     response_message=response_message,
                     guard_only=guard_only)

class ComponentView(FrameworkBaseMixin, View):
    """
    The view that handles all components.
    Which component it handles is specified in URLConf.
    """

    # Needed so that as_view can accept it.
    component_key = None
    ComponentClass = None
    init_obj_cache = None

    def __init__(self, **initkwargs):
        initkwargs['init_obj_cache'] = initkwargs.get('init_obj_cache', {})
        super(ComponentView, self).__init__(**initkwargs)

        # This should run on server startup, so no surprise 500s
        if not initkwargs.get('component_key') and initkwargs.get('ComponentClass'):
            raise ValueError("ComponentView needs a ComponentClass passed into as_view")

        self.component_key = initkwargs['component_key']
        self.ComponentClass = initkwargs['ComponentClass']

    def _get_component(self, request, kwargs):
        """
        This instantiates the attached component class object, runs guards, and
        (if the request type is ajax) calls the function's init.

        It returns the a two-tuple consisting of the component, and a
        boolean indicating if the component guard has failed.
        """
        request_info = StrippedRequestInfo(request, self.page_key, kwargs, POST=request.POST)

        if self.response_message and self.response_message['component_key'] == self.component_key:
            response_message = self.response_message
        else:
            response_message = {}

        if should_load_partial_page(request):
            component = self.ComponentClass(request_info, self.obj_cache,
                                            response_message=response_message,
                                            param_key=request.REQUEST.get('param_key'))
            return component, component.guard_fail
        else:
            guard_component = self.ComponentClass(
                request_info, self.obj_cache, response_message=response_message,
                guard_only=True)
            if not getattr(guard_component, 'bypass_page_guard', False):
                guard_page = get_page(
                    self.request, self.obj_cache, component=guard_component,
                    response_message=self.response_message, guard_only=True)
                if guard_page.guard_fail:
                    return None, guard_page.guard_fail

            # Get an initialized component
            component = self.ComponentClass(request_info, self.obj_cache,
                                            response_message=response_message)
            return component, component.guard_fail

    def sanity_check(self, request):
        """
        Just some quick checks, so we don't redirect to external sites
        """
        if request.REQUEST.get('redirect_if_not_ajax'):
            if request.REQUEST['redirect_if_not_ajax'][0] != "/":
                # require relative links
                return False
            if request.REQUEST['redirect_if_not_ajax'][:2] == "//":
                # //someotherhost.com would work
                return False
        return True

    def _common_init(self, request, kwargs, grab_submit_success=False):
        if not self.sanity_check(request):
            return HttpResponseBadRequest()

        self.obj_cache = ObjectCache(init=self.init_obj_cache)
        self.page_key = get_page_key(request, self.ComponentClass)
        if self.page_key is None:
            return HttpResponseNotFound(render_to_string('404.html'))

        self.response_message = None
        if grab_submit_success:
            submit_success = ((not should_load_partial_page(self.request))
                              and self.request.GET.get('submit_success'))
            if submit_success:
                self.response_message = self.request.session.get(
                    'success_data:' + submit_success)
                if self.response_message is not None:
                    del self.request.session['success_data:' + submit_success]

        self.component, guard_fail = self._get_component(request, kwargs)

        if guard_fail:
            return self._get_guard_fail_response(request, kwargs, guard_fail)

    def post(self, request, **kwargs):
        """
        Post should only ever target one component, either via ajax,
        or via feeding all the other components the request with the
        POST data stripped from it.

        The framework referes to idempotent methods as "passive" and
        the converse as "active", although the only idempotent action
        supported is GET and the only non-idempotent method is POST.
        """
        ret = self._common_init(request, kwargs)
        if ret is not None:
            return ret

        self.response_message = None

        # Run the handler. Get a response, if any.
        handler_result = self.component.run_handler(request)
        self.component.final()
        passive_ri = StrippedRequestInfo(request, self.page_key, kwargs, passive=True)
        self.component.init_child_components(passive_ri)
        self.component.init_dependent_components(request)

        return self._get_http_response(handler_result, kwargs)

    def get(self, request, **kwargs):
        ret = self._common_init(request, kwargs,
                                grab_submit_success=True)
        if ret is not None:
            return ret

        if not self.component.defer_this_request(request):
            self.component.final()
        passive_ri = StrippedRequestInfo(request, self.page_key, kwargs, passive=True)
        self.component.init_child_components(passive_ri)

        return self._get_http_response(None, kwargs)

    def _get_http_response(self, handler_result, component_kwargs):
        # Handle ajax vs non-ajax requests
        if not self.request.is_ajax() and self.request.REQUEST.get('redirect_if_not_ajax'):
            response = HttpResponseRedirect(self.request.REQUEST['redirect_if_not_ajax'])
            return self._add_response_headers(response)
        elif should_load_partial_page(self.request):
            # Load just the component(s) that we need to
            # (primary component of the request + dependent compontents)
            if isinstance(handler_result, HttpResponseRedirect):
                response_dict = {'redirect': handler_result["Location"]}
            else:
                actions = [self.component.get_response_action_tuple(self.request)]
                actions += [c.get_response_action_tuple(self.request)
                            for c
                            in self.component.dependent_components]
                response_dict = {
                    'actions': dict(actions),
                }
            response = json_response(response_dict)
            if "redirect" in response_dict:
                setattr(response, "form_submit_redirect", True)
            return self._add_response_headers(response)
        else:
            # full page request
            if isinstance(handler_result, HttpResponseRedirect):
                return self._add_response_headers(handler_result)
            elif handler_result is True:
                # POST request succeded, so auto-redirect for full page request
                get_string = ''

                if ('message_type' in self.component.response_message
                        or 'message_text' in self.component.response_message):
                    data_session_key = random_session_key(self.request.session,
                                                          prefix="success_data:")
                    self.request.session['success_data:' + data_session_key] = {
                        'component_key': self.component.component_key,
                        'message_type': self.component.response_message['message_type'],
                        'message_text': self.component.response_message['message_text'],
                    }
                    get_string = "?submit_success=" + data_session_key

                return self._add_response_headers(HttpResponseRedirect(
                    fuzzy_reverse(self.page_key, kwargs=component_kwargs) + get_string))
            else:
                # Show full page when not directed otherwise.
                page = get_page(self.request,
                                self.obj_cache,
                                component=self.component,
                                response_message=self.response_message)
                page_render = render(self.request,
                                     page.template_name,
                                     page._get_context(self.request))
                page.handle_component_key_errors()
                return self._add_response_headers(page_render)

    def _get_guard_fail_response(self, request, kwargs, guard_fail):
        if request.is_ajax():
            return self._add_response_headers(json_response(
                {
                    "messages": ([{'message_type': 'error',
                                   'message_text': guard_fail['str_error']}]
                                 if ((not guard_fail['always_redirect'])
                                     and ('str_error' in guard_fail))
                                 else None),
                    "redirect": (guard_fail['redirect_url']
                                 if guard_fail['always_redirect']
                                 else None)
                }
            ))
        else:
            if 'str_error' in guard_fail:
                messages.error(request, guard_fail['str_error'])
            return self._add_response_headers(HttpResponseRedirect(guard_fail['redirect_url']))

    def _add_response_headers(self, response):
        """
        Add any custom headers to the response object
        """
        if not hasattr(self, "component") or not self.component:
            return response
        all_components = self.component.dependent_components + [self.component]
        for component in all_components:
            for key, value in component.extra_response_headers.items():
                if isinstance(key, unicode):
                    key = key.encode("utf-8")
                if isinstance(value, unicode):
                    value = value.encode("utf-8")
                response[key] = value
        return response

def execute_request(request,
                    url_name,
                    args=None,
                    init_obj_cache=None,
                    kwargs=None,
                    full_passthrough=False):
    """
    Loads a component and returns its render as the response to the
    current request.

    Note that this forces the request to GET and eliminates
    parameters. That means it breaks any view for loading
    via ajax.
    """
    if init_obj_cache is None:
        init_obj_cache = {}
    if args is None:
        args = []
    ComponentClass = COMPONENT_KEYS['to_component_class'][url_name]
    view = ComponentView.as_view(
        ComponentClass=ComponentClass, component_key=url_name,
        init_obj_cache=init_obj_cache)
    if kwargs:
        request.path = reverse(url_name, kwargs=kwargs)
    else:
        request.path = reverse(url_name, args=args)

    if not full_passthrough:
        request.method = "GET"
        request.POST = QueryDict({})

        ALLOWED_GET_KEYS = ('v', 'format', 'pretty')
        passthrough_dict = dict((k, v) for k, v in request.GET.iteritems() if k in ALLOWED_GET_KEYS)
        request.GET = QueryDict('').copy()
        request.GET.update(passthrough_dict)

        request._request = {}
    request.is_execute_request = True
    if kwargs:
        return view(request, **kwargs)
    else:
        return view(request, *args)

def json_response(obj, status=200):
    '''
    Return a json response.
    '''
    return HttpResponse(json.dumps(obj), mimetype='application/json', status=status)
