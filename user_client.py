import threading
import select
import socket
import random
import time
import os


class User_Client:

    # Constructor method, creates socket
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lock = threading.Lock()
        self.running = True  # Invite listener thread controller
        self.notification = False  # Active notification controller
        self.input_ack_neg = False  # Controller for accept or decline notification at input
        self.inviter = None  # Store inviter username when user receive a notification
        self.response_in_game = None  # Store SAI invite response when user is playing
        self.match_declined = False  # Controller for refused invites while playing
        self.invite_time_left = 0  # Timer for expired invitation

        # True means invite has expired, False means invite still can be ack or neg
        self.invite_expired = False

    # Connection to server
    def connect(self):
        self.sock.connect((self.host, self.port))

        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"💡 CONNECTED TO SERVER ON {self.host}:{self.port}")

    # Message sender method
    def send_message(self, message):
        # Socket send message to server
        self.sock.sendall(message.encode("utf-8"))

    # Server response receiver
    def receive_response(self):
        try:
            data = self.sock.recv(1024)  # Socket receive response from server
            if not data:
                return None
            response = data.decode("utf-8")
            return response
        except ConnectionAbortedError as e:
            print(
                f"⛔ CONNECTION WAS TERMINATED BY THE SOFTWARE ON THE HOST")
            return None
        except Exception as e:
            print(f"⛔ AN UNHANDLED EXCEPTION OCCURRED")

    # Send registration command
    def register_user(self, username, password):
        # Send username and password
        command = f"REGISTER {username} {password}"
        self.send_message(command)

        response = self.receive_response()  # Receive response from server
        print(f"\n{response}")

    # Send login command
    def login_user(self, username, password):
        command = f"LOGIN {username} {password}"
        self.send_message(command)

        response = self.receive_response()  # Receive response from server
        print(f"\n{response}")

        # If user authenticated return username
        if "LOGIN SUCCESSFUL" in response:
            return username
        else:
            return None

    # Send list users online command
    def list_users_online(self, logged_in_username):
        command = f"LIST_USERS_ONLINE {logged_in_username}"
        self.send_message(command)

        response = self.receive_response()
        print(f"\n{response}")

    def list_users_playing(self):
        command = "LIST_USERS_PLAYING"
        self.send_message(command)

        response = self.receive_response()
        print(f"\n{response}")

    # Send initiate game command
    def initiate_game(self, player_host, player_guest):

        # HOST means the user who sends the invitation, GUEST means the user who will be invited
        command = f"GAME_INI {player_host} {player_guest}"
        self.send_message(command)

        response = self.receive_response()
        print(f"\n{response}")

        # Send invite and wait for guest response
        if "INVITED" in response:
            print("⏰ WAITING 15 SEC FOR GUEST RESPONSE\n")

            response_invite = self.receive_response()

            # Accepted, host received GAME_ACK
            if "ACCEPTED" in response_invite:
                print(f"🍾 GUEST ACCEPTED GAME INVITE\n")

                # Inviter user start P2P connection when guest accept invite
                self.start_connection(player_host, player_guest)

            # Declined, host receveid GAME_NEG
            elif "DECLINED" in response_invite:
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"🧹 GAME INVITE DECLINED BY GUEST\n")

            # Timeout, user invited is online but did not respond
            elif "TIMEOUT" in response_invite:
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"💤 GUEST SEEMS TO BE AFK\n")

            # Ignored, user invited is playing but ignored invitation
            elif "IGNORED" in response_invite:
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"🔕 GUEST IGNORED YOUR INVITATION\n")

            else:
                print("❓ UNEXPECTED RESPONSE FROM GUEST\n")

    # Inviter sends socket port to invitee command
    def start_connection(self, player_host, player_guest):
        # Host player creates a socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as game_socket_host:

            # Links to an available address
            game_socket_host.bind((self.host, 0))
            _, self_port = game_socket_host.getsockname()
            game_socket_host.listen(1)  # Only one connection

            print(
                f"🔗 WAITING FOR {player_guest} TO CONNECT ON PORT {self_port}\n")

            # Send to SAI server guest's username and which port should connect
            command = f"SEND_GUEST_CONN_PORT {player_guest} {self_port}"
            self.send_message(command)

            # Waits until invitee connects to host
            # Upon connection new socket is created for communication with the guest
            game_socket_P2P, _ = game_socket_host.accept()

            if game_socket_P2P:
                # Send to SAI game start command
                command = f"GAME_START {player_host} {player_guest}"
                self.send_message(command)

                print(f"🎉 CONNECTED TO {player_guest}. STARTING GAME...\n")

                try:
                    # Connected start game
                    self.start_game(game_socket_P2P, player_host, player_guest)

                    # Host after match ends send to SAI game over command to set back status to online
                    command = f"GAME_OVER {player_host}"
                    self.send_message(command)

                    game_socket_P2P.close()  # Close socket

                # Host view, guest had lost connection or left game
                except Exception as e:
                    print("🚨 FAILED TO CONNECT TO GUEST/n")

                    # Host after match ends send to SAI game over command to set back status to online
                    command = f"GAME_OVER {player_host}"
                    self.send_message(command)

                    # Show host win message
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(
                        f"💨 OPNT: {player_guest} HAS LEFT THE GAME, LEAVING MATCH\n")
                    print(
                        f"🥇 CONGRATULATIONS, {player_host}! YOU ARE THE WINNER!\n")

                    print("⌚ RETURNING TO LOBBY\n")
                    time.sleep(1)

                    game_socket_P2P.close()
                    # Send anything back to SAI to reload client response receiver
                    self.send_message("NOTHING")

    # Game logic
    def start_game(self, game_socket_self, player_self, player_opponent):
        while True:
            # Score counter
            score_self = 0
            score_opponent = 0

            for round_number in range(1, 6):  # Five rounds
                leave_match = False  # User left match

                # Invitation inside match received
                if (self.notification == True) and (self.invite_expired == False):
                    # Save inviter username
                    parts = self.response_in_game.split()
                    self.inviter = parts[1]

                    os.system('cls' if os.name == 'nt' else 'clear')

                    while True:
                        print(f"📬 NEW NOTIFICATION:\n{self.response_in_game}")
                        print(f"📢 SEND BACK ACK TO {self.inviter}:\n")
                        print("[8] LEAVE THE MATCH TO ACCEPT INVITE")
                        print("[9] DECLINE INVITATION AND CONTINUE PLAYING")

                        choice = input("\n📟 CHOOSE AN OPTION: ")

                        if choice == "8":  # Accept invitation to join another match
                            # Accepted but invite has already expired
                            if self.invite_expired == True:
                                os.system('cls' if os.name ==
                                          'nt' else 'clear')
                                print(
                                    f"📢 INVITATION FROM {self.inviter} EXPIRED")
                                print(
                                    f"♻️  CONTINUING MATCH AGAINST {player_opponent}")
                                time.sleep(1)

                                # When returns to lobby, client do not deal with the invitation
                                self.notification = False
                                self.input_ack_neg = False  # Remove ack and neg as valid option at input
                                self.response_in_game = None  # Store SAI invite response from invitation
                                self.invite_expired = True  # Set invite to expired again
                                leave_match = False  # User don't leave match

                                # Not used to refuse invitation but to tell client there is no need to deal with this invite anymore
                                self.match_declined = True
                                break

                            else:  # Invite not expired
                                print("\n🟠 LEAVING MATCH\n")
                                time.sleep(1)

                                self.notification = True  # When returns to lobby, client deal with the invitation
                                leave_match = True  # User left match

                                self.input_ack_neg = False  # Remove ack and neg as valid option at input
                                self.response_in_game = None  # Store SAI invite response from invitation
                                self.invite_expired = False  # Invite not expired

                                os.system('cls' if os.name ==
                                          'nt' else 'clear')

                                print(
                                    f"💨 SELF: {player_self}, YOU LEFT THE MATCH\n")
                                print(
                                    f"🥈 SORRY, {player_self}! YOU LOST THE GAME!\n")

                                print("⌚ RETURNING TO LOBBY\n")
                                time.sleep(1)
                                break

                        elif choice == "9":  # Decline invitation, continue playing
                            print("\n🔴 DECLINING")
                            print(
                                f"♻️ CONTINUING MATCH AGAINST {player_opponent}")

                            time.sleep(1)

                            os.system('cls' if os.name == 'nt' else 'clear')

                            # When returns to lobby, client do not deal with the invitation
                            self.notification = False
                            self.input_ack_neg = False  # Remove ack and neg as valid option at input
                            self.response_in_game = None  # Store SAI invite response from invitation
                            self.invite_expired = True  # Set invite to expired
                            leave_match = False  # User do not leave match

                            # Match was declined, no need to deal with this invite anymore when return to lobby
                            self.match_declined = True
                            break

                        else:  # Invalid input
                            os.system('cls' if os.name == 'nt' else 'clear')
                            print("\n⛔ INVALID OPTION, CHOOSE A VALID ONE\n")

                if leave_match == True:  # Player self left match to join another one
                    break

                os.system('cls' if os.name == 'nt' else 'clear')
                print(
                    f"🦀 ROUND {round_number}: {player_self} VS {player_opponent}\n")

                print(f"🌞 SELF TOTAL: {score_self} POINTS")
                print(f"🌚 OPNT TOTAL: {score_opponent} POINTS")
                print(f"\n🏁 TYPE [x] TO LEAVE MATCH")

                # Initialize the ocean board for each round
                ocean_board = self.initialize_ocean_board()

                self.display_ocean_empty()  # Display empty ocean

                # Get self player's move
                move_self = self.get_player_move(ocean_board)

                # Leave player's move
                if move_self == "LEAVE":
                    os.system('cls' if os.name == 'nt' else 'clear')
                    game_socket_self.send(move_self.encode('utf-8'))

                    print(
                        f"💨 SELF: {player_self}, YOU LEFT THE MATCH\n")
                    print(f"🥈 SORRY, {player_self}! YOU LOST THE GAME!\n")

                    print("⌚ RETURNING TO LOBBY\n")
                    time.sleep(1)
                    break

                # Send the animal type caught to the opponent
                game_socket_self.send(move_self.encode('utf-8'))

                # Update self score
                round_points_self = self.count_points(move_self)
                score_self += round_points_self

                print(f"\n🦗 WAITING FOR {player_opponent} ...\n")

                # Wait for opponent's response
                move_opponent = game_socket_self.recv(
                    1024).decode('utf-8')

                # Self waiting for opponent's response but received left command from opponent
                if move_opponent == "LEAVE":
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(
                        f"💨 OPNT: {player_opponent} HAS LEFT THE GAME, LEAVING MATCH\n")
                    print(
                        f"🥇 CONGRATULATIONS, {player_self}! YOU ARE THE WINNER!\n")

                    print("⌚ RETURNING TO LOBBY\n")
                    time.sleep(1)
                    break

                os.system('cls' if os.name == 'nt' else 'clear')
                print(
                    f"🦀 ROUND {round_number}: {player_self} VS {player_opponent}")

                # Update opponent score
                round_points_opponent = self.count_points(move_opponent)
                score_opponent += round_points_opponent

                # Get animal icon
                icon_self = self.get_animal_icon(move_self)
                icon_opponent = self.get_animal_icon(move_opponent)

                # Display the ocean result
                self.display_ocean_result(ocean_board)

                print(
                    f"\n🌞 SELF: {player_self} CAUGHT A {move_self} {icon_self} +{round_points_self}!\n   TOTAL: {score_self} POINTS")
                print(
                    f"\n🌚 OPNT: {player_opponent} CAUGHT A {move_opponent} {icon_opponent} +{round_points_opponent}!\n   TOTAL: {score_opponent} POINTS")

                if round_number == 5:
                    # Show results
                    print("\n⌚ GAME FINISHED! SHOWING RESULTS...\n")
                    time.sleep(5)

                    os.system('cls' if os.name == 'nt' else 'clear')

                    if score_self > score_opponent:
                        print(
                            f"\n🥇 CONGRATULATIONS, {player_self}! YOU ARE THE WINNER!")

                    elif score_self < score_opponent:
                        print(f"\n🥈 SORRY, {player_self}! YOU LOST THE GAME!")

                    else:
                        print(f"\n🃏 IT'S A TIE! THE GAME ENDS IN A DRAW!")

                    print(f"\n🌞 SELF TOTAL: {score_self} POINTS")
                    print(f"🌚 OPNT TOTAL: {score_opponent} POINTS")
                    print("\n⌚ RETURNING TO LOBBY\n")

                else:
                    print("\n⌚ NEXT ROUND STARTS IN 5 SECONDS\n")
                    time.sleep(5)
            break

    # Initialize a 5x5 ocean board with animals types and chances
    def initialize_ocean_board(self):
        ocean_board = [[None] * 5 for _ in range(5)]

        for row in range(5):
            for col in range(5):
                # Generate a random number between 0 and 1
                chance = random.random()
                # Only one of the sea creatures will be selected for each square
                if chance <= 0.05:  # 5% chance to appear
                    ocean_board[row][col] = "SHARK"
                elif chance <= 0.15:  # 10% chance to appear
                    ocean_board[row][col] = "SQUID"
                elif chance <= 0.35:  # 20% chance to appear
                    ocean_board[row][col] = "LOBSTER"
                elif chance <= 0.65:  # 30% chance to appear
                    ocean_board[row][col] = "FISH"
                elif chance <= 1.0:  # 35% chance to appear
                    ocean_board[row][col] = "SHRIMP"
        return ocean_board

    # Get the player's move by row and column
    def get_player_move(self, ocean_board):
        while True:
            try:
                # Leave comand
                row_input = input(f"🪝  CHOOSE A ROW: ")
                if row_input.lower() == "x":
                    return "LEAVE"

                col_input = input(f"🪝  CHOOSE A COLUMN: ")
                if col_input.lower() == "x":
                    return "LEAVE"

                row = int(row_input) - 1
                col = int(col_input) - 1

                # Normal coordinate input
                if 0 <= row < 5 and 0 <= col < 5:
                    animal_type = ocean_board[row][col]
                    return animal_type

                else:
                    print("\n🚨 INVALID INPUT. CHOOSE A VALID ROW AND COLUMN\n")

            except ValueError:
                print("\n🚨 INVALID INPUT. ENTER A NUMBER\n")

    # Update scores based on animal type
    def count_points(self, animal_type):
        # 🦈 Shark worth 100 points
        if animal_type == "SHARK":
            points = 100
        # 🦑 Squid worth 80 points
        elif animal_type == "SQUID":
            points = 80
        # 🦞 Lobster worth 60 points
        elif animal_type == "LOBSTER":
            points = 60
        # 🐟 Fish worth 50 points
        elif animal_type == "FISH":
            points = 50
        # 🦐 Shrimp worth 30 points
        elif animal_type == "SHRIMP":
            points = 30
        return points

    # Display the ocean board empty
    def display_ocean_empty(self):
        print("\n🦩 CHOOSE A PLACE TO FISH:\n")
        print("  1  2  3  4  5")
        for row in range(5):
            print(f"{row + 1} ", end="")
            for col in range(5):
                print("🌊", end=" ")
            print("")
        print("")

    # Display the ocean board result
    def display_ocean_result(self, ocean_board):
        print("\n🌊 YOUR OCEAN LOOKED LIKE:\n")
        print("  1  2  3  4  5")
        for row in range(5):
            print(f"{row + 1} ", end="")
            for col in range(5):
                animal_type = ocean_board[row][col]
                print(self.get_animal_icon(animal_type), end=" ")
            print("")

    # Get the animal icon for display
    def get_animal_icon(self, animal_type):
        if animal_type == "SHARK":
            return "🦈"  # Shark icon
        elif animal_type == "SQUID":
            return "🦑"  # Squid icon
        elif animal_type == "LOBSTER":
            return "🦞"  # Lobster icon
        elif animal_type == "FISH":
            return "🐟"  # Fish icon
        elif animal_type == "SHRIMP":
            return "🦐"  # Shrimp icon
        else:
            return "❓"  # Unknown animal icon

    # SAI Timeout is 15 seconds, considering RTT and 1 second delay to guest send back
    # ACK or NEG, invite must be set back to expired in less than 14 seconds
    def set_invite_expired_online(self):
        time.sleep(13)
        self.invite_expired = True

    # Delay 2 seconds to leave current match + 1 second to ACK or NEG + 2 seconds user send response
    def set_invite_expired_playing(self):
        self.invite_time_left = 10
        for i in range(9, 0, -1):
            time.sleep(1)
            self.invite_time_left = i
        self.invite_expired = True

    # Thread to listen for invite notifications
    def listen_invite_notification(self):
        while self.running:
            try:
                # Lock to ensure that only one thread at a time executes
                with self.lock:
                    # Check available data for reading at socket
                    ready_to_read, _, _ = select.select(
                        [self.sock], [], [], 0.1)

                    if ready_to_read:
                        response = self.receive_response()
                        # Show notification at client
                        if "INVITED YOU TO JOIN A GAME" in response:  # Case user is online
                            os.system('cls' if os.name == 'nt' else 'clear')

                            print(f"📬 NEW NOTIFICATION:\n{response}")
                            print("PRESS ENTER TO CONTINUE")

                            # Save inviter username
                            parts = response.split()
                            self.inviter = parts[1]
                            self.notification = True  # Notification active
                            self.invite_expired = False  # Set invite as not expired

                            # Invitation timeout client side when self is online
                            timer_thread = threading.Thread(
                                target=self.set_invite_expired_online)
                            timer_thread.start()

                        if "INVITED YOU TO JOIN ANOTHER GAME" in response:  # Case user is playing
                            self.response_in_game = response  # Store SAI invite response
                            self.notification = True  # Notification active
                            self.invite_expired = False  # Set invite as not expired

                            # Invitation timeout client side when self is playing
                            timer_thread = threading.Thread(
                                target=self.set_invite_expired_playing)
                            timer_thread.start()

            except ConnectionError:
                print("\n🚨 SERVER DISCONNECTED. EXITING CLIENT")
                break

    # Close socket connection
    def close_connection(self):
        self.sock.close()
        print("\n🛑 CONNECTION TO SERVER CLOSED\n")

    def main(self):
        self.connect()  # Connect user to SAI server
        logged_in_username = None  # Logged username
        invite_checker = threading.Thread(
            target=self.listen_invite_notification, daemon=True)

        print("\n🎏 WELCOME TO FISHERMEN MASTERS\n")

        while True:
            # Playing user declines invitation
            if self.match_declined == True:
                # Used for reloading client lobby
                self.send_message("GAME_NEG")
                self.match_declined = False

            # Notifications options
            if (self.notification) and (self.invite_expired == False):
                # Only case ack or neg can be a valid option at input
                self.input_ack_neg = True
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"📦 SEND BACK ACK TO {self.inviter}:\n")
                print("[8] ACCEPT INVITATION")
                print("[9] DECLINE INVITATION")

            # Received an invitation but it has expired
            if (self.notification) and (self.invite_expired == True):
                print(f"📢 INVITATION FROM {self.inviter} EXPIRED\n")

                # Send anything back to SAI to reload client response receiver
                self.send_message("NOTHING")

                # User received a notification, did not answer and now is back available at lobby
                command = f"AVAILABLE {logged_in_username}"
                self.send_message(command)

                self.notification = False  # Remove notification
                self.input_ack_neg = False  # Remove ack and neg as valid option at input
                self.invite_expired = False  # Set invite as not expired

            # User not yet logged in, show welcome options
            if not logged_in_username:
                print("[1] REGISTER")
                print("[2] LOGIN")
                print("[3] EXIT CLIENT")

            # User logged in, show play options
            if logged_in_username and self.notification == False:
                print(f"🧿 YOUR LOBBY: {logged_in_username}\n")
                print("[4] LIST USERS ONLINE")
                print("[5] LIST USERS PLAYING")
                print("[6] PLAY FISHERMEN MASTERS")
                print("[7] LOGOUT")

            choice = input("\n📟 CHOOSE AN OPTION: ")

            # Register user
            if choice == "1" and not logged_in_username:
                os.system('cls' if os.name == 'nt' else 'clear')

                print("\n📓 USER REGISTRATION")
                username = input("ENTER YOUR USERNAME: ")
                password = input("ENTER YOUR PASSWORD: ")
                client.register_user(username, password)

            # Login
            elif choice == "2" and not logged_in_username:
                os.system('cls' if os.name == 'nt' else 'clear')

                print("\n🔒 USER LOGIN")
                username = input("USERNAME: ")
                password = input("PASSWORD: ")

                # Receives from login method username if logged in or none if failed
                logged_in_username = client.login_user(username, password)

                # When authenticated by SAI start thread to listen for invite notifications
                if logged_in_username:
                    invite_checker.start()

                    time.sleep(1)
                    os.system('cls' if os.name == 'nt' else 'clear')

            # Exit client
            elif choice == "3" and not logged_in_username:
                os.system('cls' if os.name == 'nt' else 'clear')

                print("\n🚩 EXITING CLIENT")
                break

            # Users ONLINE means they are not currently in a game and are available for a match
            # Users PLAYING means they are connected to an ongoing game but still can be invited to join a new match
            # Users PLAYING are not considered as ONLINE

            # List online users
            elif choice == "4" and logged_in_username and self.input_ack_neg == False:
                os.system('cls' if os.name == 'nt' else 'clear')

                print("\n🧭 LISTING USERS ONLINE")
                client.list_users_online(logged_in_username)

            # List playing users
            elif choice == "5" and logged_in_username and self.input_ack_neg == False:
                os.system('cls' if os.name == 'nt' else 'clear')

                print("\n🧭 LISTING USERS PLAYING")
                client.list_users_playing()

            # Initiate game
            elif choice == "6" and logged_in_username and self.input_ack_neg == False:
                os.system('cls' if os.name == 'nt' else 'clear')

                print("\n🏹 INITIATE GAME")

                player_opponent = input("\n🔍 CHALLENGE THE USER: ")
                client.initiate_game(logged_in_username, player_opponent)

            # Logout from server
            elif choice == "7" and logged_in_username and self.input_ack_neg == False:
                os.system('cls' if os.name == 'nt' else 'clear')

                print("\n🚀 LOGGING OUT")
                logged_in_username = None
                break

            # Game invite accepted
            elif choice == "8" and logged_in_username and self.notification == True and self.input_ack_neg == True and self.invite_expired == False:
                print("\n🟢 ACCEPTING\n")
                time.sleep(1)

                self.send_message("GAME_ACK")  # Send SAI game accept
                self.notification = False   # Remove notification
                self.input_ack_neg = False  # Remove ack and neg as valid option at input

                print(f"🍾 YOU ACCEPTED THE INVITATION\n")

                player_opponent = self.inviter  # Save opponent's namne
                self.inviter = None  # Set back the inviter's to none

                # Wait for SAI response about which socket to connect to
                response = self.receive_response()

                if "CONNECT TO PORT" in response:
                    parts = response.split()
                    port_host = int(parts[3])  # Get received port

                    # Create socket and connects to received address from SAI
                    game_socket_guest = socket.socket(
                        socket.AF_INET, socket.SOCK_STREAM)

                    try:
                        # Invitee connects to inviter
                        game_socket_guest.connect((self.host, port_host))
                        print(
                            f"🎉 CONNECTED TO {player_opponent}. STARTING GAME...\n")

                        # Connected start game
                        self.start_game(game_socket_guest,
                                        logged_in_username, player_opponent)

                        # Guest after match ends send to SAI game over command to set back status to online
                        command = f"GAME_OVER {logged_in_username}"
                        self.send_message(command)

                        game_socket_guest.close()  # Close socket

                    # Guest view, host had lost connection or left game
                    except Exception as e:
                        print("🚨 FAILED TO CONNECT TO HOST/n")

                        # Guest after match ends send to SAI game over command to set back status to online
                        command = f"GAME_OVER {logged_in_username}"
                        self.send_message(command)

                        # Show guest win message
                        os.system('cls' if os.name == 'nt' else 'clear')
                        print(
                            f"💨 OPNT: {player_opponent} HAS LEFT THE GAME, LEAVING MATCH\n")
                        print(
                            f"🥇 CONGRATULATIONS, {logged_in_username}! YOU ARE THE WINNER!\n")

                        print("⌚ RETURNING TO LOBBY\n")
                        time.sleep(1)

                        game_socket_guest.close()

                        # Send anything back to SAI to reload client response receiver
                        self.send_message("NOTHING")

            # Game invite declined
            elif choice == "9" and logged_in_username and self.notification == True and self.input_ack_neg == True and self.invite_expired == False:
                print("\n🔴 DECLINING\n")
                time.sleep(1)
                os.system('cls' if os.name == 'nt' else 'clear')

                self.send_message("GAME_NEG")
                self.notification = False  # Remove notification
                self.input_ack_neg = False  # Remove ack and neg as valid option at input

            # Invalid option
            else:
                os.system('cls' if os.name == 'nt' else 'clear')

                if self.input_ack_neg == False:
                    self.send_message("NOTHING")

                if self.invite_expired == False:
                    print("\n⛔ INVALID OPTION, CHOOSE A VALID ONE\n")

        self.running = False  # Sign thread to stop execution

        # Ensure program doesn't exit before thread finish
        if invite_checker.is_alive():
            invite_checker.join()

        client.close_connection()


if __name__ == "__main__":
    client = User_Client("127.0.0.1", 4000)
    client.main()
