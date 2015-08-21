In the following example, we're adding `num_attendee`s to the Entry form and
in order to have it show the correct number after you submit a new attendee,
we're going to use `final` rather than `init` because `final` is executed
after the handler.

### In `attendance/views.py`:
```python
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
```

You should know the drill by now, we added new urls to `urls.py` and a new
attendance_page.html which uses the new component_key/name
(`step_5_attendance_entry` rather than `step_4_attendance_entry`).

We also added this to the top of a copy of the new "entry component"
template: `Add a new attendee (Currently {{ num_attendees }} attending)`

#### [View the result of example 5 locally](http://127.0.0.1:8000/5/)

**NOTE:** If you are an especially careful reader, you may have noticed that
the same `request` will both grab all attendees plus a count of all
attendees rather than just finding the length of the full list once it's in
python.

Typically, the easiest way to spot duplicate data is by using the `SQL`
panel from the `Django Debug Toolbar`:

![](https://i.imgur.com/rL46Mmk.png)

Continue to
[Example 6: Sharing objects](06_object_cache.md) to learn
how to efficiently reuse/pass information around within a request.

##### Back to [Component Framework Tutorial](00_intro.md)

