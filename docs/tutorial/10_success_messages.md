So it probably bugged you in the first example that when you submitted a
name, nothing on the page changed. This was improved when the list and the
count of attendees improved, but there is an easier solution if the action
that is being performed doesn't immediately show up. We use the
`set_message` method which adds specific variables to the template only once
and it also handles situations where a user is redirected after a successful
full page POST request.

Note: we don't actually use this that often because often we "show" the user
what action they've performed (for instance, by shifting focus onto the
comment they just posted) rather than "telling" them that it succeeded.

#### In `attendance/views.py`:
```python
class AttendanceEntryStep10Component(AttendanceEntryStep9Component):
    template_name = "example/step_10/entry_component.html"

    def handler(self, request):
        ret = super(AttendanceEntryStep10Component, self).handler(request)
        if ret is True:
            self.set_message(message_type="marked_attendance_successfully",
                             message_text="") # message_text is optional

class AttendanceStep10Page(AttendanceStep9Page):
    template_name = "example/step_10/attendance_page.html"
```

#### In `step_10/entry_component.html`:
```django
<h2>Add new attendee</h2>

Add a new attendee (Currently {{ num_attendees }} attending)

<form method="POST" action="{{ this_form_url }}">
    {% csrf_token %}
    {% if message_type == 'marked_attendance_successfully' %}
    <div style="color: green;" id="saved_div">
        {# Note: we could also use {{ message_text }} here if we set it #}
        Saved!
    </div>
    <script type="text/javascript">
        var oldonload = window.onload || function () {};
        window.onload = function () {
            $('#saved_div').fadeOut(3000);
            oldonload.call(window);
        };
        (function () {
            $('#saved_div').fadeOut(3000);
        })();
    </script>
    {% endif %}
    {{ attendance_form.as_p }}
    <input type="submit">
</form>
```

* [View the result of example 10 locally](http://127.0.0.1:8000/10/)

Cool! That's more than the basics of the `Component` framework, you should
now be able to do all of the important things with the system. It may be
worth going through it again and trying to rebuild the app from memory.
After you're happy, you may want to glance at
[Advanced Topics](../advanced_topics.md) to know what else you may need to
know in the future.

##### Back to [Component Framework Tutorial](00_intro.md)
