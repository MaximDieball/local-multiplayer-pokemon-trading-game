import socket
import threading
import zlib
import json

class WagerClient:
    def __init__(self, host="127.0.0.1", port=27777):
        self.host = host
        self.port = port
        self.sock = None
        self.player_id = None

    def connect(self):
        """Connect to the Wager server and start a read thread."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        print(f"Connected to server at {self.host}:{self.port}")

        # Start a background thread to read server messages
        t = threading.Thread(target=self.read_loop, daemon=True)
        t.start()

    def read_loop(self):
        """Continuously receive and print server messages."""
        while True:
            try:
                data = self.sock.recv(4096)
                if not data:
                    print("Server closed the connection.")
                    break
                # Decompress & decode
                try:
                    decompressed = zlib.decompress(data).decode("utf-8")
                    packet = json.loads(decompressed)
                    print(f"\n[SERVER MESSAGE]: {packet}\ncommand:", end="", flush=True)
                except Exception as e:
                    print(f"\n[Error parsing server data]: {e}\ncommand:", end="", flush=True)
            except Exception as e:
                print(f"[Error in read_loop]: {e}")
                break

    def send_packet(self, packet: dict):
        """Send a JSON packet to the server, compressed."""
        try:
            raw = json.dumps(packet).encode("utf-8")
            compressed = zlib.compress(raw)
            self.sock.sendall(compressed)
        except Exception as e:
            print(f"[Error sending packet]: {e}")

    def run_cli(self):
        """Run a simple CLI loop using match for commands."""
        print("Commands:\n"
              "  hello <player_id>\n"
              "  search <enemy_id>\n"
              "  setStarter <name>\n"
              "  move <move_name>\n"
              "  defeat\n"
              "  quit\n")
        while True:
            cmd = input("command:").strip()
            if not cmd:
                continue
            parts = cmd.split(maxsplit=1)
            main_cmd = parts[0].lower()
            argument = ""
            if len(parts) > 1:
                argument = parts[1]

            match main_cmd:
                case "quit":
                    print("Quitting client.")
                    break
                case "hello":
                    if argument.isdigit():
                        self.player_id = int(argument)
                        packet = {"type":"hello","player_id": self.player_id}
                        self.send_packet(packet)
                    else:
                        print("Usage: hello <player_id>")
                case "search":
                    if not self.player_id:
                        print("Need 'hello' first.")
                    else:
                        if argument.isdigit():
                            enemy_id = int(argument)
                            packet = {"type":"search","player_id": self.player_id,"enemy_id": enemy_id}
                            self.send_packet(packet)
                        else:
                            print("Usage: search <enemy_id>")
                case "setstarter":
                    if not self.player_id:
                        print("Need 'hello' first.")
                    else:
                        if argument:
                            packet = {"type":"setStarter","player_id": self.player_id,"name": argument}
                            self.send_packet(packet)
                        else:
                            print("Usage: setStarter <name>")
                case "move":
                    if not self.player_id:
                        print("Need 'hello' first.")
                    else:
                        if argument:
                            packet = {"type":"move","player_id": self.player_id,"move": argument}
                            self.send_packet(packet)
                        else:
                            print("Usage: move <move_name>")
                case "defeat":
                    if not self.player_id:
                        print("Need 'hello' first.")
                    else:
                        packet = {"type":"defeat","player_id": self.player_id}
                        self.send_packet(packet)
                case _:
                    print("Unknown or malformed command.")
        self.sock.close()
        print("Client socket closed.")

    def start(self):
        self.connect()
        self.run_cli()


def main():
    client = WagerClient()
    client.start()

if __name__ == "__main__":
    main()
