import socket
import threading
import zlib
import json
import os
import random
import time

class WagerManager:
    searches = []  # list of dicts: {"player_id":..., "enemy_id":...}
    wagers = []    # list of dicts: {"player1_id":..., "player2_id":..., "starters":[None,None]}

    def __init__(self, send_func):
        """
        send_func: a function that takes (player_id, dict_message)
        and sends that message to the given player.
        """
        self.send = send_func

    def search(self, player_id, enemy_id):
        """
        The player with `player_id` tries to find a match against `enemy_id`.
        If `enemy_id` is searching for `player_id`, start a wager.
        Otherwise, add a new search.
        """
        print(f"START SEARCH [{player_id}, {enemy_id}]")
        try:
            for search in self.searches:
                if search["enemy_id"] == player_id:
                    # found a match
                    self.start_wager(player1_id=search["player_id"], player2_id=player_id)
                    self.searches.remove(search)     # delete search after match was found
                    return True
            # not found -> add a search entry
            self.searches.append({
                "player_id": player_id,
                "enemy_id": enemy_id
            })
            return False
        except Exception as e:
            print(f"[Error in search]: {e}")
            
    def stop_search(self, player_id):
        for search in self.searches:
            if search["player_id"] == player_id:
                self.searches.remove(search)

    def start_wager(self, player1_id, player2_id):
        """
        Inform both players that a wager started, store it in self.wagers.
        """
        print(f"START WAGER [{player1_id}, {player2_id}]")
        try:
            start_msg = {
                "type": "start",
                "Start": True,
                "Player1": player1_id,
                "Player2": player2_id
            }
            self.send(player1_id, start_msg)
            self.send(player2_id, start_msg)
    
            self.wagers.append({
                "player1_id": player1_id,
                "player2_id": player2_id,
                "starters": [None, None]
            })
        except Exception as e:
            print(f"[Error in start_wager]: {e}")
            

    def choose_beginner(self, wager):
        """
        Choose a random player to start the first move
        """
        p1 = wager["player1_id"]
        p2 = wager["player2_id"]
        beginner = random.choice([1, 2])
        if beginner == 1:
            self.send(p1, {"type": "move", "EnemyMove": None})
        elif beginner == 2:
            self.send(p2, {"type": "move", "EnemyMove": None})

    def set_starter(self, player_id, starter_name):
        """
        The player picks a starter card.
        Once both players have set their starter, send each side the enemy starter.
        Then choose who begins.
        """
        try:
            for wager in self.wagers:
                p1 = wager["player1_id"]
                p2 = wager["player2_id"]
                if p1 == player_id:
                    wager["starters"][0] = starter_name
                    if wager["starters"][0] and wager["starters"][1]:
                        time.sleep(1)   # work around to fix race condition
                        self.send(p1, {"type": "enemyStarter", "EnemyStarter": wager["starters"][1]})
                        self.send(p2, {"type": "enemyStarter", "EnemyStarter": wager["starters"][0]})
                        wager["starters"][0] = None
                        wager["starters"][1] = None
                        self.choose_beginner(wager)
                    return True
                if p2 == player_id:
                    wager["starters"][1] = starter_name
                    if wager["starters"][0] and wager["starters"][1]:
                        time.sleep(1)
                        self.send(p1, {"type": "enemyStarter", "EnemyStarter": wager["starters"][1]})
                        self.send(p2, {"type": "enemyStarter", "EnemyStarter": wager["starters"][0]})
                        wager["starters"][0] = None
                        wager["starters"][1] = None
                        self.choose_beginner(wager)
                    return True
            return False
        except Exception as e:
            print(f"[Error in set_starter]: {e}")

    def move(self, player_id, json_data):
        """
        A player has made a move (like an attack).
        Send that move to the opponent as {"EnemyMove": move_name}.
        """
        for w in self.wagers:
            p1 = w["player1_id"]
            p2 = w["player2_id"]
            if p1 == player_id:
                # send to p2
                self.send(p2, json_data)
                return True
            elif p2 == player_id:
                # send to p1
                self.send(p1, json_data)
                return True
        return False

    def defeat(self, loser_id):
        """
        A player has conceded or lost.
        The other side wins => send them {"win": True}.
        """
        for w in self.wagers:
            p1 = w["player1_id"]
            p2 = w["player2_id"]
            if p1 == loser_id:
                # p2 is winner
                self.send(p2, {"type": "matchResult", "win": True})
                return True
            elif p2 == loser_id:
                # p1 is winner
                self.send(p1, {"type": "matchResult", "win": True})
                return True
        return False


class WagerServer:
    def __init__(self):
        """
        Keep track of each player's socket connection.
        """
        self.connected_players = {}  # player_id -> conn
        self.wager_manager = WagerManager(self.send_to_player)

    def send_to_player(self, player_id, message):
        """Send a JSON dict to the player's socket if connected."""
        conn = self.connected_players.get(player_id)
        if not conn:
            print(f"No connection for player {player_id}")
            return
        try:
            data = json.dumps(message).encode("utf-8")
            print(f"SEND to id[{player_id}]: {data}")
            compressed = zlib.compress(data)
            conn.sendall(compressed)
        except Exception as e:
            print(f"Error sending to {player_id}: {e}")

    def handle_client(self, conn, addr):
        """
        Thread function that receives multiple messages from this conn.
        We'll store the player's ID once we get it, so we can do self.connected_players[player_id] = conn.
        """
        player_id = None
        try:
            while True:
                raw = conn.recv(4096)
                if not raw:
                    print(f"Client {addr} disconnected.")
                    break
                try:
                    decompressed = zlib.decompress(raw).decode("utf-8")
                    json_data = json.loads(decompressed)
                except:
                    print("Error parsing packet from", addr)
                    continue

                packet_type = json_data["type"]
                print(f"RECEIVED from {addr}: {json_data}")

                match packet_type:
                    case "connect":
                        # example: {"type":"hello","player_id":123}
                        player_id = json_data["player_id"]
                        self.connected_players[player_id] = conn
                        # optionally send a greeting
                        self.send_to_player(player_id, {"type": "connect", "hello":"ok"})

                    case "search":
                        # {"type":"search","player_id":X,"enemy_id":Y}
                        pid = json_data["player_id"]
                        eid = json_data["enemy_id"]
                        self.wager_manager.search(pid, eid)

                    case "setStarter":
                            # {"type":"setStarter","player_id":X,"name":"..."}
                            pid = json_data["player_id"]
                            sname = json_data["name"]
                            self.wager_manager.set_starter(pid, sname)

                    case "move":
                        # {"type":"move","player_id":X,"move":"..."}
                        pid = json_data["player_id"]
                        self.wager_manager.move(pid, json_data)

                    case "defeat":
                        # {"type":"defeat","player_id":X}
                        pid = json_data["player_id"]
                        self.wager_manager.defeat(pid)

                    case "stopSearch":
                        player_id = json_data["player_id"]
                        self.wager_manager.stop_search(player_id)

        except Exception as e:
            print(f"Error in handle_client: {e}")
        finally:
            # remove from connected players if we know the ID
            if player_id and player_id in self.connected_players:
                self.connected_players.pop(player_id)
            conn.close()
            print(f"Connection closed for {addr} / player {player_id}")

    def start(self, host="0.0.0.0", port=27777):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port))
        s.listen()
        print(f"Wager server listening on {host}:{port}")

        while True:
            conn, addr = s.accept()
            print(f"New connection from {addr}")
            t = threading.Thread(target=self.handle_client, args=(conn, addr))
            t.start()


def main():
    srv = WagerServer()
    srv.start()

if __name__ == "__main__":
    main()
