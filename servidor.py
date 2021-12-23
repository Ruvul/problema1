# !/usr/bin/env python3

import socket,time
from random import randint
import threading
from time import time
import select
import speech_recognition as sr

host="192.168.0.5"
port=65432
numConn=3
buffer_size = 1024
personaje=""
personajeC=""
r = sr.Recognizer()
################################################################
#Nombres de los personajes en ingles para que sea facil reconocerlos
personajes=['batman', 'superman', 'wonder woman', 'flash', 'green lantern', 'lex luthor', 'catwoman', 'joker', 'harley quinn', 'poison ivy']
#Caracteristicas de cada personaje
personajesC= [ # Arreglo bidimiensional
    ["héroe", "rico", "capa", "negro", "sabe pelear", "hombre", "cabello corto", "inteligente", "batman"],
    ["héroe", "vuela", "super fuerza", "visión láser", "hombre", "capa", "cabello corto", "veloz","superman"],
    ["héroe", "vuela", "mujer", "cabello largo",  "super fuerza", "lazo","sabe pelear","wonder womam"],
    ["héroe", "veloz", "hombre","sabe pelear", "rojo", "ágil", "cabello corto",  "flash"],
    ["héroe", "super fuerza", "verde", "vuela", "hombre", "cabello corto", "green lantern"],
    ["villano", "rico", "hombre", "inteligente", "calvo", "verde","lex luthor"],
    ["villano", "mujer", "negro", "sabe pelear", "cabello corto", "ágil",  "catwoman"],
    ["villano", "hombre", "inteligente", "payaso","cabello corto", "joker"],
    ["villano", "mujer", "cabello largo",  "sabe pelear", "payaso", "ágil", "harley quinn"],
    ["villano", "mujer", "cabello largo", "ágil", "verde", "poison ivy"]
]

#######################################################################
global NumPlayers #Es una variable global que servira de referencia a todos los clientes que se generarán
NumPlayers = 0
eleccion = randint(0, len(personajes) - 1)

personaje = personajes[eleccion]
personajeC = personajesC[eleccion]
ganador=""
 #Contiene la ip del usuario ganador

def empty_socket(sock):
    """remove the data present on the socket"""
    input = [sock]
    while 1:
        inputready, o, e = select.select(input,[],[], 0.0)
        if len(inputready)==0: break
        for s in inputready: s.recv(1)

def servirPorSiempre(socketTcp, listaconexiones):
    global NumPlayers
    condition = threading.Condition() #Este condicional nos sirve para notificar al jugador host que la barrera ha sido cumplida y se puede proceder con el juego
    condSem = threading.Condition() #Este nos sirve para notificar al planificador de turnos que el jugador a termindao su turno y que puede proceder con el proximo
    listaSemaforos=[] #Se crea esta lista de semaforos para tener un control de cada jugador, a cada jugador se le pone un semaforo
    try:
        client_conn, client_addr = socketTcp.accept()
        print("Conectado a", client_addr)
        semaforoH = threading.Semaphore(0) #Semaforo del host
        listaSemaforos.append(semaforoH) #Se agrega el semaforo a la lista de semaforos
        listaconexiones.append(client_conn)
        thread_read = threading.Thread(target=recibir_datos_host, args=[client_conn, client_addr,listaconexiones,condition,semaforoH,listaSemaforos,condSem])
        thread_read.start() #Se inicia el hilo del jugador host para pedir el numero de jugadores
        gestion_conexiones(listaConexiones)
        with condition: 
            condition.wait() #Espera a que el host notifique que ya obtuvo el numero de jugadores 
        barrier = threading.Barrier(NumPlayers-1) #Se crea la barrera
        while True:

            client_conn, client_addr = socketTcp.accept() #Comienza a aceptar las conexiones de los demás jugadores
            print("Conectado a", client_addr)
            semaforoJ = threading.Semaphore(0) #Crea el semaforo de cado jugador
            listaSemaforos.append(semaforoJ)    #se agrega a la lista de semaforos
            listaconexiones.append(client_conn)
            thread_read = threading.Thread(target=recibir_datos, args=[client_conn, client_addr,listaconexiones,barrier,condition,semaforoJ,listaSemaforos,condSem])
            thread_read.start()
            gestion_conexiones(listaConexiones)
            if(len(listaConexiones) >= NumPlayers): #Se verifica que ya no se acepten más conexiones de otros jugadores
                break
        print("SALIENDO DE SERVIR POR SIEMPRE")
        #COMENZAR PLANIFICACION DE TURNOS
        #Cuando estan todos los jugadores, se elige un personaje al azar junto con sus caracteristicas
        print("\nElegi al personaje {} con caracteristicas({})\n".format(personaje,personajeC))
        while True: #Bucle infinito, se   recorre la lista de semaforos infinitamente
            for sem in listaSemaforos:
                sem.release() #Se liberan los semaforos en la lista uno por uno, el primero es el del host
                with condSem:
                    condSem.wait() #Se espera hasta que el jugador diga notifique que acabo
        
    except Exception as e:
        print(e)

