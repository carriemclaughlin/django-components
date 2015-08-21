
from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView

urlpatterns = patterns(
    '',
    url(r'^$', TemplateView.as_view(template_name='index.html'), name="homepage"),
    url(r'^', include('example.attendance.urls')),
)
