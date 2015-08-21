## Intro

This tutorial will walk you through how to use the Component Framework by
creating an example web page that tracks attendance at an event. All of the
relevant code changes will be in each example file, but the whole thing is
also included as en axample app [here](../../example/README.md), after you
set up the example, you can access the pages at the `/<example number>/`
endpoints.

Once you've worked your way through the tutorial, the
[Component Framework overview doc](../overview.md) may help clear up further
questions and possibly may serve as an easier reference.

## Examples:

* [**Example 1**](01_basic_view.md) Creating an initial page to display a
  simple input form for when someone "walks in".

* [**Example 2**](02_add_second_component.md) Using multiple components on
  the same page.

* [**Example 3**](03_dependent_components.md) Using add_dependent_component
  to update multiple components at the same time.

* [**Example 4**](04_deferring_components.md) Using `deferred = True` to
  defer the rendering of a specific component on initial page load.

* [**Example 5**](05_using_final.md) Using `final` to grab information after
  the `handler` which would otherwise have changed the information in the
  database but not in `self.ctx`

* [**Example 6**](06_object_cache.md) Using `obj_cache` to share information
  between `Component`s (Note: it also works the same way between
  `Component`s and `Page`s, though too much info being needed in the page
  could be a sign that you should add a new `Component`)

* [**Example 7**](07_child_components.md) When you need to display a
  `Component` within another `Component`, especially when you need to
  display many `Component`s within another `Component`, we add child
  `Component`s using `add_child_component` and `load_component`.

* [**Example 8**](08_guarding_components.md) Using `guard`s to prevent users
  from accessing `Component`s they shouldn't be able to access

* [**Example 9**](09_working_with_request.md) Grabbing stuff from the
  request object in the Component Framework even when it isn't explicitly
  passed to where you need it


* [**Example 10**](10_success_messages.md) Providing reliable way of
  signaling the frontend that a form has successfully been submitted
  (whether the next change in display is over ajax or a full page load after
  a "success redirect to self")

* [**Extra**: Advanced Topics](../advanced_topics.md)