def gestion_conexiones(listaconexiones):
    for conn in listaconexiones:
        if conn.fileno() == -1:
            listaconexiones.remove(conn)
    print("\nhilos activos:{}\n".format(threading.active_count()))
    #print("enum", threading.enumerate())
    #print("conexiones: ", len(listaconexiones))
    #print(listaconexiones)

def validarPregunta(cadena,listaConexiones,Client_conn,Client_addr):
    global ganador,personaje
    cadena=cadena.lower()
    cont = 0
    for i in personajeC:
        cont+=1
        if(cadena.find(i)!=-1): #Si encuentra alguna característica en la cadena del usuario, entonces la respuesta será si
            mensaje="Jugador dijo: "+cadena+"?\nR:Si"
            print(mensaje)
            if personaje in cadena:
                ganador=Client_addr
                mensaje="¡¡Felicidades, ganaste Jugador {}!!\nEl personaje es {}\n".format(ganador,personaje)
                Client_conn.sendall(mensaje.encode())
            else:
                Client_conn.sendall(mensaje.encode())
            break
        elif cont==len(personajeC): # de lo contrario será no
            mensaje ="Jugador dijo: "+ cadena + "?\nR:No"
            print(mensaje)
            Client_conn.sendall(mensaje.encode())
            break

def recibirPregunta(Client_conn):
    data = Client_conn.recv(buffer_size) #Recibe mensaje que envia el cliente
    tamAud=int(data.decode())
    #print(tamAud)
    i=0
    with open("Raudio.wav", 'wb') as f:
        while i<tamAud:
            l = Client_conn.recv(buffer_size)
            f.write(l)
            i+=len(l)
    #print(i)
    
    print("Terminando de recibir archivo")
    empty_socket(Client_conn)
    fileAudio = sr.AudioFile("audio.wav")
    
    with fileAudio as source:
        audio = r.record(source)
        
    response = {
        "success": True,
        "error": None,
        "transcription": None
    }
    print("Empezando reconocimiento")
    try:
        response["transcription"] = r.recognize_google(audio,language="es")
    except sr.RequestError:
        response["success"] = False
        response["error"] = "API unavailable"
    except sr.UnknownValueError:
        response["error"] = "Unable to recognize speech"

    print("Terminando reconocimiento")
    return response

def recibir_datos_host(Client_conn, Client_addr, listaConexiones,cond,semaforo,listaSemaforos,condSem):
    global ganador
    #Codigo del jugador host
    global NumPlayers
    PlayerPoints = 0
    try:
        cur_thread = threading.current_thread()
        #print("Recibiendo datos del cliente {} en el {}\n".format(Client_addr, cur_thread.name))
        
        print("\nConectado a", Client_addr)
        data = Client_conn.recv(buffer_size)
        #print ("Recibido,", data,"   de ", Client_addr)
        Client_conn.sendall(b"JH") #Manda al cliente el codigo JH jugador host
        data = Client_conn.recv(buffer_size) #recibe el numero de jugadores
        
        NumPlayers = int(data.decode()) #Actualiza la variable global
        Client_conn.sendall(b" ") #Envia algo al cliente para que continue
        
        data = Client_conn.recv(buffer_size)         
        with cond:
            cond.notifyAll() #Notifica que ya obtuvo el numero de jugadores
        
        with cond:
            print("\nEsperando a otros jugadores")
            cond.wait() #Espera a que la barrera se haya cumplido. (Le puse la condicion en vez de la barrera xD)
            
        print("\nJugadores listos Continuando..")
        Client_conn.sendall(b" ")
        data = Client_conn.recv(buffer_size)

        while True:
            Inicio = time()
            semaforo.acquire() # El host adquiere el semaforo
            empty_socket(Client_conn)
            Client_conn.sendall(b" ")
            #print("Esperando a recibir datos... ")
            while True:
                empty_socket(Client_conn)
                guess = recibirPregunta(Client_conn)
                if guess["transcription"]:
                    break
                if not guess["success"]:
                    break
                print("\nNo pude capturar nada. Que fue lo que dijiste?\n")
                Client_conn.sendall(b"*")
                empty_socket(Client_conn)
                empty_socket(Client_conn)
            
            if guess["error"]:
                print("ERROR: {}".format(guess["error"]))
                break
            
            #print("La cadena es: " + guess["transcription"])
            validarPregunta(guess["transcription"], listaConexiones, Client_conn,Client_addr)
            empty_socket(Client_conn)
            if not data:
                break
            if len(ganador)>0:
                print("\nGanó Jugador: {}\n".format(ganador)) #Mostrar quién es el jugador ganador
                Final = time()
                for c in listaConexiones: #Notificar al resto de jugadores que acabó la partida
                    if c!=ganador:
                        c.sendall((("Fin del juego.\nGanó jugador: %s.\nEl personaje es: %s\nDuración de la partida: %.2f") %(ganador,personaje,Final-Inicio)).encode())
                print("Duración de la partida: %.2f seg"%(Final-Inicio))
                break
            with condSem:
                condSem.notifyAll() #Indica al planificador de turnos que ya acabo de usar su semaforo y que continue con el proximo
            
    except Exception as e:
        print(e)
    finally:
        Client_conn.close()
    
