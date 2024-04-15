import logging


class EvoLogger(logging.Logger):
    def __init__(self, name="evo-django-kits", level=logging.DEBUG):
        super().__init__(name, level)
        self.setLevel(level)
        self.addHandler(logging.StreamHandler())
        self.addHandler(logging.FileHandler("evo.log"))
        self.propagate = False

    def log(self, level, msg, *args, **kwargs):
        super().log(level, msg, *args, **kwargs)
