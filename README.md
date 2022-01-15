# ChatBot MultiAgents Systems
Repository dedicated to the chatbot made for Multiagents Sistems practice in 2021.

## Protocols used:
Each protocol used will be explained in detail in the PDF Memoria.pdf

fipa-request-protocol -> From FIPA standards (http://www.fipa.org/repository/ips.php3)

qr_gen : Used in the QR Generation behaviour to create a QR Code and let the client know that it needs to copy de file.

## Regular Expressions used to recognize commands:
- QRGenerator: If 'qr' is in the message received, executes the QR Generation behaviour with the first URL found in the message.

- Weather: If 'weather' is in the messagae received, executes the Weather Report behaviour using as city all the words capitalized joined with a space in between.

- Create File: If the words 'create' and 'file', non-ordered, are found in the message, executes the Create File behaviour using as name the first file name found in the message, this means, the first word with a '.' between two strings.

- Wikipedia: If 'wikipedia' is found in the command, join all the capitalized words separated by a space as one unique name and retrieves information scrapping the search result in wikipedia.

- Show Time: If none of the above rules are met and the word 'time' is in the message, returns the current time for the server agent system.