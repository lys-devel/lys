import functools

def saveCanvas(func):
    @functools.wraps(func)
    def wrapper(*args,**kwargs):
        if args[0].saveflg:
            res=func(*args,**kwargs)
        else:
            args[0].saveflg=True
            res=func(*args,**kwargs)
            args[0].Save()
            args[0].draw()
            args[0].saveflg=False
        return res
    return wrapper

def notSaveCanvas(func):
    @functools.wraps(func)
    def wrapper(*args,**kwargs):
        saved=args[0].saveflg
        args[0].saveflg=True
        res=func(*args,**kwargs)
        args[0].saveflg=saved
        return res
    return wrapper
