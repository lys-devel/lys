from lys import Wave, registerFileLoader

try:
    from PIL import Image

    def __loadImage(name):
        im = Image.open(name)
        return Wave(im)

    registerFileLoader(".tif", __loadImage)
    registerFileLoader(".png", __loadImage)
    registerFileLoader(".jpg", __loadImage)
except Exception:
    pass
