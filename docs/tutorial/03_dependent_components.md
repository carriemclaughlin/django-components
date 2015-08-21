The only thing that's really being changed here is we're adding
`add_dependent_component(AttendanceListingStep2Component)` to the handler.
Note that this would be a 1 line change if we actually made the change to
`AttendanceEntryStep1Component` rather than keeping example 1 and 2 working
the same way as they were when you were looking through examples 1 and 2.

### In `attendance/views.py`:
```python
# Extending AttendanceEntryStep1Component so we can reuse as much as possible.
class AttendanceEntryStep3Component(AttendanceEntryStep1Component):
    def handler(self, request):
        # If we were starting from scratch, we would add the following
        # right before return True, but instead, since we're extending
        # a component who already has a handler we want to use, we can
        # grab the result, and add code if the handler was successful.
        result = super(AttendanceEntryStep3Component, self).handler(request)
        if result is True:
            self.add_dependent_component(AttendanceListingStep2Component)
        return result

class AttendanceStep3Page(Page):
    template_name = "example/step_3/attendance_page.html"

    def set_components(self):
        # Reusing the component from step 2 because nothing about it needs
        # to change.
        self.add_component(AttendanceListingStep2Component)
```

### In `attendance/urls.py`:
```python

# Add this component_url:
    component_url(r'^3/$',
                  ComponentClass=views.AttendanceEntryStep3Component,
                  name="step_3_attendance_entry",
                  PageClass=views.AttendanceStep3Page),
```

### In `step_3/attendance_page.html`
```
{% extends "base.html" %}

{% block content %}
    <div id="cmp_step_2_listing_id">
        {{ components.step_2_listing }}
    </div>

    {# Note: the only change is 3 instead of 1 or 2. #}
    <div id="cmp_step_3_attendance_entry_id">
        {{ components.step_3_attendance_entry }}
    </div>
{% endblock content %}
```

Now, when you add a name, it immediately updates the list.

#### [View the result of example 3 locally](http://127.0.0.1:8000/3/)

If you use chrome debug tools you can see the response that is sent back.
For your convenience, here is what I just grabbed (and then formatted):

```json

{
    "actions": {
        "step_3_attendance_entry": {
            "component_key": "step_3_attendance_entry",
            "new_html": "
                <form method=\"POST\" action=\"/3/\">
                    <div style=\"display:none\">
                        <input type=\"hidden\" name=\"csrfmiddlewaretoken\" value=\"....\">
                    </div>
                    <p><label for=\"id_name\">Name:</label>
                    <input id=\"id_name\" type=\"text\" name=\"name\" maxlength="75" />
                    <input type=\"hidden\" name=\"page_key\"
                        value=\"step_3_attendance_entry\" id=\"id_page_key\" />
                    <input type=\"hidden\" name=\"param_key\" id=\"id_param_key\" />
                    <input type=\"submit\">
                </form>"
        },
        "step_2_listing": {
            "component_key": "step_2_listing",
            "new_html": "
                <ul>
                    <li>George - Aug. 12, 2014, 1:46 p.m.</li>
                    <li>Ruth - Aug. 12, 2014, 1:46 p.m.</li>
                    <li>Joseph - Aug. 12, 2014, 1:23 p.m. </li>
                    <li>Steph - Aug. 12, 2014, 1:22 p.m.</li>
                    <li>Lily - Aug. 12, 2014, 1:22 p.m.</li>
                    <li>Andy - Aug. 12, 2014, 12:09 p.m.</li>
                    <li>Sarah - Aug. 12, 2014, 11:13 a.m.</li>
                </ul>"
        }
    }
}
```

Each action is handled by a javascript handler which can be
overridden/extended for more advanced functionality, but by default it
replaces the existing contents of the div having id `cmp_<component_key>_id`
with the contents of `new_html` so in a POST request to the entry
`Component`, we updated both the entry `Component` and the listing
`Component`

Continue to [Example 4: Deferring components](04_deferring_components.md) to
learn about the easiest way to deal with slow `Component`s and make `Page`
loading feel a lot faster.

##### Back to [Component Framework Tutorial](00_intro.md)

