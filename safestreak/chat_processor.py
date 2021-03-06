import re
import threading
import tkinter

ign_re = "[A-Za-z0-9_]+"
ign_list_re = "[A-Za-z0-9_, ]+"
qualified_ign_re = "(?:\[[A-Z\+]*\] )?([A-Za-z0-9_]+)"

def thread_map (function, iterable):
    threads = []
    for arg in iterable:
        thread = threading.Thread (target = function, args = [arg])
        thread.start ()
        threads.append (thread)
    for thread in threads:
        thread.join ()


class ChatProcessor:
    def __init__ (self, app):
        self.app = app
    def process (self, chat_message: str):
        who_response_message_parse_result = re.fullmatch (f"ONLINE: (?P<online_igns>{ign_list_re})", chat_message)
        if who_response_message_parse_result is not None:
            online_igns = who_response_message_parse_result.group ("online_igns").split (", ")
            # print (f"[!] {', '.join (online_igns)} (len {len (online_igns)}) are online")
            self.app.container.clear_rows ()
            with self.app.container_lock:
                thread_map (lambda online_ign: self.app.container.add_row (online_ign), online_igns)
            return

        join_message_parse_result = re.fullmatch (f"(?P<joined_ign>{ign_re}) has joined \([0-9]+\/[0-9]+\)!", chat_message)
        if join_message_parse_result is not None:
            joined_ign = join_message_parse_result.group ("joined_ign")
            # print (f"[!] {joined_ign} joined")
            with self.app.container_lock:
                self.app.container.add_row (joined_ign)
            return

        quit_message_parse_result = re.fullmatch (f"(?P<quit_ign>{ign_re}) has quit!", chat_message)
        if quit_message_parse_result is not None:
            quit_ign = quit_message_parse_result.group ("quit_ign")
            # print (f"[!] {quit_ign} quit")
            with self.app.container_lock:
                self.app.container.remove_row (quit_ign)
            return

        party_leader_parse_result = re.fullmatch (r"Party Leader: (?:\[[A-Z\+]*\] )?(?P<leader_ign>[A-Za-z0-9_]+) ● *", chat_message)
        if party_leader_parse_result is not None:
            leader_ign = party_leader_parse_result.group ("leader_ign")
            # print (f"[!] {leader_ign} is leader")
            with self.app.container_lock:
                self.app.container.add_row (leader_ign, pinned = True)
            return

        for party_member_type in ("Moderators", "Members"):
            party_members_parse_result = re.fullmatch (f"Party {party_member_type}: (?P<members_list>.+)", chat_message)
            if party_members_parse_result is not None:
                members = list (filter (lambda member: member != '', re.split (r"(?:\[[A-Z\+]*\] )?([A-Za-z0-9_]+) ● *", party_members_parse_result.group ("members_list"))))
                # print (f"[!] {', '.join (members)} are {party_member_type.lower ()}")
                with self.app.container_lock:
                    thread_map (lambda member: self.app.container.add_row (member, pinned = True), members)
        for warp_regex in (f"Party Leader, {qualified_ign_re}, summoned you to their server.", f"You summoned {qualified_ign_re} to your server."):
            warp_parse_result = re.fullmatch (warp_regex, chat_message)
            if warp_parse_result is not None:
                # print (f"[!] Party warp detected")
                with self.app.container_lock:
                    self.app.container.clear_rows ()