from helpers.config_helper import ConfigHelper

cfg_helper = ConfigHelper()
service_name = "send_message_whatsapp".upper()

from send_message_whatssap.workers import *
