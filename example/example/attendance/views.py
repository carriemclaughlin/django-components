
import time

from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse

from components.views import Component, Page
from components.forms import BForm
from components.decorators import obj_cache

from .models import AttendanceRecord
from .forms import AttendanceRecordForm

# Step 1

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

# Step 2

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

# Step 3

# Extending AttendanceEntryStep1Component so we can reuse the
# template_name attribute and the init method.
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

# Step 4

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

# Step 5

class AttendanceEntryStep5Component(AttendanceEntryStep3Component):
    template_name = "example/step_5/entry_component.html"

    # You might expect that we'd want to add num_attendees to the `init`
    # method because that's where data initialization is supposed to happen
    # but there is an exception to this, and that is if the thing you want
    # to grab will change based on the handler, the easiest thing to do is
    # to defer grabbing it until `final`.

    # You can experiment on your own and uncomment this and comment out
    # the `final` method in order to see what happens with it in `init`.
    # def init(self):
    #     super(AttendanceEntryStep5Component, self).init()
    #     self.ctx.num_attendees = AttendanceRecord.objects.count()

    def final(self):
        self.ctx.num_attendees = AttendanceRecord.objects.count()

class AttendanceStep5Page(AttendanceStep3Page):
    template_name = "example/step_5/attendance_page.html"

# Step 6

class AttendanceMixin(object):
    # We encourage using Mixins that contain @obj_cache decorated methods
    # that will (or in some cases may) be used by multiple components.
    @obj_cache
    def attendance_list(self):
        # Since order that attendance_list is used may not always be the
        # same, but we know that it'll be iterated through, lets cast
        # it to a list in case len(self.attendance_list) is called first.
        # (Django automatically converts `len(queryset)` into
        # `queryset.count()` if the `queryset` isn't already retrieved
        # from the database (if it is, then django just grabs the len
        # of the objects returned))
        return list(AttendanceRecord.objects.order_by('-id'))

    @obj_cache
    def num_attendees(self):
        # This is free IFF we already need a list of attendees in the
        # request, otherwise  we should be using
        # `AttendanceRecord.objects.count()`

        # Also note that it is fine to chain @obj_cache decorated methods.
        return len(self.attendance_list)

# The rest of this should mostly be stuff that has been covered previously.
# Please use it as a review to make sure nothing is still confusing.
class AttendanceEntryStep6Component(AttendanceMixin, Component):
    template_name = "example/step_5/entry_component.html"

    def init(self):
        self.ctx.this_form_url = self.this_url()

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
            self.add_dependent_component(AttendanceListingStep6Component)
            return True

    def final(self):
        # The @obj_cache decorator turns methods into properties so note
        # that this isn't `self.num_attendees()`
        self.ctx.num_attendees = self.num_attendees

class AttendanceListingStep6Component(AttendanceMixin, Component):
    template_name = "example/step_2/listing_component.html"

    def init(self):
        self.ctx.attendance_list = self.attendance_list

class AttendanceStep6Page(Page):
    template_name = "example/step_6/attendance_page.html"

    def set_components(self):
        self.add_component(AttendanceListingStep6Component)

# Step 7

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


# Step 8

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

# Step 9

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

# Example 10

class AttendanceEntryStep10Component(AttendanceEntryStep9Component):
    template_name = "example/step_10/entry_component.html"

    def handler(self, request):
        ret = super(AttendanceEntryStep10Component, self).handler(request)
        if ret is True:
            self.set_message(message_type="marked_attendance_successfully",
                             message_text="") # message_text is optional

class AttendanceStep10Page(AttendanceStep9Page):
    template_name = "example/step_10/attendance_page.html"
