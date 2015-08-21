
from django.conf.urls import patterns

from components.urls import component_url

from . import views

urlpatterns = patterns(
    '',

    component_url(r'^1/$',
                  ComponentClass=views.AttendanceEntryStep1Component,
                  name="step_1_attendance_entry",
                  PageClass=views.AttendanceStep1Page),

    component_url(r'^2/attendance_listing/$',
                  ComponentClass=views.AttendanceListingStep2Component,
                  name="step_2_listing"),
    component_url(r'^2/$',
                  ComponentClass=views.AttendanceEntryStep2Component,
                  name="step_2_attendance_entry",
                  PageClass=views.AttendanceStep2Page),

    component_url(r'^3/$',
                  ComponentClass=views.AttendanceEntryStep3Component,
                  name="step_3_attendance_entry",
                  PageClass=views.AttendanceStep3Page),

    component_url(r'^4/attendance_listing/$',
                  ComponentClass=views.AttendanceListingStep4Component,
                  name="step_4_listing"),
    component_url(r'^4/$',
                  ComponentClass=views.AttendanceEntryStep4Component,
                  name="step_4_attendance_entry",
                  PageClass=views.AttendanceStep4Page),

    component_url(r'^5/$',
                  ComponentClass=views.AttendanceEntryStep5Component,
                  name="step_5_attendance_entry",
                  PageClass=views.AttendanceStep5Page),

    component_url(r'^6/attendance_listing/$',
                  ComponentClass=views.AttendanceListingStep6Component,
                  name="step_6_listing"),
    component_url(r'^6/$',
                  ComponentClass=views.AttendanceEntryStep6Component,
                  name="step_6_attendance_entry",
                  PageClass=views.AttendanceStep6Page),

    component_url(r'^7/delete_attendee/(?P<attendee_id>\d+)/$',
                  ComponentClass=views.DeleteAttendeeStep7Component,
                  name="step_7_deleting"),
    component_url(r'^7/attendance_listing/$',
                  ComponentClass=views.AttendanceListingStep7Component,
                  name="step_7_listing"),
    component_url(r'^7/$',
                  ComponentClass=views.AttendanceEntryStep7Component,
                  name="step_7_attendance_entry",
                  PageClass=views.AttendanceStep7Page),

    component_url(r'^8/delete_attendee/(?P<attendee_id>\d+)/$',
                  ComponentClass=views.DeleteAttendeeStep8Component,
                  name="step_8_deleting"),
    component_url(r'^8/attendance_listing/$',
                  ComponentClass=views.AttendanceListingStep8Component,
                  name="step_8_listing"),
    component_url(r'^8/$',
                  ComponentClass=views.AttendanceEntryStep8Component,
                  name="step_8_attendance_entry",
                  PageClass=views.AttendanceStep8Page),

    component_url(r'^9/$',
                  ComponentClass=views.AttendanceEntryStep9Component,
                  name="step_9_attendance_entry",
                  PageClass=views.AttendanceStep9Page),

    component_url(r'^10/$',
                  ComponentClass=views.AttendanceEntryStep10Component,
                  name="step_10_attendance_entry",
                  PageClass=views.AttendanceStep10Page),
)
