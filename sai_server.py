# Authentication and Information Server - SAI

import socket
import threading
import json
from datetime import datetime


class SAI_Server:

    # Constructor method, called when an object of the class is created
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.users = {}
        self.online_users = set()   # Enforce uniqueness
        self.log_file = "game.log"  # Log server events

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()

            print(f"SAI Server listening on {self.host}:{self.port}")

            while True:
                conn, addr = s.accept()
                threading.Thread(target=self.handle_client,
                                 args=(conn, addr)).start()

    def handle_client(self, conn, addr):
        with conn:
            print(f"Connected by {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break

                message = data.decode("utf-8")
                self.handle_message(conn, message)

    def handle_message(self, conn, message):
        parts = message.split()
        command = parts[0]

        if command == "REGISTER":
            self.register_user(conn, parts[1], parts[2], parts[3])
        elif command == "LOGIN":
            self.login_user(conn, parts[1], parts[2])
        elif command == "LIST-USER-ON-LINE":
            self.send_online_users(conn)
        elif command == "LIST-USER-PLAYING":
            self.send_playing_users(conn)
        elif command == "GAME_INI":
            self.initiate_game(conn, parts[1], parts[2])
        # Add other commands as needed

    def register_user(self, conn, name, username, password):
        # Implement user registration logic
        pass

    def login_user(self, conn, username, password):
        # Implement user login logic
        pass

    def send_online_users(self, conn):
        # Implement logic to send a list of online users to the requesting user
        pass

    def send_playing_users(self, conn):
        # Implement logic to send a list of users playing to the requesting user
        pass

    def initiate_game(self, conn, user_a, user_b):
        # Implement logic to initiate a game between two users
        pass

    def log_event(self, event):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a") as log:
            log.write(f"{current_time}: {event}\n")


# Script being executed as main program and being run directly
if __name__ == "__main__":
    sai_server = SAI_Server("127.0.0.1", 4000)  # SAI instance
    sai_server.start()                          # Initiates server's execution
