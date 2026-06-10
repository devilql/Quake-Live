import importlib
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
PLUGIN_DIR = HERE.parent

if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import _minqlx as fake_minqlx

sys.modules["minqlx"] = fake_minqlx

if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

votemanager_module = importlib.import_module("votemanager")
votemanager = votemanager_module.votemanager


class FakeDB:
    def __init__(self):
        self.permissions = {}

    def get_permission(self, player):
        steam_id = getattr(player, "steam_id", player)
        return self.permissions.get(steam_id, 0)

    def has_permission(self, player, level=5):
        return self.get_permission(player) >= level


class FakePlayer:
    def __init__(self, steam_id, name, privileges=None, player_id=None):
        self.steam_id = steam_id
        self.name = name
        self.clean_name = name
        self.privileges = privileges
        self.id = steam_id if player_id is None else player_id
        self.tells = []

    def tell(self, message):
        self.tells.append(message)


class TestVoteManager(unittest.TestCase):
    def setUp(self):
        fake_minqlx.reset()
        fake_minqlx.set_configstring(9, "map campgrounds")
        self.plugin = votemanager()
        self.plugin.db = FakeDB()

    def test_vote_caller_cannot_vote_again_after_auto_yes(self):
        caller = FakePlayer(1, "Caller")

        self.plugin.handle_vote_started(caller, "map", "campgrounds")

        result = self.plugin.handle_vote(caller, False)

        self.assertEqual(fake_minqlx.RET_STOP_ALL, result)
        self.assertEqual(["^3You have already voted on this issue."], caller.tells)
        self.assertEqual([], fake_minqlx.force_vote_calls)

    def test_unprivileged_duplicate_vote_is_blocked(self):
        player = FakePlayer(2, "Player")

        self.plugin.handle_vote_started(None, "map", "campgrounds")
        first_result = self.plugin.handle_vote(player, True)
        second_result = self.plugin.handle_vote(player, False)

        self.assertIsNone(first_result)
        self.assertEqual(fake_minqlx.RET_STOP_ALL, second_result)
        self.assertEqual(["^3You have already voted on this issue."], player.tells)
        self.assertEqual([], fake_minqlx.force_vote_calls)

    def test_privileged_second_vote_forces_the_vote(self):
        player = FakePlayer(3, "Privileged")
        self.plugin.db.permissions[player.steam_id] = 3

        self.plugin.handle_vote_started(None, "map", "campgrounds")
        first_result = self.plugin.handle_vote(player, True)
        second_result = self.plugin.handle_vote(player, False)

        self.assertIsNone(first_result)
        self.assertEqual(fake_minqlx.RET_STOP_ALL, second_result)
        self.assertEqual([False], fake_minqlx.force_vote_calls)
        self.assertEqual(["Privileged^7 vetoed the vote."], fake_minqlx.messages)

    def test_vote_logging_records_force_path(self):
        player = FakePlayer(9, "LoggerPlayer")
        self.plugin.db.permissions[player.steam_id] = 3

        self.plugin.handle_vote_started(None, "map", "campgrounds")
        self.plugin.handle_vote(player, True)
        self.plugin.handle_vote(player, False)

        self.assertTrue(any("forced vote" in message.lower() for message in fake_minqlx.logger.messages))

    def test_privileged_second_vote_preserves_yes_direction(self):
        player = FakePlayer(8, "YesVote")
        self.plugin.db.permissions[player.steam_id] = 3

        self.plugin.handle_vote_started(None, "map", "campgrounds")
        self.plugin.handle_vote(player, True)
        result = self.plugin.handle_vote(player, True)

        self.assertEqual(fake_minqlx.RET_STOP_ALL, result)
        self.assertEqual([True], fake_minqlx.force_vote_calls)

    def test_qlds_admin_vote_fakes_counter_for_impression(self):
        admin = FakePlayer(4, "Admin", privileges="admin")
        fake_minqlx.set_configstring(10, "1")
        fake_minqlx.set_configstring(11, "2")

        result = self.plugin.handle_vote(admin, True)

        self.assertEqual(fake_minqlx.RET_STOP_ALL, result)
        self.assertEqual([], fake_minqlx.force_vote_calls)
        self.assertEqual("2", fake_minqlx.get_configstring(10))
        self.assertEqual("2", fake_minqlx.get_configstring(11))

    def test_protected_kick_vote_is_stopped(self):
        caller = FakePlayer(5, "Caller")
        target = FakePlayer(6, "Target")
        fake_minqlx.players[:] = [caller, target]
        self.plugin.db.permissions[target.steam_id] = 2

        result = self.plugin.handle_vote_called(caller, "kick", "Target")

        self.assertEqual(fake_minqlx.RET_STOP_ALL, result)
        self.assertEqual(["Target^7 has permission level ^42^7 and will not be kicked."], caller.tells)

    def test_unknown_kick_target_does_not_stop_the_vote(self):
        caller = FakePlayer(7, "Caller")

        result = self.plugin.handle_vote_called(caller, "kick", "Missing")

        self.assertIsNone(result)
        self.assertEqual([], caller.tells)


if __name__ == "__main__":
    unittest.main()