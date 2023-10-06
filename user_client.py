import socket


class User_Client:

    # Constructor method, creates socket
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connection to server
    def connect(self):
        self.sock.connect((self.host, self.port))
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
        print("")
        print(response)

    def login_user(self, username, password):
        command = f"LOGIN {username} {password}"
        self.send_message(command)
        response = self.receive_response()
        print(response)

    def list_users_online(self):
        command = "LIST-USER-ON-LINE"
        self.send_message(command)
        response = self.receive_response()
        print(response)

    def list_users_playing(self):
        command = "LIST-USER-PLAYING"
        self.send_message(command)
        response = self.receive_response()
        print(response)

    def initiate_game(self, player1, player2):
        command = f"GAME_INI {player1} {player2}"
        self.send_message(command)
        response = self.receive_response()
        print(response)

    def close_connection(self):
        self.sock.close()
        print("Connection closed.")


def main():
    # Connect user to SAI server
    client = User_Client("127.0.0.1", 4000)
    client.connect()

    # User welcome options
    print("\n🤠 WELCOME TO TURFMASTERS 🏆 BETTING CHAMPIONS\n")
    print("[1] REGISTER")
    print("[2] LOGIN")

    choice = input("\n📌 CHOOSE AN OPTION: ")

    # Register user
    if choice == "1":
        username = input("\nEnter your username: ")
        password = input("Enter your password: ")
        client.register_user(username, password)

    # Login
    elif choice == "2":
        username = input("\nEnter your username: ")
        password = input("Enter your password: ")
        client.login_user(username, password)

    # Invalid option
    else:
        print("\n⛔ INVALID OPTION")

    client.close_connection()


if __name__ == "__main__":
    main()
