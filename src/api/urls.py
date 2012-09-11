from handlers.places import *
from handlers.auth import AuthHandler

url_patterns = [
    (r"/places", PlacesHandler),
    (r"/places/categories", CategoriesHandler),
    (r"/auth", AuthHandler),
]