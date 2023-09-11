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
from marshmallow import Schema, fields

from helpers.communication_helpers import *
from helpers.config_helper import ConfigHelper
from helpers.io_helpers import RequiredFieldError

from walrus import *

from send_message_whatssap import SendMessageWorker


class InvalidConfigException(Exception):
    def __init__(self, param, value):
        super(InvalidConfigException, self).__init__("UNDEFINED PARAM %s: %s" % (param, value))


class InvalidInputException(Exception):
    def __init__(self, param, value):
        super(InvalidInputException, self).__init__("INVALID INPUT %s: %s" % (param, value))


class PermissionDeniedException(Exception):
    def __init__(self):
        super(PermissionDeniedException, self).__init__("PERMISSION DENIED")


class NotAuthenticatedException(InvalidInputException):
    def __init__(self):
        super(NotAuthenticatedException, self).__init__("API_KEY", "Not Authenticated")


class NotAuthorizedException(InvalidInputException):
    def __init__(self):
        super(NotAuthorizedException, self).__init__("token", "Not Authorized")


########################### background bus process
class NodeSchema(Schema):
    """
    Marshmallow schema for nodes object
    """
    name = fields.String(required=True)


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
def authorize(api_key, token, member_id):
    permitted_methods = None

    if api_key == token and member_id is None:  # CLIENT IS AN INTERNAL SERVICE
        return "SERVICE", "CLUB .*"

    member_type = None

    if member_id is None:
        raise RequiredFieldError("member_id")

    if token is None:
        raise RequiredFieldError("token")

    cfg_helper = ConfigHelper()

    redis_host = cfg_helper.get_config("DB_API")["redis_host"]
    redis_port = cfg_helper.get_config("DB_API")["redis_port"]
    redis_db_number = cfg_helper.get_config("DB_API")["redis_db_number"]

    cache_db = Database(redis_host, redis_port, redis_db_number)
    cache = cache_db.cache("authorization_cache")

    cache_record = cache.get(member_id)
    cache_token = None
    if cache_record is not None:
        cache_record = json.loads(cache_record)
        cache_token = cache_record["token"]
        member_type = cache_record["member_type"]
        permitted_methods = cache_record["permitted_methods"]

    if cache_token is None or token != cache_token:
        return None, None
    else:
        return member_type, permitted_methods


# noinspection PyShadowingNames
def execute_request(index, method_type, method, order_data, ip):
    cfg_helper = ConfigHelper()
    config_key = index.upper()

    if config_key not in cfg_helper.config.keys():
        raise InvalidInputException("TABLE", index)

    tracking_code = str(uuid.uuid4())
    size = 1000 if "size" not in order_data else order_data["size"]
    from_ = 0 if "from" not in order_data else order_data["from"]
    sort_by = [{"DC_CREATE_TIME": "desc"}] if "sort_by" not in order_data or len(
        order_data["sort_by"].keys()) == 0 else [order_data["sort_by"]]

    request = {"broker_type": cfg_helper.get_config("DEFAULT")["broker_type"],
               "method": method, "ip": ip, "size": size, "from": from_,
               "tracking_code": tracking_code,
               "sort_by": sort_by}

    source = "TEST"

    message = create_message(method=method, record=order_data["data"], tracking_code=request["tracking_code"],
                             broker_type=request["broker_type"],
                             source=source, size=size, from_=from_, error_code=0,
                             is_successful=None, error_description=None,
                             sort_by=sort_by
                             )

    try:
        Send_Message_Worker = SendMessageWorker()
        response = Send_Message_Worker.serve_request(message)


    except:
        raise InvalidConfigException(index + ".rabbit_type",
                                     cfg_helper.get_config(index)["rabbit_type"])

    response = clear_response(response)

    return response, tracking_code


# noinspection PyBroadException
class NodesController(object):

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def send_message_whatsapp(self):
        method_type = "send_message_whatsapp"
        try:
            # lock = db.lock('api_Lock', 1000)
            order_data = cherrypy.request.json
            ip = cherrypy.request.remote.ip
            index = order_data["table"]
            if "method_type" in order_data:
                method = order_data["method_type"]
                if method.upper() in ["UPDATE", "SELECT", "DELETE"]:
                    raise PermissionDeniedException()
            else:
                method = "insert"

            if "data" not in order_data.keys():
                raise RequiredFieldError("data")

            order_data["data"]["DC_CREATE_TIME"] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f")

            response, tracking_code = execute_request(index=index, method_type=method_type, method=method,
                                                      order_data=order_data, ip=ip)

            return {"status": 200, "tracking_code": tracking_code, "method_type": method_type,
                    "response": response}
        except NotAuthenticatedException as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except NotAuthorizedException as e:
            return {"status": 405, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except PermissionDeniedException as e:
            return {"status": 403, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except RequiredFieldError as e:
            return {"status": e.error_code, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except InvalidInputException as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except KeyError as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type,
                    "error": "key %s is not passed" % str(e)}
        except:
            import traceback
            traceback.print_exc()
            return {"status": 500, "tracking_code": None, "method_type": None, "error": "General Error"}


####################################### bad request response
def jsonify_error(status, message): \
        # pylint: disable=unused-argument

    """JSONify all CherryPy error responses (created by raising the
    cherrypy.HTTPError exception)
    """

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
