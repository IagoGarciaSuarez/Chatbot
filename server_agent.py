import json
import time
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
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

# stream = logging.StreamHandler()
# streamformat = logging.Formatter("%(levelname)s:%(module)s:%(message)s")
# stream.setLevel(logging.DEBUG)
# stream.setFormatter(streamformat)

logs.addHandler(logfile)
# logs.addHandler(stream)

f = open('credentials.json',)
data = json.load(f)

search_q = None
file_name = None
city = None
qr_url = None

show_time_behav = None
person_info_behav = None
create_file_behav = None
generate_qr_behav = None
weather_behav = None

class ReceiverAgent(Agent):
    async def setup(self):
        terminate_template = Template()
        terminate_template.set_metadata("performative", "inform")
        terminate_template.body = "exit"

        template = Template()
        template.set_metadata("performative", "request")

        self.add_behaviour(TerminateExecutionBehav(), terminate_template)
        self.add_behaviour(RecvBehav(), template)

        logs.info("Agent setup completed.")

class RecvBehav(CyclicBehaviour):
    async def run(self):
        global search_q
        global city
        global qr_url
        global file_name
        logs.info("Waiting for commands...")

        msg = await self.receive(timeout=3600)

        if msg:
            if re.search('qr', msg.body, re.IGNORECASE):
                logs.info(
                    f"Message received with content: '{msg.body}'. Running QR Generator behaviour.")
                url_regexp = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
                qr_url_search = re.search(url_regexp, msg.body)
                if qr_url_search:
                    qr_url = qr_url_search.group()
                self.agent.add_behaviour(GenerateQR())

            elif re.search('weather', msg.body, re.IGNORECASE):
                logs.info(
                    f"Message received with content: '{msg.body}'. " +
                    "Running Weather Report behaviour.")
                city_regexp = re.findall(r'([A-Z][a-z]+)', msg.body)
                if city_regexp:
                    city = " ".join(city_regexp)                
                self.agent.add_behaviour(GetWeatherBehav())

            elif re.search('create', msg.body, re.IGNORECASE) and re.search('file', msg.body, re.IGNORECASE):
                logs.info(
                    f"Message received with content: '{msg.body}'. " +
                    "Running Create File behaviour.")
                file_name_search = re.search(r'(\w+[.]\w+)', msg.body)
                if file_name_search:
                    file_name = file_name_search.group()
                self.agent.add_behaviour(CreateFileBehav())

            elif re.search('wikipedia', msg.body, re.IGNORECASE):
                logs.info(
                    f"Message received with content: '{msg.body}'. Running Person Info search.")
                person_name = re.findall(r'([A-Z][a-z]+)', msg.body)
                if person_name:
                    search_q = " ".join(person_name)    
                self.agent.add_behaviour(PersonInfoBehav())           
            
            elif re.search(r'time|clock', msg.body, re.IGNORECASE):
                logs.info(
                    f"Message received with content: '{msg.body}'. Running Show Time behaviour.")
                self.agent.add_behaviour(ShowTimeBehav())
            
            else:
                logs.info(f'No function recognized in the command \'{msg.body}\'.')
                msg_resp = Message(to=data['chatbot_client']['username'])
                msg_resp.set_metadata("performative", "not-understood")
                msg_resp.set_metadata("protocol", "fipa-request-protocol")
                msg_resp.body = 'No function recognized in the command'
                
                await self.send(msg_resp)
        else:
            logs.info("Did not receive any message after 1 hour.")

class ShowTimeBehav(OneShotBehaviour):
    async def run(self):
        current_time = datetime.now().strftime("%H:%M:%S %Z")
        result = f'My clock says it\'s {current_time}'
        msg = Message(to=data['chatbot_client']['username'])
        msg.set_metadata("performative", "inform")
        msg.set_metadata("protocol", "fipa-request-protocol")
        msg.body = result
        await self.send(msg)
        logs.info('Current time sent.')

class PersonInfoBehav(OneShotBehaviour):
    async def run(self):
        global search_q
        msg = Message(to=data['chatbot_client']['username'])
        msg.set_metadata("performative", "inform")
        msg.set_metadata("protocol", "fipa-request-protocol")

        if not search_q:
            msg.set_metadata("performative", "refuse")
            msg.body = 'No search name received.'
            await self.send(msg)
            logs.warning('No search parameter detected. Sent warning message.')
            self.kill()
            return
        
        try:
            url = 'https://wikipedia.org/wiki/' + search_q
            request_page = requests.get(url)
            html_soup = BeautifulSoup(request_page.content, 'html.parser')
            variable=html_soup.find('p', {'class': not "mw-empty-elt"})

            if 'Other reasons this message may be displayed' in variable.text:
                msg.body = 'No results found.'
                logs.warning('No results found.')
            elif 'may refer to:' in variable.text:
                msg.body = 'Multiple results found. Need search parameters to be more specific.'
                logs.warning('Multiple results found. Need search parameters to be more specific.')
            else:
                logs.info('Search result found correctly.')
                msg.body = variable.text

        except:
            logs.error("An unexpected error ocurred while performing the search.")
            msg.set_metadata("performative", "failure")
            msg.body = "An unexpected error ocurred while performing the search."
            await self.send(msg)
            self.kill()
            return

        await self.send(msg)

        search_q = None
        logs.info('Search result sent.')
        
