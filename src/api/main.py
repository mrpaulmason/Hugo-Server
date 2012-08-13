import tornado.ioloop
import tornado.web

import logging
import os, sys, getopt


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

settings = {
            "static_path": os.path.join(os.path.dirname(__file__), "static")
}

application = tornado.web.Application([
    (r"/", MainHandler),
    ], **settings)

if __name__ == "__main__":
    port = 8888

    try:
        opts, args = getopt.getopt(sys.argv[1:], "p:", ["port="])
    except getopt.GetoptError, err:
        print str(err)
        sys.exit(2)

    for o, a in opts:
        if o in ("-p", "--port"):
            port = int(a)
            print a
            if port <= 0 or port > 65535:
                raise ValueError
    logging.getLogger().setLevel(logging.INFO)
    application.listen(port)
    tornado.ioloop.IOLoop.instance().start()    
    