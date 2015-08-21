
from django.conf.urls import url, patterns

from .views import ComponentView, Component, COMPONENT_KEYS, PAGE_KEYS

def component_url(regex,
                  ComponentClass,
                  name,
                  kwargs=None,
                  prefix='',
                  view_class_kwargs={},
                  PageClass=None):
    """
        For use within URLConf:

        urlpatterns = patterns('',
            component_url(r'^profile/', ProfileComponent, 'profile', PageClass = ProfilePage),
            component_url(r'^profile/widget/', 'profile_widget', ProfileWidgetComponent),
        )

    """

    if not isinstance(name, (str, unicode)):
        raise TypeError("name should be a string")
    if not issubclass(ComponentClass, Component):
        raise TypeError("ComponentClass should be a subclass of Component")

    if '(' in regex and '?P<' not in regex:
        raise TypeError('component_url does not allow positional arguments, only kwargs')

    view = ComponentView.as_view(ComponentClass=ComponentClass, component_key=name, **view_class_kwargs)
    if (ComponentClass in COMPONENT_KEYS['from_component_class']
            and COMPONENT_KEYS['from_component_class'][ComponentClass] != name):
        raise BaseException("The Component %s is being added to as both '%s' and '%s' urls"
                            % (ComponentClass.__name__,
                               COMPONENT_KEYS['from_component_class'][ComponentClass],
                               name))

    COMPONENT_KEYS['to_component_class'][name] = ComponentClass
    COMPONENT_KEYS['from_component_class'][ComponentClass] = name

    if PageClass:
        if (PageClass in PAGE_KEYS['from_page_class']
                and PAGE_KEYS['from_page_class'][PageClass] != name):
            raise BaseException("The Page %s is being added to both '%s' and '%s' urls"
                                % (PageClass.__name__,
                                   PAGE_KEYS['from_page_class'][PageClass],
                                   name))
        PAGE_KEYS['to_page_class'][name] = PageClass
        PAGE_KEYS['from_page_class'][PageClass] = name

    return url(regex, view, kwargs=kwargs, name=name, prefix=prefix)


urlpatterns = patterns('',)
