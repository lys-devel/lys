def avoidCircularReference(func, name="_avoidCircularFlg"):
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, name):
            setattr(self, name, False)
        if getattr(self, name) is True:
            return
        else:
            setattr(self, name, True)
            func(self, *args, **kwargs)
            setattr(self, name, False)
    return wrapper
