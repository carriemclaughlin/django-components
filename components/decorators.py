
from functools import wraps, partial

def obj_cache(key_name_or_var_func, force_shared=False, args=None, kwargs=None):
    """
    If key_name_or_var_func is a callable then obj_cache is being used
    as a decorator. If it's a string, then it's being called directly
    as a function with the key name specified.

    If forced_shared is false, and the object has a param_key, the
    name is concatenated with a hash of the current Component's args
    and kwargs parameters. This ensures that the objects are only
    shared between components with the same set of arguments, which is
    normally what we want.
    """
    def decorator(name, var_func):
        wraps(var_func)
        def func(self):
            has_param_key = hasattr(self, "param_key") and self.param_key
            if has_param_key and not force_shared:
                param_name = self.obj_cache.get_key_for_child_component(name, self.kwargs)
            else:
                param_name = name

            return self.obj_cache(param_name, lambda: var_func(self))
        return property(func)

    if hasattr(key_name_or_var_func, "__call__"):
        return decorator(key_name_or_var_func.__name__, key_name_or_var_func)
    else:
        return partial(decorator, key_name_or_var_func)

def shared_obj_cache(key_name_or_var_func, args=None, kwargs=None):
    """
    Same as obj_cache but doesn't use param key (same as calling obj_cache
    with force_shared)
    """
    def decorator(name, var_func):
        wraps(var_func)
        def func(self):
            return self.obj_cache(name, lambda: var_func(self))
        return property(func)

    if hasattr(key_name_or_var_func, "__call__"):
        return decorator(key_name_or_var_func.__name__, key_name_or_var_func)
    else:
        return partial(decorator, key_name_or_var_func)
