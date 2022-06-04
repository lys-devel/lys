import warnings


class NotImplementedWarning(Warning):
    pass


class NotSupportedWarning(Warning):
    pass


warnings.simplefilter("once", NotSupportedWarning)
