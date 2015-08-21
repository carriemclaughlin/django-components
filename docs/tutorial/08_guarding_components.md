You may have noticed that up until this point in the tutorial, you could be
logged in or logged out and all of the examples would have worked.
Typically, when you're letting people access or enter information and
certainly when you are letting them delete it, they should at a minimum be
logged into the site, if not staff.

In order to provide an easy way to block access, we made the `guard` method
on `Component`s that is called before the Component can be used.

Especially in this example, it's suggested that you play around starting
with the previous example's code, adding the specified guards and seeing
what happens.

Note 1: if you guard a child component that doesn't succeed, it
will render a blank template on the live site, and locally, it'll print out
a warning that there is a component that isn't being displayed. If you
encounter a message like this, typically, the solution is to add logic
before `self.add_child_component` so that it only gets added if it would
pass the guards.

Note 2: If you want a child component to show up conditionally and don't
want to duplicate logic between the view and the template (which is always
discouraged), use the `ignore_missing=1` kwarg on the `load_component`
template tag and put all of the control logic in the view.

### In `attendance/views.py`:
```python
class AttendanceListingStep8Component(AttendanceListingStep7Component):
    template_name = "example/step_8/listing_component.html"
    deletion_component_name = 'step_8_deleting'

    # `guard` methods simply check conditions and return None if there are
    # no guard failures or when there is a guard failure, it should return
    # a special dict with instructions on what to do.
    def guard(self):
        # The most common guard that we use is "require that user is logged
        # in". Because it occurs so often, we've added it to the base
        # `Component` class so that you don't have to repeat the logic all
        # over the place (search for guard_active_user in base/views.py):

        # return self.guard_active_user()

        # HOWEVER, since it's annoying to set up authentication for an
        # example app, we're going to bypass it.

        return None

    @property
    def DeleteAttendeeComponent(self):
        return DeleteAttendeeStep8Component

    def init(self):
        super(AttendanceListingStep7Component, self).init()
        self.ctx.deletion_component_name = self.deletion_component_name

        # Since we're `guard`ing against non-staff users being able to see
        # the `DeleteAttendeeComponent` (see the `guard` method in
        # `DeleteAttendeeComponent`) we should short circuit before
        # trying to add `DeleteAttendeeComponent` as a child component.
        if not self.user.is_staff:
            return
        for attendee in self.ctx.attendance_list:
            self.add_child_component(self.DeleteAttendeeComponent,
                                     kwargs={'attendee_id': attendee.id},
                                     obj_cache_init={'attendee': attendee})

class AttendanceEntryStep8Component(AttendanceEntryStep7Component):
    AttendanceListingComponent = AttendanceListingStep8Component

    def guard(self):
        # This is an poor example of a custom guard.
        # Other examples of where a guard would be used is making sure that
        # a user viewing a "paywalled" problem has paid or that edit options
        # only show up on content that you have permission to edit.

        # We're basically saying here, that the request can't have a GET
        # parameter of fail_guard
        if not self.request_info.GET.get('pass_guard', False):
            return {
                # `redirect_url` is the URL the user should be redirected to
                'redirect_url': reverse('homepage'),

                # `always_redirect` redirects even for ajax responses.
                # If `always_redirect` is False, ajax responses will instead
                # show the text that is included in this dict under the key
                # `str_error`.
                'always_redirect': True,

                # `str_error` is displayed if an ajax request has
                # `always_redirect` set to False OR if it is a full page
                # request, `str_error` will be added as a django framework's
                # `messages.error` which will be displayed on the next page.

                # `str_error` is optional.
                'str_error': 'You must include a `pass_guard` GET parameter to view that page',
            }

        # Because the Attendance Entry `Component` has a dependent component
        # we want to make sure the dependent `Component`s `guard` runs prior
        # to the handler being run. It would be bad if the guard redirected
        # the user to some random place after state was changed in the
        # handler (which would mean the fact that state was changed would
        # be hidden from the user)

        # `guard_dependent_component` is all that's needed, but ONLY if
        # this is the component that is being POSTed to so that we don't
        # get into infinite loops because multiple `Component`s with
        # `guard`s are interdependent:
        if self.is_post():
            self.guard_dependent_component(self.AttendanceListingComponent)

class DeleteAttendeeStep8Component(DeleteAttendeeStep7Component):
    AttendanceListingComponent = AttendanceListingStep8Component
    AttendanceEntryComponent = AttendanceEntryStep8Component

    def guard(self):
        # `guard_staff_user` is like `guard_active_user`, but instead
        # makes sure that the user viewing the component has `user.is_staff`

        # when using a default guard in a component that needs to guard
        # dependent `Component`s we typically store this `Component`s guard
        # result and return before adding the dependent `guard`s if there
        # is an actual failure:
        guard_result = self.guard_staff_user()
        if guard_result is not None:
            return guard_result

        if self.is_post():
            self.guard_dependent_component(self.AttendanceListingComponent)
            self.guard_dependent_component(self.AttendanceEntryComponent)

    def handler(self, request):
        self.ctx.delete_form = BForm(request.POST, **self.form_init())
        if self.ctx.delete_form.is_valid():
            self.attendee.delete()
            self.add_dependent_component(self.AttendanceListingComponent)
            self.add_dependent_component(self.AttendanceEntryComponent)
            return True

class AttendanceStep8Page(Page):
    template_name = "example/step_8/attendance_page.html"

    def set_components(self):
        self.add_component(AttendanceListingStep8Component)
```

The only interesting url/template change is here:
### In `step_8/listing_component.html`:
```django
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
                        We're using a variable instead of hardcoding the
                        component_name/key so that we can more easily
                        extend the listing component in later examples.

                        Also, ignore_missing is added so that if we end up
                        not adding the component due to the viewing user
                        not being staff, we won't get a warning locally.
                    {% endcomment %}
                    {% load_component deletion_component_name attendee_id=attendee.id ignore_missing=1 %}
                </div>
                <br style="clear: both;">
            </div>
        </li>
    {% endfor %}
</ul>
```

#### [View the result of example 8 locally](http://127.0.0.1:8000/8/)
#### [Pass the Guard](http://127.0.0.1:8000/8/?pass_guard=yes)

This is the last of the hard examples, you're getting there! Continue with
[Example 9: What happens to `request`](09_working_with_request.md)

##### Back to [Component Framework Tutorial](00_intro.md)
