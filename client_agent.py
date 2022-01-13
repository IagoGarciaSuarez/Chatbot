import json
import time
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from spade.template import Template
import pandas as pd

# Load the json file with the crendentials
f = open('credentials.json',)
data = json.load(f)

class SenderAgent(Agent):
    class InformBehav(OneShotBehaviour):
        async def run(self):

            # Message
            print("InformBehav running")
            msg = Message(to=data['spade_intro']['username'])     # Instantiate the message
            msg.set_metadata("performative", "inform")     # Set the "inform" FIPA performative
            msg.body = "Hi there!"                         # Set the message content

            #More metadata can be added
            #msg.set_metadata("ontology", "myOntology")
            #msg.set_metadata("language", "OWL-S")

            await self.send(msg)
            print("Message sent!")

            # stop agent from behaviour
            await self.agent.stop()

    async def setup(self):
        print("Agent "+str(self.jid)+ " started")
        b = self.InformBehav()
        self.add_behaviour(b)

def main():
    
    # Create the agent
    print("Creating Agents ... ")
    # receiveragent = ReceiverAgent(data['spade_intro']['username'], 
    #                         data['spade_intro']['password'])
    # future = receiveragent.start()
    # future.result()
    senderagent = SenderAgent(data['spade_intro_2']['username'], 
                            data['spade_intro_2']['password'])
    senderagent.start()
    
    while 1:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            senderagent.stop()
            # receiveragent.stop()
            break
    print("Agents finished")

if __name__ == "__main__":
    main()