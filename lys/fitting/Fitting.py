import inspect

import numpy as np
from scipy import optimize


def fit(f, xdata, ydata, guess=None, bounds=None):
    """
    Wrapper of scipy.curve_fit that implements several useful functionarities.

    If the lower and upper bounds are same, the the parameter is not used for the fitting.

    Args:
        funcs(callable): Function or list of functions that is used to fit data. The functions should have appropriate signature. See inspect.signature.
        xdata(any): xdata used to fitting.
        ydata(any): ydata used to fitting. Assume ydata = func(xdata, *args)
        guess: See scipy.curve_fit
        bounds: See scipy.curve_fit

    Return:
        sequence: the fitting result.
        sigma: the covalence matrix. If the parameter is not used for the fitting, None is returned.
    """
    if guess is None:
        guess = [1 for _ in range(_nparam(f))]
    if bounds is None:
        res, tmp = optimize.curve_fit(f, xdata, ydata, guess)
    else:
        fixed = []
        b_low, b_high = [], []
        for i in range(len(bounds[0])):
            if bounds[0][i] == bounds[1][i]:
                fixed.append(i)
            else:
                b_low.append(bounds[0][i])
                b_high.append(bounds[1][i])
        for i in fixed:
            f = _fixFunc(f, i, bounds[0][i])
        guess = [g for i, g in enumerate(guess) if i not in fixed]
        res, sig = optimize.curve_fit(f, xdata, ydata, guess, bounds=(b_low, b_high))
        for i in fixed:
            res = np.insert(res, i, bounds[0][i])
            sig = np.insert(sig, i, None)
    return res, sig


def _nparam(f):
    return len(inspect.signature(f).parameters) - 1


def _sumFunc(f1, f2):
    def func(x, *p):
        n = _nparam(f1)
        return f1(x, *p[:n]) + f2(x, *p[n:])
    func.__signature__ = inspect.Signature(list(inspect.signature(f1).parameters.values()) + list(inspect.signature(f2).parameters.values())[1:])
    return func


def _fixFunc(f, n, value):
    def func(x, *p):
        return f(x, *p[:n], value, *p[n:])
    p = list(inspect.signature(f).parameters.values())
    func.__signature__ = inspect.Signature(p[:n + 1] + p[n + 2:])
    return func


def sumFunction(f, *funcs):
    if hasattr(f, "__iter__"):
        return sumFunction(f[0], *f[1:])
    else:
        if len(funcs) > 0:
            fs = _sumFunc(f, funcs[0])
            return sumFunction(fs, *funcs[1:])
        else:
            return f
