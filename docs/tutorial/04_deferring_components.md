Say you have a component that is slow to load that you need to show up on a
page but that maybe isn't the main thing that someone is wanting to look at
on the page. We're going to pretend the "listing" component is very slow and
defer it in this example by adding a `sleep(1)` to the init method.

Note that the only actual change necessary from previous examples is adding
the `deferred = True` attribute to the class you want deferred.

### In `attendance/views.py`:
```python
class AttendanceListingStep4Component(AttendanceListingStep2Component):
    deferred = True
    def init(self):
        super(AttendanceListingStep4Component, self).init()
        time.sleep(1)

class AttendanceEntryStep4Component(AttendanceEntryStep1Component):
    def handler(self, request):
        result = super(AttendanceEntryStep4Component, self).handler(request)
        if result is True:
            self.add_dependent_component(AttendanceListingStep4Component)
        return result

class AttendanceStep4Page(Page):
    template_name = "example/step_4/attendance_page.html"

    def set_components(self):
        self.add_component(AttendanceListingStep4Component)
```

### In `attendance/urls.py`:
```python
# New views:
    component_url(r'^4/attendance_listing/$',
                  ComponentClass=views.AttendanceListingStep4Component,
                  name="step_4_listing"),
    component_url(r'^4/$',
                  ComponentClass=views.AttendanceEntryStep4Component,
                  name="step_4_attendance_entry",
                  PageClass=views.AttendanceStep4Page),
```

### In `step_4/attendance_page.html`:
```django
{% extends "base.html" %}

{% block content %}
    <div id="cmp_step_4_listing_id">
        {{ components.step_4_listing }}
    </div>

    <div id="cmp_step_4_attendance_entry_id">
        {{ components.step_4_attendance_entry }}
    </div>
{% endblock content %}
```

This should mean that on initial page load, you'll see a spinner for a
second in place of the listing component utils the listing component is
available for display:

![](https://i.imgur.com/SlXKYZb.png)

#### [View the result of example 4 locally](http://127.0.0.1:8000/4/)

Note: if a component set as a `deferred` component is loaded as a dependent
component it is not deferred in the current implementation of the framework.
If this becomes an issue it shouldn't be that hard to change, but for now,
most of the time, deferred components aren't also used as dependent
components.

Continue with [Example 5: Using final vs init](05_using_final.md) to learn
about how to take into account data changing within a POST request.

##### Back to [Component Framework Tutorial](00_intro.md)

