import tornado.ioloop
import tornado.web
import tornado.websocket
import socket
import bcrypt
from secrets import token_urlsafe
import ServerHandler
import Aor
import Config

sql = ServerHandler.Sql()
cache = ServerHandler.Cache()
config = Config.Config()


class BaseHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        return self.get_secure_cookie("i")


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("templates/index.html",
                    company=config.Get("company_name"),
                    servers=sql.Get(), stats=cache.Fetch())


class ResourceHandler(tornado.web.RequestHandler):

    def get(self, resource):
        try:
            res = open('src/static/' + resource).read()
            self.set_header("Content-Type", 'text/css; charset="utf-8"')
            self.write(res)
        except:
            self.write("404 - not found")


class LoginManager(tornado.web.RequestHandler):

    def get(self):
        self.render("templates/login.html")

    def post(self):
        username = self.get_body_argument("username")
        password = self.get_body_argument("password").encode('utf8')
        admin_password = config.Get("admin_password").encode('utf8')
        if username == config.Get("admin_username") and bcrypt.checkpw(password, admin_password):
            self.set_secure_cookie("i", token_urlsafe(32))
            self.redirect("/admin")
        else:
            self.redirect("/login")


class AdminInterface(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        self.render("templates/admin.html", servers=sql.Get())

    @tornado.web.authenticated
    def post(self):
        ip = socket.gethostbyname(self.get_body_argument("hostname"))
        sql.New(self.get_body_argument("name"),
                self.get_body_argument("hostname"),
                ip)
        self.write("success")


class AdminInterfaceDelete(BaseHandler):

    @tornado.web.authenticated
    def post(self, id):
        sql.Delete(id)
        self.write("success")


def make_app():

    settings = {
        "cookie_secret": token_urlsafe(32),
        "login_url": "/login",
        "xsrf_cookies": True,
        "debug": True
    }

    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/static/(.*)", ResourceHandler),
        (r"/fetch", Aor.FetchWebsocket),
        (r"/login", LoginManager),
        (r"/admin", AdminInterface),
        (r"/admin/delete/([0-9]+)", AdminInterfaceDelete),
        (r"/aor", Aor.Aor)
    ], **settings)


def run_app():
    port = config.Get("webserver_port")
    app = make_app()
    app.listen(port)
    print("Platypus master listening on port :", port)

    tornado.ioloop.IOLoop.current().start()


run_app()
