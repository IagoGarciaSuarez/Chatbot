import json
import time
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
import logging
import shutil

logs = logging.getLogger('chatbot')
logs.setLevel(logging.DEBUG)

logsformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
logfile = logging.FileHandler('chatbot_client.log')
logfile.setFormatter(logsformat)

stream = logging.StreamHandler()
streamformat = logging.Formatter("%(levelname)s:%(module)s:%(message)s")
stream.setLevel(logging.WARNING)
stream.setFormatter(streamformat)

logs.addHandler(logfile)
logs.addHandler(stream)

# Load the json file with the crendentials
f = open('credentials.json',)
data = json.load(f)

help = """
Hi! I can do some work for you, here is my list of functionalities:
- Show my current time.
- Show info about a person you ask for.
- Create a file in my system with the name you wish, needing to specify the extension.
- Generate a QR code for any URL you want.
- Show the weather report for any city you want.
- Terminate my execution if you type 'exit'.

Except for this help command and the termination one, I don't have predefined commands.
You just need to speak to me and ask me for what you need, I'll try my best!

"""

executing = True

class SenderAgent(Agent):
    async def setup(self):
        logs.info("Agent "+str(self.jid)+ " started")
        print(
            'Welcome to this ChatBot. You can speak to me normally, ' + 
            'no predefined commands... Except if you need help, then just type "help".')
        self.add_behaviour(InformBehav())

class InformBehav(CyclicBehaviour):
    async def run(self):
        command = input('> ')
        msg = Message(to=data['chatbot_server']['username'])
        msg.set_metadata("performative", "request")

        if command == "help":
            logs.info("Displaying help information.")
            print(help)
        
        elif command == "exit":
            self.agent.add_behaviour(TerminateExecutionBehav())
            self.kill()

        else:  
            msg.body = command

            await self.send(msg)
            logs.info(f'Command \'{command}\' sent. Waiting for reply...')

            msg = await self.receive(timeout=10)
            if msg:
                logs.info(f"Received message with protocol '{msg.metadata['protocol']}'.")
                if msg.metadata["protocol"] == "qr_gen":
                    shutil.copyfile(msg.body, './qr_client.png')
                    print("Here you have your QR Code! You can check my root directory to find it.")
                else:
                    logs.info("Response received.")
                    print(msg.body)
            else:
                logs.warning('No reply received.')
                print("No reply received, maybe the server agent is not available.")

class TerminateExecutionBehav(OneShotBehaviour):
    async def run(self):
        global executing
        msg = Message(to=data['chatbot_server']['username'])
        msg.set_metadata("performative", "inform")            
        msg.set_metadata("protocol", "termination")            
        msg.body = 'exit'
        await self.send(msg)

        logs.info("Terminating execution...")
        await self.agent.stop()
        executing = False
        logs.info("Agent finished execution.")

def main():
    print("Waking up...")
    logs.info("Starting boot for the client agent.")

    senderagent = SenderAgent(data['chatbot_client']['username'], 
                            data['chatbot_client']['password'])
    senderagent.start()
    
    while executing:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            senderagent.add_behaviour(TerminateExecutionBehav())
            break
    
    print("Thank you for the chat, see you soon!")
    

if __name__ == "__main__":
    main()