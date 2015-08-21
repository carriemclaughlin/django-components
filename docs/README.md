**Before looking for specific information about a specific feature of the
framework, we suggest working through the [Component Framework
Tutorial](tutorial/00_intro.md)**

## Table of Contents

* [Background: What?](#background-what)
* [Background: Why?](#background-why)
* [What are the main concepts?](#what-are-the-main-concepts)
  * [Component Class](#the-component-class-componentsviews)
  * [Page Class](#the-page-class-componentsviews)
  * [ObjCache](#objcache-componentsviews)
  * [Mixins](#mixins-standard-python-mixins)
  * [What happens to `request`](#what-happens-to-request-componentsviews)
* [Using Components in the Front-end](#using-components-in-the-front-end)
  * [HTML](#html)
  * [JavaScript](#javascript)
  * [Debugging](#debugging)

## Background: What?
Specialized class based views and sub-views, that facilitate:
* Split page template into components, each of which can be POSTed to and/or
  updated via ajax.
* View code and templates for full page view and ajax update is the same
  code. (very DRY)
* Updating multiple parts of the page with a single request
* Built-in compatibility to handle no-js in most situations (for free)
* Deferred loading of components, for performance

## Background: Why?
* Complex site where content should be easy to change dynamically
* Slow connections overseas (minimize round trips and limit full page loads
  without sacrificing dev time too much)
* Some may not even have JS? Though we don't really cater to them that
  specifically anymore, this was a consideration originally.

## What are the main concepts?

### The Component class (components.views)
* Specific components derive from this class.
* Tied to a template snippet by parameter of the class (search for
  `template_name = …`)
* View code necessary to generate context for the template (`self.ctx.<key>
  = value` in `def init` (not to be confused with `__init__`)
* A URL gets mapped to it, similarly to a Django view, using a special
  function (`component_url(r"^regex/$", ComponentClass, "component_name"[,
  PageClass=PageClass])` in urls.py, instead of the standard `url(...)`)
  * Url maps to component instead of just page because components can be
    used independently and even show up on multiple pages.
  * Django "URL name" is used as the "component key". Component key is used
    to identify the component in various cases.
* Takes care of rendering part of a page on full page GET requests for on
  page load - Page's URL
* Takes care of rendering just the component on AJAX GET requests for
  deferred components (`deferred = True` or `def is_deferred` as component
  attribute) - This component's URL
* Can handle AJAX and non-AJAX POST requests for changing, and also updating
  - This component's URL
* Loads pseudo AJAX GET when the component is claimed as a dependent of
  another component which has been AJAX POSTed to.
  (`self.add_dependent_component(DependentComponentClass)`) (Note that in
  this case, the URL of the component it is dependent on is the URL for the
  request)

#### Methods on the Component Class:
* `def guard(self):` # protects the component against improper or
  unauthorized access
  * returns None if there are no errors
  * returns a dict if there are errors with the following parameters:
    * `"redirect_url": reverse("url_name", kwargs=url_kwargs),`
    * `"always_redirect": True,` # Redirect on ajax and non-ajax instead of
      just non-ajax (if this is False, for ajax requests, the component will
      be replaced with the `str_error` rather than redirecting while a non-
      ajax request will still redirect)
    * `"str_error": "This problem set is no longer open"`
* `def init(self):` # allows you to add information to the context of the
  template, especially if the information will be needed by the handler
* `def handler(self, request):` # Called only for POST requests, this should
  handle form validation and updating objects.
  * Should return True on success, None on error
  * If True is returned and the request is non-ajax, the framework will
    redirect back to the original Page (so that if the user hits refresh the
    browser won't ask if they want to re-submit form data).
  * If the request is ajax, returning True or not returning (or explicitly
    returning None) will simply re-render the component.
* `def final(self):` # If you need to initialize variables for the template
  context after the handler, you can put them in `final` which is run right
  before rendering the templates whether it is a POST or non-POST request.
  It's not yet standard practice, but unless a variable is needed in the
  handler, there is no difference between if you initialize a context
  variable in `init` or in `final`.
* If there is a component that you really need to be inserted into the page
  from inside of another component, you can do that using
  `add_child_component` from within `init` or `final`. (See
  `components/views.py:add_child_compontent` for more info.)

### The Page class (components.views)
* Specific pages derive from this class.
* Represents Full page view, container for components, little to no
  processing happens in this class, since it can't be dynamically updated
  the way components can.
* Tied to a full-page template (called `template_name` for pages as well)
  * Within page template, include a pre-rendered component as
    `{{ components.component_key }} (must be wrapped with
    `<div id="cmp_component_key_id">` to be updated with AJAX)
* Associated with a "main component", for the following purposes:
  * The Page's full-page (ie, non-ajax) URL is this component's URL
  * Any POST requests are handled by the main component code, not the Page
  * Specified in `component_url` (see above)
  * Why would we do this? So that non-js GET/POST requests can look nicer on
    browsers.
* Add extra components in `def set_components()` using
  `self.add_component_safe(ComponentClass)`
* Note: ideally or usually, there is very little actual computation or
  rendering in the page, it should mainly be a container for components.

### ObjCache (components.views)
* Components are designed to operate independently, however since multiple
  components can be rendered in one request, we want to cache data gotten
  from the database (or even memcache), so they're only grabbed once per
  request. For this we use ObjCache which is shared between all components
  and pages.
* Also works on Pages, and the cache is shared with any components in the
  request.
* Specify a key, and a function to get the value. This will memoize it
  between components within a request.

```python
@obj_cache
def key(self):
    # Executed lazily at most once per key per request.
    return get_object_or_404(Model, slug=self.kwargs["some_slug"])
    # note: self.kwargs are the url kwargs.
```
* Works like `property`. ie, `self.key` rather than `self.key()`

### Mixins (standard python mixins)
We strongly encourage use of mixins when multiple Components and/or Pages
use the same information and therefore could share it without extra database
query or processing time using ObjCache shared between the Components and
Pages.

### What happens to `request` (components.views)
* GET vs POST
* Ajax vs non-ajax
  * The framework is designed to avoid needing to distinguish this much.
* Passive vs non-passive
  * If a component is being directly requested, ie, referenced by its URL,
    it is not in passive mode.
  * If a component is processed because it was added as a dependent
    component, it is in passive mode.
* StrippedRequestInfo
  * Very similar to Request, with some modifications.
  * Available as self.request_info within component and page
  * Hides POST if you're in a GET request, or processing the component in passive mode.
  * request_info.passive is available to check

## Using Components in the Front-end

### HTML
Typical usage

```html
<div id="cmp_example_component_id">
    {{ components.example_component }}
</div>
```

### Child components

```django
{% load components %}
    …
{% load_component "example_component" <url kwargs> %}
```

### JavaScript
Add functions to the `vkey` object to use as callbacks for when components
load or refresh `vkey.example_component = function () {};` // where
`example_component` is the same as the URL name Use `vkey.handle` to take
care of default actions

```javascript
vkey.example = function () {
    vkey.handle.apply(this, arguments); // handle component-specific processing
};
```

Refresh a component with JS
```javascript
ajax("example_page").get("/url/", {
    component_key: "example_component"
});
```

POST to a component URL
```javascript
ajax("example_page").post("/url/", { … data … });
```

### Debugging

#### Display component_key/template_name for all components on page.
When your local_settings.py file is set to `DEBUG = True` you automatically
get a new option in the logged in header that displays the component_key and
template_name for every component on the page:

![](https://i.imgur.com/ktyBPe7.png)

If you are looking at a logged out page or a page without the header, you
can maybe run `show_component_debug();` or resort to
`$("div.debug_component_info").show();` from your browsers developer tools
console.

What it looks like:

![](http://i.imgur.com/JPlZQUB.png)

#### A note about deferred components

Deferred components are used just like normal components above. However, you
must use the component's `vkey` callback in order to attach events onload.
That may sound obvious since the component is loaded via ajax, but I've
spent way too much time on several occasions tracking a bug that was
happening because the component was deferred and I didn't notice right away.
