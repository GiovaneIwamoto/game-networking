# Authentication and Information Server - SAI

import socket
import threading
import json
import uuid
import os
from datetime import datetime


class SAI_Server:

    # Constructor method, called when an object of the class is created
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.users = {}
        self.games = {}
        self.online_users = {}
        self.playing_users = {}
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

    # Get user address IP and PORT
    def get_user_address(self, username):
        if username in self.users:
            user_data = self.users[username]
            ip = user_data.get('ip', 'UNKNOWN')
            port = user_data.get('port', 'UNKNOWN')
            return f"{ip}:{port}"
        else:
            return 'UNKNOWN'

    # Initiate socket
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

            # connection_event = f"⚡ CONNECTED BY {addr}"
            # self.stdout_event(connection_event)

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

        # Register user command
        if command == "REGISTER":
            if len(parts) >= 3:
                self.register_user(conn, parts[1], parts[2])
            else:
                conn.send("🚨 BOTH FIELDS MUST BE FILLED IN\n".encode("utf-8"))

        # Login user command
        elif command == "LOGIN":
            if len(parts) >= 3:
                is_logged_in = self.login_user(conn, parts[1], parts[2])

                if is_logged_in:
                    # Update only if login is successful
                    logged_in_username = parts[1]
            else:
                conn.send("🚨 BOTH FIELDS MUST BE FILLED IN\n".encode("utf-8"))

        # List online users command
        elif command == "LIST_USERS_ONLINE":
            self.send_online_users(conn, parts[1])

        # List playing users command
        elif command == "LIST_USERS_PLAYING":
            self.send_playing_users(conn)

        # Game initiation command
        elif command == "GAME_INI":
            if len(parts) >= 3:
                self.initiate_game(conn, parts[1], parts[2])
            else:
                conn.send("🚨 INVALID USER\n".encode("utf-8"))

        # Game start command
        elif command == "GAME_START":
            self.start_game(conn, parts[1], parts[2])

        # Send to guest connection port command
        elif command == "SEND_GUEST_CONN_PORT":
            self.send_guest_conn_port(parts[1], parts[2])

        # Game over command
        elif command == "GAME_OVER":
            self.game_over(parts[1])

        # User back available command
        elif command == "AVAILABLE":
            self.set_invite_status_available(parts[1])

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
            # Check username already logged in
            if self.users[username]['status'] == 'OFFLINE':
                # Check password match stored password
                if self.users[username]['password'] == password:
                    # Get client's address info
                    ip, port = conn.getpeername()

                    # Update ip and port when logged in, user's last login address
                    self.users[username]['ip'] = ip
                    self.users[username]['port'] = port

                    # Update status for online when logged in
                    self.users[username]['status'] = 'ONLINE'

                    # Update status for logged in users to available to receive notifications
                    self.users[username]['notification'] = 'AVAILABLE'

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
                response = "🚨 USER ALREADY LOGGED IN\n"
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
                response += f"🟢 👤 {username} | STATUS: {status} | IP: {ip} | PORT: {port}\n"
        else:
            response = "👻 NO USERS ARE CURRENTLY ONLINE\n"

        conn.send(response.encode("utf-8"))

    # Users playing server response
    def send_playing_users(self, conn):

        playing_users = [(username, data.get('status'), data.get('ip'), data.get('port'))
                         for username, data in self.users.items()
                         if data.get('status') == 'PLAYING']

        if playing_users:
            response = "🤖 PLAYING USERS:\n\n"

            # Iterate over pairs of playing users
            for i in range(0, len(playing_users), 2):
                user1 = playing_users[i]
                user2 = playing_users[i + 1] if i + \
                    1 < len(playing_users) else None

                response += f"🔴 👤 {user1[0]} | {user1[2]}:{user1[3]}"
                if user2:
                    response += f" X 👤 {user2[0]} | {user2[2]}:{user2[3]}"
                response += "\n"
        else:
            response = "👻 NO USERS ARE CURRENTLY PLAYING\n"
        conn.send(response.encode("utf-8"))

    # Game initiation server response
    def initiate_game(self, conn, host, guest):

        # HOST means the user who sends the invitation, GUEST means the user who will be invited
        # Can not invite yourself for a game
        if host != guest:

            # Check users existence
            if host in self.users and guest in self.users:

                # Check if host user is online, guest is online or playing, guest is available to receive notifications
                if (self.users[host]['status'] == 'ONLINE') and (self.users[guest]['status'] == 'ONLINE' or self.users[guest]['status'] == 'PLAYING') and (self.users[guest]['notification'] == 'AVAILABLE'):

                    # Generate unique token for the game
                    game_token = self.generate_unique_token()

                    # Initiate game notification
                    response_host = f"🔔 INVITED {guest} TO A GAME\n"

                    response_guest_online = f"🔔 {host} INVITED YOU TO JOIN A GAME\n"
                    response_guest_playing = f"🔔 {host} INVITED YOU TO JOIN ANOTHER GAME\n"

                    # Get participants connections
                    conn_host = self.get_user_connection(host)
                    conn_guest = self.get_user_connection(guest)

                    # Starting game infos
                    game_info = {
                        'token': game_token,
                        'players': [host, guest],
                        'status': 'PENDING',  # Can be PENDING or ACCEPTED or DECLINED
                    }

                    # Store game infos to server
                    self.games[game_token] = game_info

                    # If connections exists, send notification
                    if conn_host:
                        conn_host.send(response_host.encode("utf-8"))

                        # Set availability to receive notifications to busy
                        self.users[host]['notification'] = 'BUSY'
                        self.users[guest]['notification'] = 'BUSY'
                        self.save_users_to_file()   # Save user data to database file

                    # Invite to join a new game for an online user
                    if conn_guest and self.users[guest]['status'] == 'ONLINE':
                        conn_guest.send(response_guest_online.encode("utf-8"))

                    # Invite to join another game for a playing user
                    if conn_guest and self.users[guest]['status'] == 'PLAYING':
                        conn_guest.send(response_guest_playing.encode("utf-8"))

                    # Wait for guest response
                    response = None

                    def wait_for_response():  # Wait for a response
                        nonlocal response
                        response = conn_guest.recv(1024).decode("utf-8")

                    # Create a thread to run wait for response function
                    response_thread = threading.Thread(
                        target=wait_for_response)

                    response_thread.start()  # Start thread

                    # Wait for thread to finish or timeout
                    response_thread.join(timeout=15)  # Timeout 15 seconds

                    if response is None:  # No response received within timeout
                        # Guest did not answer
                        game_info['status'] = 'DECLINED'
                        response_afk = "TIMEOUT"
                        response_ignore = "IGNORED"

                        # Set availability to receive notifications back to available
                        self.users[host]['notification'] = 'AVAILABLE'
                        self.users[guest]['notification'] = 'AVAILABLE'
                        self.save_users_to_file()   # Save user data to database file

                        # User online and do not respond
                        if self.users[guest]['status'] == 'ONLINE':
                            # Event user seems to be afk, doesn't answer
                            afk_event = f"💤 USER SEEMS TO BE AFK: {guest}"
                            response_guest = response_afk

                            # Guest is still AFK, did not answer previous notification, keep him busy
                            self.users[guest]['notification'] = 'BUSY'
                            self.save_users_to_file()   # Save user data to database file

                            # Stdout SAI server event
                            self.stdout_event(afk_event)
                            # Afk event to log file
                            self.log_event(afk_event)

                        # User playing and did not respond
                        elif self.users[guest]['status'] == 'PLAYING':
                            # Event user ignored invite, didn't answer
                            response_guest = response_ignore

                        if conn_host:  # Send to host timeout
                            conn_host.send(response_guest.encode("utf-8"))

                        if conn_guest:  # Send to guest timeout
                            conn_host.send(response_guest.encode("utf-8"))
                    else:
                        # Set availability to receive notifications back to available
                        self.users[host]['notification'] = 'AVAILABLE'
                        self.users[guest]['notification'] = 'AVAILABLE'
                        self.save_users_to_file()   # Save user data to database file

                        # Invitation accepted by guest
                        if response == "GAME_ACK":
                            game_info['status'] = 'ACCEPTED'

                            # Send to host user client response command
                            response_host_accepted = "ACCEPTED"

                            if conn_host:
                                conn_host.send(
                                    response_host_accepted.encode("utf-8"))

                        # Invitation declined by guest
                        elif response == "GAME_NEG":
                            game_info['status'] = 'DECLINED'

                            # Send to host user client response command
                            response_host_declined = "DECLINED"

                            if conn_host:
                                conn_host.send(
                                    response_host_declined.encode("utf-8"))

                        # Unexpected response from guest
                        else:
                            game_info['status'] = 'DECLINED'

                            # Invitation cancelled by server
                            response_host_unexpected = "UNEXPECTED RESPONSE"
                            if conn_host:
                                conn_host.send(
                                    response_host_unexpected.encode("utf-8"))

                # Guest is busy, still trying to deal with an invitation
                elif self.users[guest]['notification'] == 'BUSY':
                    response_host = f"📞 {guest} IS DEALING WITH ANOTHER INVITE, TRY AGAIN LATER\n"

                    # Get host connection
                    conn_host = self.get_user_connection(host)
                    if conn_host:
                        conn_host.send(response_host.encode("utf-8"))

        # Guest not found or offline
        response = "💣 PLAYER NOT FOUND OR OFFLINE\n"
        conn.send(response.encode("utf-8"))

    # Change users status to playing
    def start_game(self, conn, host, guest):
        # Events
        playing_event_host = f"🥊 USER IS PLAYING: {host}"
        playing_event_guest = f"🥊 USER IS PLAYING: {guest}"
        playing_event_both = f"🔥 USERS IN MATCH: {host} X {guest}"

        # Stdout SAI server event
        self.stdout_event(playing_event_host)
        self.stdout_event(playing_event_guest)
        self.stdout_event(playing_event_both)

        # Playing event to log file
        self.log_event(playing_event_host)
        self.log_event(playing_event_guest)
        self.log_event(playing_event_both)

        # Update status for playing
        self.users[host]['status'] = 'PLAYING'
        self.users[guest]['status'] = 'PLAYING'
        self.save_users_to_file()

    # Send to guest which port should connect server response
    def send_guest_conn_port(self, player_guest, port):
        # Get guest's address by username
        conn_guest = self.get_user_connection(player_guest)
        response_guest = f"CONNECT TO PORT {port}"

        if conn_guest:
            conn_guest.send(response_guest.encode("utf-8"))

    # Set back user status to online
    def game_over(self, player_self):
        # Inactive means user is no longer in a game and is now available
        inactive_event_self = f"🌀 USER BECAME INACTIVE: {player_self}"

        # Stdout SAI server event
        self.stdout_event(inactive_event_self)

        # Inactive event to log file
        self.log_event(inactive_event_self)

        # Update status for online
        self.users[player_self]['status'] = 'ONLINE'
        self.save_users_to_file()

    # Set user status to available to receive notifications
    def set_invite_status_available(self, self_user):
        self.users[self_user]['notification'] = 'AVAILABLE'
        self.save_users_to_file()   # Save user data to database file

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
    os.system('cls' if os.name == 'nt' else 'clear')
    sai_server = SAI_Server("127.0.0.1", 4000)  # SAI instance
    sai_server.start()                          # Initiates server's execution
