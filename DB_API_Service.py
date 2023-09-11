# !/usr/bin/env python

# pylint: disable=invalid-name

"""
CherryPy-based webservice daemon with background threads
CherryPy-based webservice daemon with background threads
"""

from __future__ import print_function

import threading

import cherrypy
from cherrypy.process import plugins
import cherrypy_cors
from helpers.communication_helpers import *
from helpers.config_helper import ConfigHelper
from helpers.io_helpers import RequiredFieldError

from walrus import *

from send_message_whatssap import SendMessageWorker


def worker():
    """Background Timer that runs the hello() function every 5 seconds
    TODO: this needs to be fixed/optimized. I don't like creating the thread
    repeatedly.
    """

    # while True:
    #     t = threading.Timer(5.0, hello)
    #     t.start()
    #     t.join()


class MyBackgroundThread(plugins.SimplePlugin):
    """CherryPy plugin to create a background worker thread"""

    def __init__(self, bus):
        super(MyBackgroundThread, self).__init__(bus)

        self.t = None

    def start(self):
        """Plugin entrypoint"""

        self.t = threading.Thread(target=worker)
        self.t.daemon = True
        self.t.start()

    # Start at a higher priority that "Daemonize" (which we're not using
    # yet but may in the future)
    start.priority = 85


# noinspection PyShadowingNames
def execute_request(order_data, ip):
    cfg_helper = ConfigHelper()

    tracking_code = str(uuid.uuid4())
    size = 1000 if "size" not in order_data else order_data["size"]
    from_ = 0 if "from" not in order_data else order_data["from"]
    sort_by = [{"DC_CREATE_TIME": "desc"}] if "sort_by" not in order_data or len(
        order_data["sort_by"].keys()) == 0 else [order_data["sort_by"]]

    request = {"broker_type": cfg_helper.get_config("DEFAULT")["broker_type"], "ip": ip, "size": size, "from": from_,
               "tracking_code": tracking_code,
               "sort_by": sort_by}

    source = "TEST"

    message = create_message(method="send_message", record=order_data["data"], tracking_code=request["tracking_code"],
                             broker_type=request["broker_type"],
                             source=source, size=size, from_=from_, error_code=0,
                             is_successful=None, error_description=None,
                             sort_by=sort_by
                             )

    try:
        Send_Message_Worker = SendMessageWorker()
        response = Send_Message_Worker.serve_request(message)

    except:
        raise Exception

    response = clear_response(response)

    return response, tracking_code


# noinspection PyBroadException
class NodesController(object):

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def send_message_whatsapp(self):
        method_type = "send_message_whatsapp"
        try:
            order_data = cherrypy.request.json
            ip = cherrypy.request.remote.ip
            if "data" not in order_data.keys():
                raise RequiredFieldError("data")

            order_data["data"]["DC_CREATE_TIME"] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f")

            response, tracking_code = execute_request(order_data=order_data, ip=ip)

            return {"status": 200, "tracking_code": tracking_code, "method_type": method_type,
                    "response": response}

        except:
            import traceback
            traceback.print_exc()
            return {"status": 500, "tracking_code": None, "method_type": None, "error": "General Error"}


def jsonify_error(status, message):

    cherrypy.response.headers['Content-Type'] = 'application/json'
    response_body = message

    cherrypy.response.status = status

    return response_body


def cors():
    if cherrypy.request.method == 'OPTIONS':
        # preflign request
        # see http://www.w3.org/TR/cors/#cross-origin-request-with-preflight-0
        cherrypy.response.headers['Access-Control-Allow-Methods'] = 'POST'
        cherrypy.response.headers['Access-Control-Allow-Headers'] = 'content-type'
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        # tell CherryPy no avoid normal handler
        return True
    else:
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'


if __name__ == '__main__':
    ports = list(sys.argv)

    cherrypy_cors.install()

    MyBackgroundThread(cherrypy.engine).subscribe()

    dispatcher = cherrypy.dispatch.RoutesDispatcher()
    dispatcher.connect(name='auth',
                       route='/send_message_whatsapp',
                       action='send_message_whatsapp',
                       controller=NodesController(),
                       conditions={'method': ['POST']})

    config = {

        '/': {
            'request.dispatch': dispatcher,
            'error_page.default': jsonify_error,
            'cors.expose.on': True,
            # 'tools.auth_basic.on': True,
            # 'tools.auth_basic.realm': 'localhost',
            # 'tools.auth_basic.checkpassword': validate_password,
        },
    }

    cherrypy.tree.mount(root=None, config=config)

    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': int(ports[1]),
        'server.socket_queue_size': 3000,
        'server.thread_pool': 30,
        'log.screen': False,
        'log.access_file': '',
        'engine.autoreload.on': False,
    })
    cherrypy.log.error_log.propagate = False
    cherrypy.log.access_log.propagate = False
    cherrypy.engine.start()
    cherrypy.engine.block()
