# GAME NETWORKING

### **OVERVIEW**

Hybrid peer-to-peer application to represent an online gaming network, consisting of a server and multiple players. The interaction between the server and users follows a client-server style, while the interaction between players is peer-to-peer. SAI Server is responsible for managing data related to connections made between clients. For this purpose, it has been defined to store hosts, ports, online users, and users who are currently playing. With this data being stored by SAI, the application have all the necessary information to enable the hybrid peer-to-peer functionality. It does not interfere in the connection between clients once it has been established; at that point, all logic is at the discretion of the clients.

[![Icons](https://skillicons.dev/icons?i=py,powershell,vscode&theme=dark)](https://skillicons.dev)

> [!TIP]
> The complete game documentation including game interactions explanations and protocols can be found in the doc file available in Portuguese PT-BR.

---

### **GAME PREVIEW**

Each player has 25 choices to make, where in each round, each player must submit their choice through a valid row and column. When both players send their responses, all the animals at each coordinate in the ocean will be revealed, along with what each player caught by choosing a position. Based on the caught animal, points are assigned to the total score.

> [!IMPORTANT]
> Each animal has a predetermined score and a rarity of being generated at each ocean coordinate. The player's total score is the sum of the value of each caught animal throughout the 5 rounds. After the five rounds, the game displays the match information, and the peer-to-peer connection between the players is terminated, returning to the main menu.

---

### **HOW TO RUN**

It is important to note that the interface relies heavily on the emojis present in your operating system and the shell itself for a better experience. We recommend using terminals that support these types of characters, such as VSCode's terminal. The project is built in Python and is easily executable. First, you need to run the SAI Server in the terminal using the following command:

```ruby
$ python sai_server.py
```

Now you can run the clients. In a new terminal, execute the following script located in the root of the project. You can run it in multiple different terminals, each representing a possible connection:

```ruby
$ python user_client.py
```

To clean the database and the game.log file, if necessary, you can use the following script:

```ruby
$ python clean_script.py
```

---

### **AUTHOR**

- Giovane Hashinokuti Iwamoto - Computer Science student at UFMS - Brazil - MS
- Paulo Henrique Mendonça Leite - Computer Science student at UFMS - Brazil - MS

I am always open to receiving constructive criticism and suggestions for improvement in my developed code. I believe that feedback is an essential part of the learning and growth process, and I am eager to learn from others and make my code the best it can be. Whether it's a minor tweak or a major overhaul, I am willing to consider all suggestions and implement the changes that will benefit my code and its users.
