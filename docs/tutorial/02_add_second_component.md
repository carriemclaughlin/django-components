**Note:** We will be extending the `Component` from step 1 with no changes
rather than copying all of that code. Also, even though we're "adding a
component to an existing page", in order for step 1 to still work in
parallel, we will make and use a copy of the template and to simplify will
remove the comments from the previous step (this pattern will be continued
in future examples).

### In `attendance/views.py`:
```python
# Adding to the imports:
from .models import AttendanceRecord

# Add new views:

class AttendanceEntryStep2Component(AttendanceEntryStep1Component):
    pass

class AttendanceListingStep2Component(Component):
    template_name = "example/step_2/listing_component.html"

    def init(self):
        self.ctx.attendance_list = AttendanceRecord.objects.order_by('-id')

class AttendanceStep2Page(Page):
    template_name = "example/step_2/attendance_page.html"

    def set_components(self):
        # Add the new component as a secondary component.
        # This will make that component also available in the `components`
        # dict in the page template, along with the primary component for
        # this page.
        self.add_component(AttendanceListingStep2Component)
```

### In `attendance/urls.py`:
```python

# Add these urls:
    component_url(r'^2/attendance_listing/$',
                  ComponentClass=views.AttendanceListingStep2Component,
                  name="step_2_listing"),
    component_url(r'^2/$',
                  ComponentClass=views.AttendanceEntryStep2Component,
                  name="step_2_attendance_entry",
                  PageClass=views.AttendanceStep2Page),
```

### In `step_2/listing_component.html`:
```django
<h2>Attendees</h2>

<ul>
    {% for attendance_record in attendance_list %}
        <li>
            {{ attendance_record.name }}
            - {{ attendance_record.arrival_time }}
        </li>
    {% endfor %}
</ul>
```

### In `step_2/attendance_page.html`:
```django
{% extends "base.html" %}

{% block content %}
    {% comment %}
        Adding a secondary component into a page works the same way
        as a primary component from a html perspective:
    {% endcomment %}
    <div id="cmp_step_2_listing_id">
        {{ components.step_2_listing }}
    </div>

    {% comment %}
        Note that order doesn't matter and components is just a dict.
        If you wanted to you could include another template that used
        the components rather than using them in the page.html file.
    {% endcomment %}
    <div id="cmp_step_2_attendance_entry_id">
        {{ components.step_2_attendance_entry }}
    </div>
{% endblock content %}
```

#### [View the result of example 2 locally](http://127.0.0.1:8000/2/)

You'll note that you'll see a list of users that you added when playing
around in example 1, but you won't see any users you newly add until you
refresh the page, move on to
[Example 3: Updating Multiple Components](03_dependent_components.md)
for how to update the list when a new entry is added.

##### Back to [Component Framework Tutorial](00_intro.md)

