
import numpy as np
from scipy import special
from collections import OrderedDict


def const(x, value):
    return np.ones([x.shape[0]]) * value


def linear(x, a, b):
    return a * x + b


def quadratic(x, a, b, c):
    return a * x**2 + b * x + c


def step(x, position, height):
    return np.heaviside(x - position, 0.5) * height


def error(x, position, height, fwhm):
    return height / 2 * (special.erf(2 * np.sqrt(np.log(2)) * (x - position) / fwhm) + 1)


def stepExp(x, position, height, a):
    return np.heaviside(x - position, 0.5) * height * (1 - np.exp(-a * (x - position)))


def lorentz(x, position, height, fwhm):
    return height * (fwhm / 2)**2 / ((x - position)**2 + (fwhm / 2)**2)


def cos(x, position, height, frequency, phase):
    return np.cos(frequency * (x - position) + phase) * height


def exp(x, position, height, a):
    return np.exp(a * (x - position)) * height


def gauss(x, position, height, sigma):
    return np.exp(-(x - position)**2 / (2 * sigma**2)) * height


def doubleExp(x, position, height, a, b):
    return height * np.heaviside(x - position, 0.5) * (1 - np.exp(-((x - position) / a)**2)) * np.exp(-(x - position) / b)


def relaxOsci(x, position, height, frequency, phase, offset, relax):
    return height * np.heaviside(x - position, 0.5) * np.exp(-(x - position) / relax) * (offset + np.cos(frequency * (x - position) + phase * np.pi / 180))


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


def addFittingFunction(func, name):
    if name is None:
        name = func.__name__
    functions[name] = func
