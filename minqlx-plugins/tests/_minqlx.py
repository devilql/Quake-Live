RET_NONE = 0
RET_STOP = 1
RET_STOP_EVENT = 2
RET_STOP_ALL = 3


cvars = {}
configstrings = {}
players = []
messages = []
force_vote_calls = []


class Logger:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(str(message))


logger = Logger()


def reset():
    cvars.clear()
    configstrings.clear()
    players[:] = []
    messages[:] = []
    force_vote_calls[:] = []
    logger.messages.clear()


def set_cvar_once(name, value):
    cvars.setdefault(name, value)


def get_cvar(name, value_type=str):
    value = cvars.get(name)
    if value_type is int:
        return int(value)
    if value_type is bool:
        return str(value).lower() in ("1", "true", "on", "yes")
    return value


def get_configstring(index):
    return configstrings.get(index, "")


def set_configstring(index, value):
    configstrings[index] = value


def force_vote(pass_it):
    force_vote_calls.append(pass_it)


def get_logger(name=None):
    return logger


class Plugin:
    @property
    def logger(self):
        return get_logger(self)

    def add_hook(self, event, handler):
        if not hasattr(self, "_hooks"):
            self._hooks = []
        self._hooks.append((event, handler))

    def add_command(self, command, handler):
        if not hasattr(self, "_commands"):
            self._commands = []
        self._commands.append((command, handler))

    def set_cvar_once(self, name, value):
        set_cvar_once(name, value)

    def get_cvar(self, name, value_type=str):
        return get_cvar(name, value_type)

    @classmethod
    def is_vote_active(cls):
        return bool(get_configstring(9))

    @classmethod
    def msg(cls, text, chat_channel="chat", **kwargs):
        messages.append(text)

    @classmethod
    def player(cls, name, player_list=None):
        current_players = players if player_list is None else player_list
        for player in current_players:
            if name == player:
                return player
            if isinstance(name, int) and (player.id == name or player.steam_id == name):
                return player
            if isinstance(name, str) and player.clean_name.lower() == name.lower():
                return player
        return None

    @classmethod
    def find_player(cls, name, player_list=None):
        current_players = players if player_list is None else player_list
        clean_name = name.lower()
        return [player for player in current_players if clean_name in player.clean_name.lower()]