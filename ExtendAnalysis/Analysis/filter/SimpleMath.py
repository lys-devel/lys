from .FilterInterface import FilterInterface


class SimpleMathFilter(FilterInterface):
    def __init__(self, type, value):
        self._type = type
        self._value = value

    def _execute(self, wave, **kwargs):
        if self._type == "+":
            wave.data = wave.data + self._value
        if self._type == "-":
            wave.data = wave.data - self._value
        if self._type == "*":
            wave.data = wave.data * self._value
        if self._type == "/":
            wave.data = wave.data / self._value
        if self._type == "**":
            wave.data = wave.data ** self._value
        return wave