class CreateFileBehav(OneShotBehaviour):
    async def run(self):
        global file_name
        msg = Message(to=data['chatbot_client']['username'])
        msg.set_metadata("performative", "agree")
        msg.set_metadata("protocol", "fipa-request-protocol")

        if not file_name:
            msg.set_metadata("performative", "refuse")
            msg.body = 'No file name detected.'
            await self.send(msg)
            logs.warning('No file name detected. Sent warning message.')
            self.kill()
            return
        try:
            f = open(file_name, "x")
            f.close()

        except FileExistsError:
            logs.error("File creation attempted but a file with that name already exists.")
            msg.set_metadata("performative", "refuse")
            msg.body = "A file with that name already exists."
            await self.send(msg)
            self.kill()
            return

        except:
            logs.error("An unexpected error ocurred while creating the file.")
            msg.set_metadata("performative", "failure")
            msg.body = "An unexpected error ocurred while creating the file."
            await self.send(msg)
            self.kill()
            return
            

        msg.body = f'File {file_name} created.'
        await self.send(msg)
        
        logs.info(f'File {file_name} created. Informed the client about it.')
        file_name = None

class GenerateQR(OneShotBehaviour):
    async def run(self):
        global qr_url
        msg = Message(to=data['chatbot_client']['username'])
        msg.set_metadata("performative", "inform")
        msg.set_metadata("protocol", "qr_gen")

        if not qr_url:
            msg.set_metadata("performative", "refuse")
            msg.set_metadata("protocol", "fipa-request-protocol")
            msg.body = 'No URL detected.'
            await self.send(msg)
            logs.warning('No URL detected. Sent warning message.')
            self.kill()
            return
        try: 
            qr = qrcode.QRCode(
                    version=1,
                    box_size=10,
                    border=5)
            qr.add_data(qr_url)
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            img.save('qr_img.png')

            with open('qr_img.png', 'rb') as qr_img:
                msg.body = qr_img.name
                qr_img.close()
        except:
            logs.error("An unexpected error ocurred while generating QR Code.")
            msg.set_metadata("performative", "failure")
            msg.set_metadata("protocol", "fipa-request-protocol")
            msg.body = "An unexpected error ocurred while generating QR Code."
            await self.send(msg)
            self.kill()
            return


        await self.send(msg)

        logs.info('QR Code generated and sent to client.')
        qr_url = None

class GetWeatherBehav(OneShotBehaviour):
    async def run(self):
        global city
        msg = Message()
        msg.to = data['chatbot_client']['username']
        msg.set_metadata("performative", "inform")
        msg.set_metadata("protocol", "fipa-request-protocol")

        if not city:
            msg.set_metadata("performative", "refuse")
            msg.body = 'No city detected.'
            await self.send(msg)
            logs.warning('No city detected. Sent warning message.')
            self.kill()
            return
            

        openweather_api_url = "https://api.openweathermap.org/data/2.5/weather?"
        openweather_api_url += "q=" + city + "&appid=" + data["WEATHER_API_KEY"]
        try:
            response = requests.get(openweather_api_url)
            if response.status_code == 200:
                resp_data = response.json()
                main = resp_data['main']
                temperature = main['temp']
                humidity = main['humidity']
                report = resp_data['weather']
                msg.body = f'This is the weather data in {city}:\nTemperature: {round(temperature-273.15, 2)}ºC\nHumidity: {humidity}%\nWeather Report: {report[0]["description"]}'

            else:
                logs.error("Response code different to 200.")
                msg.body(f"Couldn't retrieve weather report for {city}.")
                msg.set_metadata("performative", "failure")
        except:
            logs.error("An unexpected error ocurred while retrieving weather data.")
            msg.set_metadata("performative", "failure")
            msg.body = "An unexpected error ocurred while retrieving weather data."
            await self.send(msg)
            self.kill()
            return

        await self.send(msg)
        city = None

        logs.info('Weather report retrieved and sent to client.')
        
class TerminateExecutionBehav(CyclicBehaviour):
    async def run(self):
        msg = await self.receive(timeout=3600)
        if msg:
            logs.info('Termination message received. Terminating...')
            await self.agent.stop()

def main():
    logs.info("Creating Agent ... ")
    agent = ReceiverAgent(data['chatbot_server']['username'],
                            data['chatbot_server']['password'])
    future = agent.start()
    future.result()
    logs.info("Agent created succesfully.")

    while agent.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            agent.stop()
            break
    logs.info("Agent finished.")

if __name__ == "__main__":
    main()