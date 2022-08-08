from contextlib import contextmanager

from fabric2 import Connection


class CliConnection(Connection):
    def __init__(self, host, user, password):
        print(f"host : {host}")
        super(CliConnection, self).__init__(
            host=host, connect_kwargs={"user": user, "password": password}
        )
        command_user = list()
        self._set(command_user=command_user)

    @contextmanager
    def update_config(self, user):
        if self.is_connected:
            self.close()
        self.command_user.append(self.user)
        self.user = user
        try:
            yield
        finally:
            self.command_user.pop()
            self.close()
