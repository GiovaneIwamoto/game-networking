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
        print(response)

    # TODO:
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


client = User_Client("127.0.0.1", 4000)
client.connect()

# Testing
client.register_user("Alice", "pass123")

# client.close_connection()
