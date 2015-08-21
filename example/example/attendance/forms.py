
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

