from channels.routing import route_class
from .consumers import GenericWatcher

channel_routing = [
    route_class(GenericWatcher, path=GenericWatcher.url_pattern),

]
