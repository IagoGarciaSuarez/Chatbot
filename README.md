# chatbot_SMA
Repository dedicated to the chatbot made for Multiagents Sistems practice in 2021.


protocols:
from fipa -> http://www.fipa.org/repository/ips.php3
qr_gen : protocolo para la funcion de generacion de qr, el cliente debe copiar el archivo cuando recibe un msg con este protocolo.
fipa-request-protocol : protocolo base para la comunicación donde el cliente da una orden y el servidor contesta con el resultado. El cliente solo muestra ese resultado.

RegExp para reconocer comandos:
- QRGenerator: Si hay 'qr' en el comando, ejecuta el comportamiento buscando la primera url que haya.
- Weather: Si tiene la palabra 'weather' en el comando, ejecuta el comportamiento buscando las palabras con primera letra mayúscula que encuentre y las une como una ciudad.
- Create: Si las palabras 'file' y 'create' están en el comando. Para determinar el nombre del archivo se obtiene la primera ocurrencia de un nombre, un punto, y una extensión.
- Wikipedia: si la palabra 'wikipedia' está en el comando, busca las palabras con primera letra en mayúscula y las une separadas por un espacio para dar el nombre de la búsqueda.
- Show Time: si el comando tiene la palabra 'time' y ninguna de las anteriores mencionadas.