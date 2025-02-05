
import copy
from typing import Any, Dict

from tornado.web import Application, RequestHandler
from tornado.ioloop import IOLoop

from neuro_san.http_sidecar.handler_factory import HandlerFactory
from neuro_san.http_sidecar.handlers.connectivity_handler import ConnectivityHandler
from neuro_san.http_sidecar.handlers.function_handler import FunctionHandler
from neuro_san.http_sidecar.handlers.streaming_chat_handler import StreamingChatHandler


class HttpSidecar:
    def __init__(self, port: int, agents: Dict[str, Any]):
        self.port = port
        self.http_port: int = self.port+1
        self.agents = copy.deepcopy(agents)

    def __call__(self):
        app = self.make_app()
        app.listen(self.http_port)
        print(f"HTTP server is running on port {self.http_port}...")
        print(f"Serving agents: {self.agents.keys()}...")
        IOLoop.current().start()

    def make_app(self):
        handlers = []
        for agent_name in self.agents.keys():
            route: str = f"/api/v1/{agent_name}/connectivity"
            print(f"Registering: {route}")
            handler_class = ConnectivityHandler().build(self.port, agent_name, "connectivity")
            handlers.append((route, handler_class,))
            route: str = f"/api/v1/{agent_name}/function"
            print(f"Registering: {route}")
            handler_class = FunctionHandler().build(self.port, agent_name, "function")
            handlers.append((route, handler_class,))
            route: str = f"/api/v1/{agent_name}/streaming_chat"
            print(f"Registering: {route}")
            handler_class = StreamingChatHandler().build(self.port, agent_name, "streaming_chat")
            handlers.append((route, handler_class,))

        return Application(handlers)