def recibir_datos(Client_conn, Client_addr, listaConexiones,barrier,cond,semaforo,listaSemaforos,condSem):
    global ganador
    #Codigo para los otros jugadores, es muy parecido xD
    PlayerPoints = 0
    try:
        cur_thread = threading.current_thread()
        print("\nRecibiendo datos del cliente {} en el {}".format(Client_addr, cur_thread.name))
        print("\nConectado a", Client_addr)
        
        data = Client_conn.recv(buffer_size)
        print("\nEl tablero ha sido creado por otro usuario")
        #ETC: Error, tablero creado
        Client_conn.sendall(b"ETC") #Indica al cliente que sera tratado como un jugador no host
        data = Client_conn.recv(buffer_size)
        
        #Espera a que se cumpla la barrera
        print("\n"+threading.current_thread().name,
          'Esperando en la barrera con {} hilos más'.format(barrier.n_waiting))
        worker_id = barrier.wait()
        
        with cond:
            cond.notifyAll() #Notifica al host que la barrera ya se ha cumplido

        Client_conn.sendall(b" ") 
        data = Client_conn.recv(buffer_size)
        
        while True:
            Inicio=time()
            semaforo.acquire() # El host adquiere el semaforo
            empty_socket(Client_conn)
            Client_conn.sendall(b" ")
            #print("Esperando a recibir datos... ")
            while True:
                empty_socket(Client_conn)
                guess = recibirPregunta(Client_conn)
                if guess["transcription"]:
                    break
                if not guess["success"]:
                    break
                print("No pude capturar nada. Que fue lo que dijiste?\n")
                Client_conn.sendall(b"*")
                empty_socket(Client_conn)
                empty_socket(Client_conn)
            
            if guess["error"]:
                print("\nERROR: {}".format(guess["error"]))
                break
            
            #print("La cadena es: " + guess["transcription"])
            validarPregunta(guess["transcription"], listaConexiones, Client_conn, Client_addr)
            empty_socket(Client_conn)
            if not data:
                break
            if len(ganador)>0: #Si ya hay un ganador
                print("Ganó Jugador: {}\n".format(ganador)) #Mostrar quién es
                Final=time()
                for c in listaConexiones: #notificar al resto de los jugadores que la partida terminó
                    if c!=ganador:
                        c.sendall((("Fin del juego.\nGanó jugador: %s.\nEl personaje es: %s\nDuración de la partida: %.2f seg") % (ganador, personaje, Final - Inicio)).encode())
                print("Duración de la partida: %.2f seg" % (Final - Inicio))
                break
            with condSem:
                condSem.notifyAll() #Indica al planificador de turnos que ya acabo de usar su semaforo y que continue con el proximo
        
    except Exception as e:
        print(e)
    finally:
        Client_conn.close()


listaConexiones = []
serveraddr = (host, int(port))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as TCPServerSocket:
    TCPServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    TCPServerSocket.bind(serveraddr)
    TCPServerSocket.listen(int(numConn))
    print("El servidor TCP está disponible y en espera de solicitudes")

    servirPorSiempre(TCPServerSocket, listaConexiones)
