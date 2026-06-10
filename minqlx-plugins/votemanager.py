# Created by Thomas Jones on 19/01/2016 - thomas@tomtecsolutions.com
# votemanager.py - a minqlx plugin to permit privileged players to vote normally initially, then vote a second time to force the vote either way.
# This plugin is released to everyone, for any purpose. It comes with no warranty, no guarantee it works, it's released AS IS.
# You can modify everything, except for lines 1-4 and the !tomtec_versions code. They're there to indicate I whacked this together originally. Please make it better :D

"""
This plugin works best when the player isn't a QLDS mod/admin, otherwise it can only be
used to give the impression that a QLDS mod/admin voted.
You can also protect players with permission level >= LEVEL from getting kickvoted
by setting: qlx_protectedPerm "LEVEL"
"""

import minqlx

class votemanager(minqlx.Plugin):
    def __init__(self):
        self.add_hook("vote_called", self.handle_vote_called)
        self.add_hook("vote_started", self.handle_vote_started)
        self.add_hook("vote", self.handle_vote)
        self.add_hook("vote_ended", self.handle_vote_ended)

        self.add_command("tomtec_versions", self.cmd_showversion)
        
        self.set_cvar_once("qlx_protectedPerm", "1")
        
        self.has_voted = set()

        self.plugin_version = "1.6"

    def handle_vote_started(self, player, vote, args):
        self.has_voted = set()
        caller_name = player.name if player is not None else "server"
        self.logger.info("vote_started: caller=%s vote=%s args=%r" % (caller_name, vote, args))
        if player is not None:
            self.has_voted.add(player.steam_id)

    def can_force_vote(self, player):
        return player.privileges is not None or self.db.has_permission(player.steam_id, 3)

    def resolve_kick_target(self, vote, args):
        if vote.lower() == "clientkick":
            try:
                return self.player(int(args))
            except ValueError:
                return None

        target = self.player(args)
        if target is not None:
            return target

        matches = self.find_player(args.lower())
        if len(matches) == 1:
            return matches[0]

        return None
        
    def handle_vote_called(self, caller, vote, args):
        self.logger.info("vote_called: caller=%s vote=%s args=%r" % (caller.name if caller else "server", vote, args))
        if vote.lower() in ["clientkick", "kick"]:
            guy = self.resolve_kick_target(vote, args)
            if guy is None:
                return
                
            perm = self.db.get_permission(guy)
            if perm >= self.get_cvar("qlx_protectedPerm", int):
                caller.tell("{}^7 has permission level ^4{}^7 and will not be kicked.".format(guy.name, perm))
                return minqlx.RET_STOP_ALL
                
    def handle_vote(self, player, yes):
        if not self.is_vote_active():
            return

        steam_id = player.steam_id
        can_force = self.can_force_vote(player)
        privilege_label = "privileged" if can_force else "normal"
        self.logger.info("vote: player=%s yes=%s privilege=%s (repeat=%s)" % (player.name, yes, privilege_label, steam_id in self.has_voted))
        
        if steam_id in self.has_voted:
            if can_force:
                minqlx.force_vote(yes)
                if yes:
                    word = "passed"
                else:
                    word = "vetoed"
                self.logger.info("vote: %s forced vote %s (%s)" % (player.name, "yes" if yes else "no", word))
                self.msg("{}^7 {} the vote.".format(player.name, word))
                return minqlx.RET_STOP_ALL
            
            self.logger.info("vote: %s attempted a duplicate vote; blocked as normal" % player.name)
            player.tell("^3You have already voted on this issue.")
            return minqlx.RET_STOP_ALL

        self.has_voted.add(steam_id)
        if can_force:
            self.logger.info("vote: %s cast the initial vote normally; repeat vote will be forced" % player.name)
        else:
            self.logger.info("vote: %s cast the initial vote normally" % player.name)

        if (player.privileges != None):
            self.logger.info("vote: %s is a QLDS mod/admin; just fake vote countersto give the impression of a normal vote" % player.name)
            # at least give the impression that the QLDS admin/mod voted normally.
            if yes:
                yes_votes = int(minqlx.get_configstring(10))
                yes_votes += 1
                minqlx.set_configstring(10, str(yes_votes))
            else:
                no_votes = int(minqlx.get_configstring(11))
                no_votes += 1
                minqlx.set_configstring(11, str(no_votes))
            return minqlx.RET_STOP_ALL
                
        #self.msg("self.has_voted == {}".format(str(self.has_voted))) # was used to make sure we stored player objects properly.

    def handle_vote_ended(self, votes, vote, args, passed):
        self.logger.info("vote_ended: votes=%r vote=%s args=%r passed=%s" % (votes, vote, args, passed))
        self.has_voted = set()

    def cmd_showversion(self, player, msg, channel):
        channel.reply("^4votemanager.py^7 - version {}, created by Thomas Jones on 19/01/2016.".format(self.plugin_version))
