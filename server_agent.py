import json
from re import search
import time
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
import pandas as pd
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import re
import qrcode

logs = logging.getLogger('chatbot')
logs.setLevel(logging.DEBUG)

logsformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
logfile = logging.FileHandler('chatbot_server.log')
logfile.setFormatter(logsformat)

stream = logging.StreamHandler()
streamformat = logging.Formatter("%(levelname)s:%(module)s:%(message)s")
stream.setLevel(logging.DEBUG)
stream.setFormatter(streamformat)

logs.addHandler(logfile)
logs.addHandler(stream)

# Load the json file with the crendentials
f = open('credentials.json',)
data = json.load(f)

search_q = None
file_name = None
city = None
qr_url = None

class ReceiverAgent(Agent):
    class RecvBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=3600)
            if msg:
                logging.info("Message received with content: {}".format(msg.body))
            else:
                logging.info("Did not receive any message after 1 hour.")

    class ShowTimeBehav(OneShotBehaviour):
        async def run(self):
            current_time = datetime.now().strftime("%H:%M:%S %Z")
            result = f'My clock says it\'s {current_time}'
            msg = Message()
            msg.to = data['chatbot']['username']
            msg.set_metadata("performative", "inform")
            msg.body = result
            await self.send(msg)
            logging.info('Current time sent.')

    class PersonInfoBehav(OneShotBehaviour):
        async def run(self):
            global search_q
            msg = Message()
            msg.to = data['chatbot']['username']
            msg.set_metadata("performative", "inform")

            if not search_q:
                msg.body = 'No search name received.'
                await self.send(msg)
                logging.warning('No search parameter detected. Sent warning message.')
                self.kill()
                return
            
            url = 'https://wikipedia.org/wiki/' + search_q
            request_page = requests.get(url)
            html_soup = BeautifulSoup(request_page.content, 'html.parser')
            variable=html_soup.find('p', {'class': not "mw-empty-elt"})

            if 'Other reasons this message may be displayed' in variable.text:
                msg.body = 'No results found.'
                logging.warning('No results found.')
            elif 'may refer to:' in variable.text:
                msg.body = 'Multiple results found. Need search parameters to be more specific.'
                logging.warning('Multiple results found. Need search parameters to be more specific.')
            else:
                logging.info('Search result found correctly.')
                msg.body = variable.text

            await self.send(msg)
            search_q = None
            logging.info('Search result sent.')
            
    class CreateFileBehav(OneShotBehaviour):
        async def run(self):
            global file_name
            msg = Message()
            msg.to = data['chatbot']['username']

            if not search_q:
                msg.set_metadata("performative", "refuse")
                msg.body = 'No file name detected.'
                await self.send(msg)
                logging.warning('No file name detected. Sent warning message.')
                self.kill()
                return

            f = open(file_name, "x")
            f.close()

            msg.set_metadata("performative", "agree")
            msg.body = f'File {file_name} created.'
            await self.send(msg)
            
            logging.debug(f'File {file_name} created. Informed the client about it.')

            file_name = None

    class GenerateQR(OneShotBehaviour):
        async def run(self):
            global qr_url
            msg = Message()
            msg.to = data['chatbot']['username']
            msg.set_metadata("performative", "inform")

            if not qr_url:
                msg.set_metadata("performative", "refuse")
                msg.body = 'No URL detected.'
                await self.send(msg)
                logging.warning('No URL detected. Sent warning message.')
                self.kill()
                return

            qr = qrcode.QRCode(
                    version=1,
                    box_size=10,
                    border=5)
            qr.add_data(qr_url)
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            img.save('qr_img.png')
            with open('qr_img.png', 'rb') as qr_img:
                msg.body = qr_img.read()
            await self.send(msg)

            logging.info('QR Code generated and sent to client.')

    class GetWeatherBehav(OneShotBehaviour):
        async def run(self):
            global city
            msg = Message()
            msg.to = data['chatbot']['username']
            msg.set_metadata("performative", "inform")

            if not city:
                msg.set_metadata("performative", "refuse")
                msg.body = 'No city detected.'
                await self.send(msg)
                logging.warning('No city detected. Sent warning message.')
                self.kill()
                return
                

            openweather_api_url = "https://api.openweathermap.org/data/2.5/weather?"
            openweather_api_url += "q=" + city + "&appid=" + data["WEATHER_API_KEY"]
            response = requests.get(openweather_api_url)
            if response.status_code == 200:
                resp_data = response.json()
                main = resp_data['main']
                temperature = main['temp']
                humidity = main['humidity']
                report = resp_data['weather']
                msg.body = f'This is the weather data in {city}:\nTemperature: {round(temperature-273.15, 2)}ºC\nHumidity: {humidity}%\nWeather Report: {report[0]["description"]}'
                await self.send(msg)
                logging.info('Weather report retrieved and sent to client.')

            else:
                logging.error("Error retrieving weather data.")
        
            city = None
            
    class TerminateExecutionBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=3600)
            if msg:
                logging.info('Termination message received. Terminating...')
                await self.agent.stop()


    async def setup(self):
        b = self.RecvBehav()
        person_info_behav = self.PersonInfoBehav()
        terminate = self.TerminateExecutionBehav()
        get_weather = self.GenerateQR()

        terminate_template = Template()
        terminate_template.set_metadata("performative", "inform")
        terminate_template.body = "exit"

        # Msg Template
        template = Template()
        template.set_metadata("performative", "inform")

        # Adding the Behaviour with the template will filter all the msg
        # self.add_behaviour(b, template)
        self.add_behaviour(terminate, terminate_template)
        self.add_behaviour(get_weather)

        logging.info("Agent setup completed.")


def main():
    logging.info("Creating Agent ... ")
    agent = ReceiverAgent(data['chatbot']['username'],
                            data['chatbot']['password'])
    future = agent.start()
    future.result()
    logging.info("Agent created succesfully.")

    while agent.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            agent.stop()
            break
    logging.info("Agent finished.")

if __name__ == "__main__":
    main()