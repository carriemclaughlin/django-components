
from django import forms

class BFormMixin(object):
    def init_bform_kwargs(self, **kwargs):
        try:
            page_key = kwargs.pop('page_key')
            param_key = kwargs.pop('param_key', '')
        except KeyError:
            raise ValueError("BForms require page_key to be passed in.")

        kwargs['initial'] = dict(
            kwargs.get('initial', {}),
            page_key=page_key, param_key=param_key)

        return kwargs

class BForm(BFormMixin, forms.Form):
    page_key = forms.CharField(widget=forms.HiddenInput)
    param_key = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        kwargs = self.init_bform_kwargs(**kwargs)
        super(BForm, self).__init__(*args, **kwargs)

class BModelForm(BFormMixin, forms.ModelForm):
    page_key = forms.CharField(widget=forms.HiddenInput)
    param_key = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        kwargs = self.init_bform_kwargs(**kwargs)
        super(BModelForm, self).__init__(*args, **kwargs)
