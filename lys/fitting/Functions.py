
import numpy as np
from scipy import special
from collections import OrderedDict


def const(x, C):
    """
    Function for fitting.

    :math:`y = C`
    """
    return np.ones([x.shape[0]]) * C


def linear(x, a=1, b=0):
    """
    Function for fitting.

    :math:`y = ax + b`
    """
    return a * x + b


def quadratic(x, a, b, c):
    """
    Function for fitting.

    :math:`y = ax^2 + bx + c`
    """
    return a * x**2 + b * x + c


def step(x, position, height):
    """
    Heaviside step function for fitting.

    :math:`y = h \\theta(x-x_0)`

    Args:
        position: :math:`x_0`.
        height: :math:`h`.
    """

    return np.heaviside(x - position, 0.5) * height


def error(x, position, height, fwhm):
    """
    Error function for fitting.

    For convenience, this function is defined as

    :math:`h(\mathrm{erf}[(x-x_0)/\\tau] + 1)/2`

    erf is error function (scipy.special.erf).

    FWHM is of gaussian function integrated.

    Args:
        position: :math:`x_0`.
        height: :math:`h`.
        fwhm: ::math:`2\sqrt{\log 2}\\tau`.

    """
    return height / 2 * (special.erf(2 * np.sqrt(np.log(2)) * (x - position) / fwhm) + 1)


def stepExp(x, position, height, a):
    """
    Exponential decay multiplied by step function.

    :math:`y = h\\theta(x-x_0)\exp[-a(x-x_0)]` 

    Args:
        position: :math:`x_0`.
        height: :math:`h`.
        a: :math:`a`.
    """
    return np.heaviside(x - position, 0.5) * height * np.exp(-a * (x - position))


def lorentz(x, position, height, fwhm):
    """
    Lorentz function.

    :math:`y = hd^2/[(x-x_0)^2+d^2]`

    Args:
        position: :math:`x_0`.
        height: :math:`h`.
        fwhm: :math:`2d`.
    """
    return height * (fwhm / 2)**2 / ((x - position)**2 + (fwhm / 2)**2)


def cos(x, position, height, frequency, phase):
    """
    Cosine function

    :math:`y = h \cos(f(x-x_0)+\phi)`

    Args:
        position: :math:`x_0`.
        height: :math:`h`.
        frequency: :math:`f`.
        phase: :math:`\phi`.

    """
    return np.cos(frequency * (x - position) + phase) * height


def exp(x, position, height, a):
    """
    Simple exponential function

    :math:`y=h\exp(a(x-x_0))`

    Args:
        position: :math:`x_0`.
        height: :math:`h`.
        a: :math:`a`.
    """
    return np.exp(a * (x - position)) * height


def gauss(x, position, height, sigma):
    """
    Simple gaussian

    :math:`y=h\exp[-(x-x_0)^2/2\sigma^2]`

    Args:
        position: :math:`x_0`.
        height: :math:`h`.
        sigma: :math:`\sigma`.
    """
    return np.exp(-(x - position)**2 / (2 * sigma**2)) * height


def doubleExp(x, position, height, a, b):
    """
    Double exponential function with step.

    :math:`y = h\\theta (x-x_0)(1-\exp[-(x-x_0)/a]^2)\exp[-(x-x_0)/b]`

    Args:
        position: :math:`x_0`.
        height: :math:`h`.
        a: :math:`a`.
        b: :math:`b`.
    """
    return height * np.heaviside(x - position, 0.5) * (1 - np.exp(-((x - position) / a)**2)) * np.exp(-(x - position) / b)


def relaxOsci(x, position, height, frequency, phase, offset, tau):
    """
    Relaxed ocillation.

    :math:`y=h(C + cos[f(x-x_0)+\phi])\exp[-(x-x_0)/\\tau]\\theta(x-x_0)`

    Args:
        position: :math:`x_0`.
        height: :math:`h`.
        frequency: :math:`f`.
        phase: :math:`\phi`.
        offset: :math:`C`.
        tau: :math:`\\tau`.    
    """
    return height * np.heaviside(x - position, 0.5) * np.exp(-(x - position) / tau) * (offset + np.cos(frequency * (x - position) + phase * np.pi / 180))


functions = OrderedDict()
functions["Const"] = const
functions["Linear"] = linear
functions["Quadratic"] = quadratic
functions["Step"] = step
functions["Cos"] = cos
functions["Exp"] = exp
functions["Gauss"] = gauss
functions["Lorentzian"] = lorentz
functions["StepExponential"] = stepExp
functions["DoubleExp"] = doubleExp
functions["relaxOsci"] = relaxOsci
functions["Error"] = error


def _addFittingFunction(func, name):
    if name is None:
        name = func.__name__
    functions[name] = func
