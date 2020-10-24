class User:
    def __init__(self, name=None, email=None, password=None, salt=None, photo_id = None):
        self.name = name
        self.email = email
        self.password = password
        self.salt = salt
        self.photo_id = photo_id

    def toList(self):
        return [self.name, self.email, self.password, self.photo_id]

    def fromList(self, user_info):
        self.name = user_info[0]
        self.email = user_info[1]
        self.password = user_info[2]
        self.salt = user_info[3]
        self.photo_id = user_info[4]

    def getAttrs(self):
        return ('name, email, password','photo_id')

class User_photo:
    def __init__(self, name=None, org_photo=None, thumbnail=None, det_photo=None):
        self.name = name
        self.org_photo = org_photo
        self.thumbnail = thumbnail
        self.det_photo = det_photo