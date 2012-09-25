from handlers.news import *
from handlers.places import *
from handlers.auth import *
from handlers.comments import *

url_patterns = [
    (r"/places", PlacesHandler),
    (r"/places/categories", CategoriesHandler),
    (r"/auth", AuthHandler),
    (r"/comments", CommentsHandler),
    (r"/news", NewsHandler),
]