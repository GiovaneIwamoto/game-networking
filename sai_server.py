# Authentication and Information Server - SAI

import socket
import threading
import json
import time
import uuid
from datetime import datetime


class SAI_Server:

    # Constructor method, called when an object of the class is created
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.users = {}
        self.games = {}
        self.online_users = {}
        self.log_file = "game.log"  # Log server events
        self.load_users_from_file()  # Load users database

    # Load users data from database file
    def load_users_from_file(self):
        try:
            with open("database.txt", "r") as file:
                for line in file:
                    if line.strip():  # Check if the line is not empty
                        user_data = json.loads(line)
                        username, data = user_data.popitem()
                        self.users[username] = data  # Filling user dictionary

        except FileNotFoundError:
            print("\n ⚠️  DATABASE FILE NOT FOUND\n")

        # Empty database JSON format check
        else:
            if not self.users:
                print("\n ⚠️  DATABASE FILE IS EMPTY\n")

    # Save registered users to database file
    def save_users_to_file(self):
        with open("database.txt", "w") as file:
            for username, user_data in self.users.items():
                json.dump({username: user_data}, file)
                file.write("\n")

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

            logged_in_username = None  # Save username for disconnection control

            connection_event = f"⚡ CONNECTED BY {addr}"
            self.stdout_event(connection_event)

            while True:
                try:
                    data = conn.recv(1024)  # Client data

                    if not data:
                        # Disconnection using logout command only if user was logged in
                        if logged_in_username:
                            disconnect_event = f"🍃 USER DISCONNECTED: {logged_in_username}"

                            # Stdout SAI server event
                            self.stdout_event(disconnect_event)
                            # Disconnect event to log file
                            self.log_event(disconnect_event)

                            # Update status for offline when logged out
                            self.users[logged_in_username]['status'] = 'OFFLINE'
                            self.save_users_to_file()

                            del self.online_users[logged_in_username]
                        break

                    # Handle commands
                    message = data.decode("utf-8")
                    logged_in_username = self.handle_message(
                        conn, message, logged_in_username)

                # Disconnected handler for connection reset error
                except ConnectionResetError:
                    if logged_in_username:
                        disconnect_event = f"🍃 USER DISCONNECTED: {logged_in_username}"

                        # Stdout SAI server event
                        self.stdout_event(disconnect_event)
                        # Disconnect event to log file
                        self.log_event(disconnect_event)

                        # Update status for offline when connection error
                        self.users[logged_in_username]['status'] = 'OFFLINE'
                        self.save_users_to_file()

                        del self.online_users[logged_in_username]
                    break

     # Add connection to online user
    def add_user_connection(self, username, conn):
        self.online_users[username] = conn

    # Remove connection to offline user
    def remove_user_connection(self, username):
        if username in self.online_users:
            del self.online_users[username]

    # Get connection from user
    def get_user_connection(self, username):
        return self.online_users.get(username, None)

    # Communication protocol, commands trigger server-side actions
    def handle_message(self, conn, message, logged_in_username):
        parts = message.split()
        command = parts[0]

        if command == "REGISTER":
            self.register_user(conn, parts[1], parts[2])

        elif command == "LOGIN":
            is_logged_in = self.login_user(conn, parts[1], parts[2])

            if is_logged_in:
                # Update only if login is successful
                logged_in_username = parts[1]

        elif command == "LIST-USERS-ONLINE":
            self.send_online_users(conn, parts[1])

        # elif command == "LIST-USER-PLAYING":
        #     self.send_playing_users(conn)

        elif command == "GAME_INI":
            self.initiate_game(conn, parts[1], parts[2])

        return logged_in_username  # Important return for disconnection control

    # User registration server response
    def register_user(self, conn, username, password):

        # Existing username check
        if username in self.users:
            response = "🚨 USERNAME ALREADY IN USE PLEASE CHOOSE ANOTHER\n"

        else:
            # Add to username dictionary
            self.users[username] = {'password': password, 'status': 'OFFLINE'}

            # Event log register
            user_event = f"⭐ REGISTERED NEW USER: {username}"

            self.stdout_event(user_event)  # Stdout SAI server event
            self.log_event(user_event)  # Save registration event to log file

            self.save_users_to_file()   # Save user data to database file

            response = "✅ REGISTRATION SUCCESSFUL\n"

        # Client response
        conn.send(response.encode("utf-8"))

    # User login server response
    def login_user(self, conn, username, password):
        # Check username exists in database
        if username in self.users:

            # Check password match stored password
            if self.users[username]['password'] == password:
                # Get client's address info
                ip, port = conn.getpeername()

                # Update ip and port when logged in, user's last login address
                self.users[username]['ip'] = ip
                self.users[username]['port'] = port

                # Update status for online when logged in
                self.users[username]['status'] = 'ONLINE'

                # Event log login
                user_event = f"📌 USER LOGGED IN: {username}"

                self.stdout_event(user_event)  # Stdout SAI server event
                self.log_event(user_event)  # Save login event to log file

                self.save_users_to_file()   # Save user data to database file

                # Add user's connection
                self.add_user_connection(username, conn)

                response = "✅ LOGIN SUCCESSFUL\n"
                conn.send(response.encode("utf-8"))

                return username
            else:
                response = "🚨 INVALID PASSWORD\n"
        else:
            response = "🚨 USERNAME NOT FOUND\n"

        # Send the response to the client
        conn.send(response.encode("utf-8"))

    # Users online server response
    def send_online_users(self, conn, logged_in_username):

        # All users online except current user
        online_users = [(username, data.get('status'), data.get('ip'), data.get('port'))
                        for username, data in self.users.items()
                        if data.get('status') == 'ONLINE' and username != logged_in_username]

        if online_users:
            response = "🤖 ONLINE USERS:\n\n"
            for user_info in online_users:
                username, status, ip, port = user_info
                response += f"👤 {username} | STATUS: {status} | IP: {ip} | PORT: {port}\n"
        else:
            response = "👻 NO USERS ARE CURRENTLY ONLINE\n"

        conn.send(response.encode("utf-8"))

    # def send_playing_users(self, conn):
    #     # Implement logic to send a list of users playing to the requesting user
    #     pass

    # Game initiation server response

    def initiate_game(self, conn, player1, player2):

        # Can not invite yourself for a game
        if player1 != player2:

            # Check users existence
            if player1 in self.users and player2 in self.users:

                # Check if user invited is online
                if self.users[player1]['status'] == 'ONLINE' and self.users[player2]['status'] == 'ONLINE':

                    # Generate unique token for the game
                    game_token = self.generate_unique_token()

                    # Initiate game notification
                    response_receiver = f"🔔 {player1} INVITED YOU TO JOIN A GAME\n"
                    response_sender = f"🔔 INVITED {player2} TO A GAME. WAITING FOR RESPONSE...\n"

                    # Get participants connections
                    conn_sender = self.get_user_connection(player1)
                    conn_receiver = self.get_user_connection(player2)

                    # Starting game infos
                    game_info = {
                        'token': game_token,
                        'players': [player1, player2],
                        'status': 'PENDING',  # can be PENDING or ACCEPTED or DECLINED
                    }

                    # Store game infos to server
                    self.games[game_token] = game_info

                    # If connections exists, send notification
                    if conn_sender:
                        conn_sender.send(response_sender.encode("utf-8"))

                    if conn_receiver:
                        conn_receiver.send(response_receiver.encode("utf-8"))

                    # Start thread to wait for invited player's response
                    threading.Thread(target=self.wait_for_response,
                                     args=(game_token,)).start()

                    return

        response = "💣 PLAYER NOT FOUND OR OFFLINE\n"
        conn.send(response.encode("utf-8"))

    # Wait for invited player response
    def wait_for_response(self, game_token):
        game_info = self.games[game_token]

        while game_info['status'] == 'PENDING':
            time.sleep(10)

        return game_info['status']  # Return ACCEPTED or DECLINED

    # Sender's logic to process guest response
    def process_response(self, game_token, response):

        game_info = self.games[game_token]
        game_info['status'] = response

        player1, player2 = game_info['players']
        conn_player1 = self.get_user_connection(player1)

        if response == 'accepted':
            notification = f"🎮 {player2} ACCEPTED YOUR GAME INVITATION ({game_token}). LET THE GAME BEGIN!\n"
        else:
            notification = f"❌ {player2} DECLINED YOUR GAME INVITATION ({game_token}).\n"

        if conn_player1:
            conn_player1.send(notification.encode("utf-8"))

    # Log file event addition
    def log_event(self, event):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(self.log_file, "a", encoding="utf-8") as log:
            log.write(f"{current_time}: {event}\n")

    # Stdout time and event printing
    def stdout_event(self, event):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{current_time}: {event}")

    # Generate unique token for game
    def generate_unique_token(self):
        return str(uuid.uuid4())


# Script being executed as main program and being run directly
if __name__ == "__main__":
    sai_server = SAI_Server("127.0.0.1", 4000)  # SAI instance
    sai_server.start()                          # Initiates server's execution
