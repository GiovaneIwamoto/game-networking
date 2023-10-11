from queue import Queue
import threading
import select
import socket
import os
import time
import sys


class User_Client:

    # Constructor method, creates socket
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lock = threading.Lock()
        self.running = True
        self.notification = False

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
        data = self.sock.recv(1024)  # Socket receive response from server
        return data.decode("utf-8")

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
        if response == "✅ LOGIN SUCCESSFUL\n":
            return username
        else:
            return None

    # Send list users online command
    def list_users_online(self, logged_in_username):
        command = f"LIST-USERS-ONLINE {logged_in_username}"
        self.send_message(command)

        response = self.receive_response()
        print(f"\n{response}")

    # def list_users_playing(self):
    #     command = "LIST-USER-PLAYING"
    #     self.send_message(command)
    #     response = self.receive_response()
    #     print(response)

    # Send initiate game command
    def initiate_game(self, host, guest):
        command = f"GAME_INI {host} {guest}"
        self.send_message(command)

        response = self.receive_response()
        print(f"\n{response}")

        if "INVITED" in response:
            print("⏰ WAITING FOR GUEST RESPONSE...\n")

            response_invite = self.receive_response()

            if "ACCEPTED" in response_invite:
                print(f"🍾 GUEST ACCEPTED GAME INVITATION. STARTING GAME...\n")

                # TODO: Implement logic to start the game here

            elif "DECLINED" in response_invite:
                print(f"🧹 GAME INVITATION DECLINED BY GUEST\n")

            elif "TIMEOUT" in response_invite:
                print(f"💤 GUEST SEEMS TO BE AFK\n")

            else:
                print("❓ UNEXPECTED RESPONSE FROM GUEST\n")

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

                        if "INVITED YOU TO JOIN A GAME" in response:
                            os.system('cls' if os.name == 'nt' else 'clear')

                            print(f"📬 NEW NOTIFICATION:\n{response}")
                            print("PRESS ENTER TO CONTINUE")

                            self.notification = True

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

        print("\n🤠 WELCOME TO TURFMASTERS 🏆 BETTING CHAMPIONS\n")

        while True:
            # Notifications options
            if self.notification:
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"📦 SEND BACK ACK:\n")
                print("[8] ACCEPT INVITATION")
                print("[9] DECLINE INVITATION")

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
                print("[6] PLAY TURFMASTERS")
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
                    invite_checker = threading.Thread(
                        target=self.listen_invite_notification, daemon=True)
                invite_checker.start()

            # Exit client
            elif choice == "3" and not logged_in_username:
                os.system('cls' if os.name == 'nt' else 'clear')

                print("\n🚩 EXITING CLIENT")
                break

            # List online users
            elif choice == "4" and logged_in_username:
                os.system('cls' if os.name == 'nt' else 'clear')

                print("\n🧭 LISTING USERS ONLINE")
                client.list_users_online(logged_in_username)

            # List playing users
            elif choice == "5" and logged_in_username:
                os.system('cls' if os.name == 'nt' else 'clear')

                print("\n🎮 LISTING USERS PLAYING")
                # client.list_users_playing()
                pass

            # Initiate game
            elif choice == "6" and logged_in_username:
                os.system('cls' if os.name == 'nt' else 'clear')

                print("\n🏹 INITIATE GAME")

                adversary_user = input("\n🔍 CHALLENGE THE USER: ")
                client.initiate_game(logged_in_username, adversary_user)

            # Logout from server
            elif choice == "7" and logged_in_username:
                os.system('cls' if os.name == 'nt' else 'clear')

                print("\n🚀 LOGGING OUT")
                logged_in_username = None
                break

            # Game invite accepted
            elif choice == "8" and logged_in_username:
                print("\n🟢 ACCEPTING")
                time.sleep(1)
                self.send_message("GAME_ACK")
                self.notification = False

            # Game invite declined
            elif choice == "9" and logged_in_username:
                print("\n🔴 DECLINING")
                time.sleep(1)
                self.send_message("GAME_NEG")
                self.notification = False

            # Invalid option
            else:
                os.system('cls' if os.name == 'nt' else 'clear')

                self.send_message("NOTHING")
                print("\n⛔ INVALID OPTION, CHOOSE A VALID ONE\n")

        self.running = False  # Sign thread to stop execution
        invite_checker.join()  # Ensure program doesn't exit before thread finish

        client.close_connection()


if __name__ == "__main__":
    client = User_Client("127.0.0.1", 4000)
    client.main()
