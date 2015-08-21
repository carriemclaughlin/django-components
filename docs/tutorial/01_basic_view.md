### In `attendance/models.py`:
```python
from django.db import models

class AttendanceRecord(models.Model):
    name = models.CharField(max_length=75)
    arrival_time = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'%s attended at %s (id-%s)' % (self.name,
                                               self.arrival_time,
                                               self.id)
```

### In `attendance/forms.py:`
```python

from components.forms import BModelForm

from .models import AttendanceRecord

# We use BModelForm for most of our ModelForms that are used by the
# Component Framework instead of ModelForm because BModelForm adds special
# parameters that are used by the component framework such as the `page_key`
# to the form. They are initialized by passing in the kwargs return from
# the `form_init()` method on `Component`

# If you aren't familiar with forms, you should google and/or read the docs:
# https://docs.djangoproject.com/en/dev/topics/forms/
class AttendanceRecordForm(BModelForm):
    class Meta:
        model = AttendanceRecord
```

### In `attendance/views.py`:
```python

from components.views import Component, Page

from .forms import AttendanceRecordForm

class AttendanceEntryStep1Component(Component):
    template_name = "example/step_1/attendance_entry_component.html"

    def init(self):
        # self.this_url() returns the url for the specific component.

        # self.ctx is a dictionary of items that will be merged into the
        # template context of both `Page`s and `Component`s. Items can
        # be added to the dict from any method in the respective `Page` or
        # `Component`. It is a special kind of dict that can be accessed
        # using dot notation in addition to standard methods (you may see
        # stuff like `if 'key' not in self.ctx: self.ctx.key = 'something'`)

        # In this line, the component's url will be available by accessing
        # `{{ this_form_url }}` in the template.
        self.ctx.this_form_url = self.this_url()

        # `is_post` returns True if and only if this is a POST request AND
        # this is the `Component` which is being POSTed to. (This can also
        # be thought of as if `is_post` is True, the `handler` will be run,
        # otherwise the `handler` won't be run (see `handler` below))
        if not self.is_post():
            # Set up form for non-POST requests

            # form_init() passes in the extra information needed to
            # initialize the fields automatically added by extending
            # BModelForm.
            self.ctx.attendance_form = AttendanceRecordForm(**self.form_init())

    def handler(self, request):
        # `handler` is only called on POST requests and is only called for
        # the `Component` that is specifically tied to the url that is being
        # POSTed to.

        # Basically `handler` is to handle the form/any changes that need
        # to happen when a `Component` is POSTed to.

        # Is a post request so initialize the form with the POST data
        self.ctx.attendance_form = AttendanceRecordForm(request.POST, **self.form_init())
        if self.ctx.attendance_form.is_valid():
            self.ctx.attendance_form.save()

            # Reset the form because most of the time, the component will be
            # re-rendered and returned in a json dict to be redisplayed and
            # in this case we want to present a new form rather than showing
            # the last name that was entered.
            self.ctx.attendance_form = AttendanceRecordForm(**self.form_init())

            # return True on success so that if this happens to be a
            # non-ajax  request, the framework will automatically redirect
            # back to the page url so that if the user refreshes the page
            # the browser won't automatically try to resubmit the form.
            return True
        # NOTE: the default case (when you don't return anything or
        # explicitly return None) will not automatically redirect, it
        # always re-renders whether that be the full page in a full page
        # POST request or just the component in a ajax POST request. (This
        # means any form errors will be displayed to the user as you would
        # expect)

class AttendanceStep1Page(Page):
    template_name = "example/step_1/attendance_page.html"
```

### In `attendance/urls.py`:
```python

from django.conf.urls import patterns

from components.urls import component_url

from . import views

urlpatterns = patterns(
    '',

    component_url(r'^1/$',
                  ComponentClass=views.AttendanceEntryStep1Component,
                  name="step_1_attendance_entry",
                  PageClass=views.AttendanceStep1Page),
)
```

### In `step_1/attendance_entry_component.html`:
```django
<h2>Add new attendee</h2>
<form method="POST" action="{{ this_form_url }}">
    {% csrf_token %}
    {{ attendance_form.as_p }}
    <input type="submit">
</form>
```

### In `step_1/attendance_page.html`:
```django
{% extends "base.html" %}

{% block content %}
    {% comment %}
        The surrounding div id follows a specific formula so it can be
        automatically updated on ajax requests: `cmp_<component_name>_id`
    {% endcomment %}
    <div id="cmp_step_1_attendance_entry_id">
        {% comment %}
            Similarly, you can grab the rendered html from the component by
            asking for `component_name` from the dictionary of rendered html
            `components`:
        {% endcomment %}
        {{ components.step_1_attendance_entry }}
    </div>
{% endblock content %}
```

* [View the result of step 1 locally](http://127.0.0.1:8000/1/)

After submitting the form, you can use `python manage.py shell` to show
you that the data was actually saved into the database (Future examples will
add various things that change as you submit the form):

```python
>>> from example.attendance.models import AttendanceRecord
>>> AttendanceRecord.objects.all()

[<AttendanceRecord: Sam attended at 2014-08-12 18:13:07.135282+00:00 (id-1)>]
```

This page is rather bland, and we probably want to see the records that
we're adding as we add them, so lets continue with
[Example 2: Adding a second component](02_add_second_component.md)

##### Back to [Component Framework Tutorial](00_intro.md)
