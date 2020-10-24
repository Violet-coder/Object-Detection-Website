from PIL import Image

def Thumbnail(photo_adress, thumbnail_adress):
    image = Image.open(photo_adress)
    size = 200,200
    image.thumbnail(size)
    image.save(thumbnail_adress)


