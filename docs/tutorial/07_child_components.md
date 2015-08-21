So by now, if you've actually been playing with each example, you probably
have quite a list of "attendees" in your database. Lets add a feature so
that you can delete records.

There are a few ways to do this, each with pros and cons:

    | pro | con
----|-----|-----
Create an old function based django view | familiarity | requires a lot of custom javascript
Adding a handler to the Listing Component | no new components | Component bloat isn't good
Using a child Component | each Component stays simple | new thing to learn


So here, we're going to show you how to use the recommended child Component
method.

### In `attendance/views.py`:
```python

class DeleteAttendeeStep7Component(Component):
    template_name = "example/step_7/delete_attendee.html"

    @obj_cache
    def attendee(self):
        # This is the first time we're dealing with a component that needs
        # to be attached to a specific object. In order to associate the
        # component with an object, url kwargs are used. The framework
        # passes the current url's kwargs though to all `Component`s and
        # `Page`s __init__ function which both add it to the attributes
        # for easy access using `self.kwargs`.
        return get_object_or_404(AttendanceRecord,
                                 id=self.kwargs['attendee_id'])

    def init(self):
        self.ctx.this_form_url = self.this_url()
        # Not actually used this time, but it usually would be
        self.ctx.attendee = self.attendee

        if not self.is_post():
            # In this case, we don't need a specific form (unless you
            # wanted to add a confirmation checkbox or something) because
            # the object is determined by the kwargs of the URL that the
            # form will be POSTing to.

            # In situations like this, we simply use the raw BForm which
            # adds the hidden form fields we need like `page_key` as you
            # may recall from the explanation of BModelForm.
            self.ctx.delete_form = BForm(**self.form_init())

    def handler(self, request):
        self.ctx.delete_form = BForm(request.POST, **self.form_init())
        if self.ctx.delete_form.is_valid():
            self.attendee.delete()
            # Here we're adding both other components as dependent
            # `Component`s because they both are changing, the listing
            # will be getting one fewer item on it, and the entry component
            # will have it's counter of num_attendees go down.

            # You may be thinking "this is somewhat inefficient, we could
            # just have javascript do it", which is true, but that extra
            # javascript adds tech debt and extra time to set up for each
            # action that may update many things on the page.
            self.add_dependent_component(AttendanceListingStep7Component)
            self.add_dependent_component(AttendanceEntryStep7Component)
            return True

class AttendanceListingStep7Component(AttendanceListingStep6Component):
    template_name = "example/step_7/listing_component.html"

    def init(self):
        super(AttendanceListingStep7Component, self).init()
        for attendee in self.ctx.attendance_list:
            # Adding a child component requires two parts, adding it to the
            # view of the "parent" component so that it's available in the
            # template, and then grabbing it in the template.

            # The view portion is handled using `add_child_component` which
            # only requires the `Component` class as an argument.

            # Additional arguments that are often used are `kwargs` and
            # `obj_cache_init`.

            # `kwargs` is the url arguments for the child `Component` since
            # most child `Component`s do not share all kwargs with the
            # parent component.

            # `obj_cache_init` is a dictionary of objects to pre-insert into
            # the `ObjCache` for the child component. Because kwargs aren't
            # shared, and usually there are duplicate child components of
            # the same type on a page displaying different objects, the
            # `ObjCache` also can't be shared. In addition to
            # `obj_cache_init` the other way to "break" the per child
            # `Component` `ObjCache` is by adding extra parameters to the
            # `@obj_cache` decorator, the important one is `force_shared`
            # Example: `@obj_cache('cache_key_name', force_shared=True)`
            # Note: 'cache_key_name' is usually the name of the method, but
            # due to how decorators work, trying to use the `force_shared`
            # kwarg without specifying the first argument would break stuff.

            # An interesting experiment is removing `obj_cache_init` and
            # looking at the SQL panel in the debug toolbar.
            self.add_child_component(DeleteAttendeeStep7Component,
                                     kwargs={'attendee_id': attendee.id},
                                     obj_cache_init={'attendee': attendee})

class AttendanceEntryStep7Component(AttendanceEntryStep6Component):
    # Make it easier to reuse this component going forward the only
    # noteworthy change in this class is using `this_url_fuzzy` instead of
    # `this_url`
    AttendanceListingComponent = AttendanceListingStep7Component

    def init(self):
        # In some situations, `this_url_fuzzy` must be used rather than
        # `this_url`. The difference is the `fuzzy` version allows for there
        # to be extra kwargs as long as all of the required kwargs are
        # present. In this case, Attendance Entry doesn't require any kwargs
        # but when being processed as a dependent component of
        # DeleteAttendee which has the 'attendee_id' kwarg, trying for an
        # exact match would fail.
        self.ctx.this_form_url = self.this_url_fuzzy()

        if not self.is_post():
            self.ctx.attendance_form = AttendanceRecordForm(
                **self.form_init())

    def handler(self, request):
        self.ctx.attendance_form = AttendanceRecordForm(request.POST,
                                                        **self.form_init())
        if self.ctx.attendance_form.is_valid():
            self.ctx.attendance_form.save()
            self.ctx.attendance_form = AttendanceRecordForm(
                **self.form_init())
            self.add_dependent_component(self.AttendanceListingComponent)
            return True

class AttendanceStep7Page(Page):
    template_name = "example/step_7/attendance_page.html"

    def set_components(self):
        self.add_component(AttendanceListingStep7Component)
```

### In `attendance/urls.py`:
```python
# In addition to the normal stuff to add /7/, we add a url with kwargs:
    component_url(r'^7/delete_attendee/(?P<attendee_id>\d+)/$',
                  ComponentClass=views.DeleteAttendeeStep7Component,
                  name="step_7_deleting"),
```

### In `step_7/delete_attendee.html`:
```django
<form method="POST" action="{{ this_form_url }}">
    {% csrf_token %}
    {{ delete_form.as_p }}
    <input type="submit" value="x">
</form>
```

### In `step_7/listing_component.html`:
```django
{# the template tag for adding child components is in `components` #}
{% load components %}

<h2>Attendees</h2>

<ul>
    {% for attendee in attendance_list %}
        <li>
            <div>
                <div style="float: left;">
                    {{ attendee.name }}
                    - {{ attendee.arrival_time }}
                </div>
                <div style="float: left;">
                    {% comment %}
                        the `load_component` template tag takes 1
                        positional argument: `component_key`/name and
                        optional kwargs which correspond to the url kwargs.
                    {% endcomment %}
                    {% load_component 'step_7_deleting' attendee_id=attendee.id %}
                </div>
                <br style="clear: both;">
            </div>
        </li>
    {% endfor %}
</ul>
```

#### [View the result of example 7 locally](http://127.0.0.1:8000/7/)

Child components are great when they're needed, but are usually excessive,
so lets get back to the basics with
[Example 8: Limiting Access to Components](08_guarding_components.md)

##### Back to [Component Framework Tutorial](00_intro.md)
