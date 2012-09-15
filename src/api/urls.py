from handlers.news import *
from handlers.places import *
from handlers.auth import *

url_patterns = [
    (r"/places", PlacesHandler),
    (r"/places/categories", CategoriesHandler),
    (r"/auth", AuthHandler),
    (r"/news", NewsHandler),
]