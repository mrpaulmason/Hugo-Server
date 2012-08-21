from handlers.places import PlacesHandler
from handlers.auth import AuthHandler

url_patterns = [
    (r"/places", PlacesHandler),
    (r"/auth", AuthHandler),
]