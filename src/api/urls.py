from handlers.places import PlacesHandler

url_patterns = [
    (r"/places", PlacesHandler),
    (r"/auth", AuthHandler),
]