import os


class SettingDict(dict):
    """Wrapped dict, internally used to automatically save settings

    SettingDict is wrapper of dict that is is automatically saved when __setitem__ and __delitem__ are called.

    If file is not specified, SettingDict behave as normal dict class.

    If file does not exist, the file is automatically created.

    Args:
        file (string): The filename to be loaded and saved

    Examples:
        >>> d = SettingDict() 
        >>> d["setting1"] = "SettingString"
        >>> d.Save("Setting.dic")

        >>> d2 = SettingDict("Setting.dic")   # setting.dic is loaded
        >>> d2["setting1"]
        SettingString

    """

    def __init__(self, file=None):
        self.__file = file
        if file is None:
            return
        if os.path.exists(file):
            with open(file, 'r') as f:
                data = eval(f.read())
            for key, item in data.items():
                self[key] = item

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.Save()

    def __delitem__(self, key):
        del self.data[key]
        self.Save()

    def Save(self, file=None):
        """Save dictionary

        Args:
            file (string): The filename to be saved
        """
        if file is None:
            file = self.__file
        if file is None:
            return
        file = os.path.abspath(file)
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, 'w') as f:
            f.write(str(self))
