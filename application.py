from gevent import monkey
from gevent.pywsgi import WSGIServer
import werkzeug.serving
monkey.patch_all()
from siyu import application

@werkzeug.serving.run_with_reloader
def server_start():
    #application.debug = True
    #application.run(host='0.0.0.0',debug=True)
    from werkzeug.debug import DebuggedApplication
    dapp = DebuggedApplication(application, evalex= True)
    http_server = WSGIServer(('0.0.0.0', int(5000)), dapp)
    http_server.serve_forever()

if __name__ == '__main__':
    server_start()

