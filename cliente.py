#!/usr/bin/env python3


from random import shuffle
import pyaudio, wave, socket,time
from pathlib import Path

HOST = "192.168.0.5"  # The server's hostname or IP address
PORT = 65432  # The port used by the server
buffer_size = 1024

################################################################
# Nombres de los personajes en ingles para que sea facil reconocerlos
personajes = ['batman', 'superman', 'wonder woman', 'flash', 'green lantern', 'lex luthor', 'catwoman', 'joker',
              'harley quinn', 'poison ivy']
# Caracteristicas de cada personaje
personajesC = [  # Arreglo bidimiensional
    ["héroe", "rico", "capa", "negro", "sabe pelear", "hombre", "cabello corto", "inteligente", "batman"],
    ["héroe", "vuela", "super fuerza", "visión láser", "hombre", "capa", "cabello corto", "veloz","superman"],
    ["héroe", "vuela", "mujer", "cabello largo",  "super fuerza", "lazo","sabe pelear","wonder womam"],
    ["héroe", "veloz", "hombre","sabe pelear", "rojo", "ágil", "cabello corto",  "flash"],
    ["héroe", "super fuerza", "verde", "vuela", "hombre", "cabello corto", "green lantern"],
    ["villano", "rico", "hombre", "inteligente", "calvo", "verde","lex luthor"],
    ["villano", "mujer", "negro", "sabe pelear", "cabello corto", "ágil",  "catwoman"],
    ["villano", "hombre", "inteligente", "cabello corto","payaso", "joker"],
    ["villano", "mujer", "cabello largo",  "sabe pelear", "payaso", "ágil", "harley quinn"],
    ["villano", "mujer", "cabello largo", "ágil", "verde", "poison ivy"]
]


#######################################################################
def verPersonajes():
    global personajes, personajesC
    print("******PERSONAJES******")
    for i in range(0, len(personajes)):
        print("{}:\t{}".format(personajes[i], personajesC[i]))
    print("**********************")


def ocultarPersonajes(preg, resp):
    global personajesC, personajes

    if resp == "Si":
        for x in range(len(personajesC)):
            cont = 0
            for y in range(len(personajesC[x])):
                if (personajesC[x][y]) in preg:  # Si la característica está, se salta al siguiente personaje
                    break
                else:  # En caso de que no tenga es característica, el personaje se oculta
                    cont += 1
            if cont == len(personajesC[
                               x]):  # Cuando se confirma que no se trata de un personaje, su nombre y características se ocultan
                personajesC[x] = "-"
                personajes[x] = "-"
    if resp == "No":
        for x in range(len(personajesC)):
            cont = 0
            for y in range(len(personajesC[x])):
                if (personajesC[x][y]) in preg:  # Si está la característica, oculta al siguiente personaje
                    personajesC[x] = "-"
                    personajes[x] = "-"
                    break # y pasa al siguiente
    verPersonajes()


def GrabarPregunta():
    chunk = 1024
    sample_format = pyaudio.paInt16
    channels = 2
    fs = 44100
    seconds = 3
    filename = "audio.wav"

    p = pyaudio.PyAudio()

    print('Grabando')
    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=fs,
                    frames_per_buffer=chunk,
                    input=True)
    frames = []
    for i in range(0, int(fs / chunk * seconds)):
        data = stream.read(chunk)
        frames.append(data)

    stream.stop_stream()
    stream.close()

    p.terminate()

    print('Terminando de grabar')

    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(fs)
    wf.writeframes(b''.join(frames))
    wf.close()


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as TCPClientSocket:
    TCPClientSocket.connect((HOST, PORT))
    TCPClientSocket.sendall(b" ")
    data = TCPClientSocket.recv(buffer_size)
    Jugador = data.decode()
    if (data.decode() == "JH"):  # Código para jugador host
        numPlay = input("Ingrese el número de jugadores: \n")
        TCPClientSocket.sendall(numPlay.encode())
        data = TCPClientSocket.recv(buffer_size)  # Manda al servidor el número de jugadores

        TCPClientSocket.sendall(b" ")
        print("Esperando a otros jugadores...")
        data = TCPClientSocket.recv(
            buffer_size)  # Espera a que el servidor mande algo para que sepa que ya se ha cumplido la barrera
        TCPClientSocket.sendall(b" ")

    if (data.decode() == "ETC"):  # Código para otros jugadores
        print("Esperando a otros jugadores...")
        TCPClientSocket.sendall(b" ")
        data = TCPClientSocket.recv(buffer_size)
        TCPClientSocket.sendall(
            b" ")  # Prácticamente solo sincroniza los enviar y recibir, si no luego hace cosas raras xD

        time.sleep(1)
    print("=======ADIVINA QUIÉN???=======\n")
    while True:
        termina=False
        print("Espere su turno: ")
        data = TCPClientSocket.recv(buffer_size)
        if data.decode().startswith("Fin"): #Significa que ya hay un ganador
            print(data.decode()) #Imprimir mensaje del jugador ganador
            break
        verPersonajes()
        # TCPClientSocket.sendall(coord.encode())
        ##########################################
        while True:
            print("Debe decir una frase como 'El personaje vuela', 'El personaje es hombre',etc...")
            coord = input("Pulse enter para grabar ")
            GrabarPregunta()
            TamAud = Path("audio.wav").stat().st_size
            # print(str(TamAud))
            TCPClientSocket.sendall(str(TamAud).encode())
            with open("audio.wav", 'rb') as f:
                for l in f:
                    TCPClientSocket.sendall(l)
            print("Terminando de enviar archivo")
            respuesta = TCPClientSocket.recv(buffer_size)
            if respuesta.decode() != '*':
                if respuesta.decode().startswith("¡¡Felicidades"):
                    print(respuesta.decode())
                    print("Fin de la partida")
                    termina=True
                    break
                else:
                    print(respuesta.decode())
                    ocultarPersonajes(respuesta[14:-6].decode(), (respuesta[-2:].decode()))
                    break
            else:
                print("No pude capturar nada. Que fue lo que dijiste?\n")
            if termina:
                break
        if termina:
            break

                
           
