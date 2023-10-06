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
        self.load_users_from_file()  # Load users database

    # Load users data from database file
    def load_users_from_file(self):
        try:
            with open("database.txt", "r") as file:
                content = file.read()

                # Empty database JSON format check
                if content:
                    self.users = json.loads(content)  # Filling user dictionary
                else:
                    print("\n ⚠️  DATABASE FILE IS EMPTY, SHUTTING DOWN\n")

        except FileNotFoundError:
            print("\n ⚠️  DATABASE FILE NOT FOUND, SHUTTING DOWN\n")

    # Save registered users to database file
    def save_users_to_file(self):
        with open("database.txt", "w") as file:
            json.dump(self.users, file)

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # Socket object TCP
            s.bind((self.host, self.port))
            s.listen()

            print(f"☎️  SAI SERVER LISTENING ON {self.host}:{self.port}\n")

            # Loop for incoming clients connections
            while True:
                conn, addr = s.accept()

                # Handle multiple client connections concurrently
                threading.Thread(target=self.handle_client,
                                 args=(conn, addr)).start()

    def handle_client(self, conn, addr):
        with conn:
            print(f"⚡ CONNECTED BY {addr}")
            while True:
                data = conn.recv(1024)  # Client data
                if not data:
                    break

                message = data.decode("utf-8")
                self.handle_message(conn, message)

    # Communication protocol, commands trigger server-side actions
    def handle_message(self, conn, message):
        parts = message.split()
        command = parts[0]

        if command == "REGISTER":
            self.register_user(conn, parts[1], parts[2])

        elif command == "LOGIN":
            self.login_user(conn, parts[1], parts[2])

        # elif command == "LIST-USER-ON-LINE":
        #     self.send_online_users(conn)

        # elif command == "LIST-USER-PLAYING":
        #     self.send_playing_users(conn)

        # elif command == "GAME_INI":
        #     self.initiate_game(conn, parts[1], parts[2])

    # User registration server response
    def register_user(self, conn, username, password):

        # Existing username check
        if username in self.users:
            response = "🚨 USERNAME ALREADY IN USE PLEASE CHOOSE ANOTHER"

        else:
            # Add to username dictionary
            self.users[username] = {'password': password}

            # Event log register
            user_event = f"⭐ REGISTERED NEW USER: {username}"

            print(user_event)  # Stdout SAI server event

            self.log_event(user_event)  # Save registration event to log file
            self.save_users_to_file()   # Save user data to database file

            response = "✅ REGISTRATION SUCCESSFUL"

        # Client response
        conn.send(response.encode("utf-8"))

    # User login server response
    def login_user(self, conn, username, password):
        # Implement user login logic
        pass

    # def send_online_users(self, conn):
    #     # Implement logic to send a list of online users to the requesting user
    #     pass

    # def send_playing_users(self, conn):
    #     # Implement logic to send a list of users playing to the requesting user
    #     pass

    # def initiate_game(self, conn, user_a, user_b):
    #     # Implement logic to initiate a game between two users
    #     pass

    # Log file event addition
    def log_event(self, event):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(self.log_file, "a", encoding="utf-8") as log:
            log.write(f"{current_time}: {event}\n")


# Script being executed as main program and being run directly
if __name__ == "__main__":
    sai_server = SAI_Server("127.0.0.1", 4000)  # SAI instance
    sai_server.start()                          # Initiates server's execution
