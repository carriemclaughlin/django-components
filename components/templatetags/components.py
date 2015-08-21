
from hashlib import md5

from django.template import base as tmp
from django.utils.safestring import mark_safe

register = tmp.Library()

class ComponentNode(tmp.Node):
    def __init__(self, component_key, kwargs):
        self.component_key = component_key
        self.ignore_missing = kwargs.pop('ignore_missing', False)
        self.kwargs = kwargs

    def render(self, context):
        from django.core.urlresolvers import reverse, NoReverseMatch


        if 'url_kwargs_dict' in self.kwargs and len(self.kwargs) == 1:
            kwargs = self.kwargs['url_kwargs_dict'].resolve(context)
        else:
            if self.kwargs:
                kwargs = {key: unicode(value.resolve(context))
                          for key, value
                          in self.kwargs.iteritems()}
            else:
                kwargs = {}

        component_key = self.component_key.resolve(context)

        if not component_key:
            raise KeyError(u"Missing component key for load_component")

        try:
            url = reverse(component_key,
                          kwargs=kwargs,
                          current_app=context.current_app)
        except NoReverseMatch:
            raise KeyError(
                u"No component found for key {key} and kwargs {kwargs}".format(
                    key=component_key, kwargs=kwargs))

        param_key = md5(url).hexdigest()

        components = context.get('components')
        component = components.get(param_key)
        components.accessed_keys.append(param_key)

        if component is None:
            if not self.ignore_missing:
                raise KeyError(
                    u"No component in context for key {key} and kwargs {kwargs}".format(
                        key=component_key, kwargs=kwargs))
            return mark_safe('')

        return mark_safe(u''.join([
            '<div class="cmp cmp_{param_key}_id">'.format(
                param_key=param_key),
            component,
            '</div>'
        ]))


@register.tag
def load_component(parser, token):
    parts = token.split_contents()
    if len(parts) <= 1:
        raise tmp.TemplateSyntaxError("'%s' needs a component key" % parts[0])

    # compile_filter is an undocumented django function that extracts
    # items from the "filter style" django syntax
    component_key = parser.compile_filter(parts[1])

    kwargs = {}

    parts = parts[2:]
    if len(parts):
        for part in parts:
            match = tmp.kwarg_re.match(part)
            if not match:
                raise tmp.TemplateSyntaxError("Malformed arguments to url tag")
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
            else:
                raise BaseException("load_component can't accept args, only kwargs")

    return ComponentNode(component_key, kwargs)
