Thus far, we've only "explicitly" accessed stuff from `request` when the
`request` object is passed into the `handler` methods.

We decided early on that even though you don't need it often, a lot of stuff
in request should be available to all `Component`s and `Page`s. The way
these are available is via `self.request_info` which isn't actually the
`request` object itself. `self.request_info` is actually a
`StrippedRequestInfo` object which attaches various things from `request`
onto itself. Most notably, it passes `GET`, `method`, `is_ajax`, `META`,
`session`, `path`, `get_full_path` as `full_path` and `POST`. Note that
`POST` is only passed through for the instance of `StrippedRequestInfo` that
is attached to the primary `Component`. `POST` is NEVER set for non-
POSTed to components.

In order to show how `request_info` works, we'll change the example so that
you can turn on and off showing the `AttendanceListingComponent` using a
`GET` variable.

#### In `attendance/views.py`:
```python
class AttendanceEntryStep9Component(AttendanceEntryStep7Component):
    def handler(self, request):
        self.ctx.attendance_form = AttendanceRecordForm(request.POST, **self.form_init())
        if self.ctx.attendance_form.is_valid():
            self.ctx.attendance_form.save()
            self.ctx.attendance_form = AttendanceRecordForm(**self.form_init())
            if self.request_info.session.get('show_attendance_listing', False):
                self.add_dependent_component(self.AttendanceListingComponent)
            return True

class AttendanceStep9Page(Page):
    template_name = "example/step_9/attendance_page.html"

    def set_components(self):
        show_attendance_listing = self.request_info.GET.get(
            'show_attendance_listing',
            self.request_info.session.get('show_attendance_listing',
                                          'true')) in ('true', True)
        if show_attendance_listing != self.request_info.session.get('show_attendance_listing'):
            self.request_info.session['show_attendance_listing'] = (show_attendance_listing)

        if show_attendance_listing:
            self.add_component(AttendanceListingStep7Component)
```

#### In `step_9/attendance_page.html`:
```django
{% extends "base.html" %}

{% block content %}

    {% comment %}
        If you have a component that you want to conditionally show on a
        page and don't want to duplicate the logic between the view and the
        template (because you really shouldn't /want/ to do that) you should
        use `has_components` which is basically a dictionary with
        `component_key`s as the keys and `True` as the values for only those
        `component_key`s that are also in the `components` dict.
    {% endcomment %}
    {% if has_component.step_7_listing %}
        <div id="cmp_step_7_listing_id">
            {{ components.step_7_listing }}
        </div>
    {% endif %}

    <div id="cmp_step_9_attendance_entry_id">
        {{ components.step_9_attendance_entry }}
    </div>
{% endblock content %}
```

* [View the no-listing result of example 9 locally](http://127.0.0.1:8000/9/?show_attendance_listing=false)
* [use the session state](http://127.0.0.1:8000/9/)
* [toggle listing back on](http://127.0.0.1:8000/9/?show_attendance_listing=true)

Alright, almost done, in fact this was supposed to be the end of the
tutorial, but because when it's useful, it's very useful, I'll throw in
[Example 10: Success messages](10_success_messages.md)

##### Back to [Component Framework Tutorial](00_intro.md)
