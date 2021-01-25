#!/usr/bin/python
import os, sys, subprocess, socket


class Server:
    #Intiailize server parameters port and hostname
    def __init__(self):
        self.theHost = socket.gethostname()
        self.port = 15086
        self.addr = ("", self.port)

    #startServer(self)
    #   Method called to create the socket object and start the server
    def startServer(self):
        self.mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.mySocket.bind(self.addr)
            print("Server created on: %s with port number: %d") % (
                self.theHost, self.port)
        except Exception as e:  # error checking if socket creation fails print error message
            print("Socket creation failed", e)
            sys.exit(1)
        # start a connection to the server
        self.startConnections()

    #createHeaders(statusCode, statusType)
    #   creates headers depending on the file type i.e cgi,html with
    #   appropriate header status code
    def createHeaders(self, statusCode, statusType):
        header = ""
        if (statusCode == 200):
            header = "HTTP/1.1 200 OK\n"

        elif (statusCode == 404):
            header = "HTTP/1.1 404 Not Found\n"

        if (statusType == "html" or statusType == "cgi"):
            header += "Content-Type: text/html\n\n"

        return header

    #startConnections()
    #   socket listens to incoming connection and accepts the connection request
    #   and prints out request messages of the file rendered
    def startConnections(self):
        self.mySocket.listen(socket.SOMAXCONN)
        while True:  #keep waiting for connections
            print("Listening for new connection")
            responseContent = ''
            responseHeaders = ''
            requestSocket, address = self.mySocket.accept()

            print('Server connected by', address[0])

            data = requestSocket.recv(4096)
            if not data:
                break

            line = bytes.decode(data)

            requestMethod = line.split(' ')[0]

            print("-------------------------------------------------")
            print("METHOD IS: {m}".format(m=requestMethod))
            print(
                "REQUEST BODY IS:\n--------------------\n {b}".format(b=line))
            print("------------------------")
            print("REQUEST PAGE IS:\n-------------------\n {b}".format(
                b=line.split(' ')[1]))
            print("----------------------------------------------\n")

            #------Supporting GET Methods--------
            if requestMethod == 'GET':
                print("Serving http GET request")

                fileRequested = line.split(' ')[1]

                fileRequested = fileRequested.split('?')

                line = ''
                if (len(fileRequested) > 1):
                    line = fileRequested[1]

                fileRequested = fileRequested[0]

                if (fileRequested == '/'):
                    fileRequested = 'index.html'

                print("Rendering web page: {b}".format(b=fileRequested))

                fileRequested = fileRequested.strip('/')

                try:
                    fileHander = open(fileRequested, 'rb')
                    responseContent = fileHander.read()
                    fileHander.close()

                    if (fileRequested.endswith('.html')):
                        responseHeaders = self.createHeaders(200, 'html')
                    elif (fileRequested.endswith('.cgi')):
                        responseHeaders = self.createHeaders(200, 'cgi')
                        responseContent = ''

                        if (len(line) > 1):
                            os.environ['QUERY_STRING'] = line

                        proc = subprocess.Popen(fileRequested,
                                                stdin=subprocess.PIPE,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
                        out = proc.communicate(input=None)

                        responseContent = out[0]
                        #print(responseContent)
                        #print(responseContent.split('Content-type: text/html\n')[0])

                        if (len(
                                responseContent.split(
                                    'Content-type: text/html\n')[0]) > 0):
                            cookie = responseContent.split(
                                'Content-type: text/html\n')[0]
                            cookie = cookie.split(':')[1]
                            os.environ['HTTP_COOKIE'] = cookie
                        responseContent = responseContent.split(
                            'Content-type: text/html\n')[1]

                except Exception as e:
                    print("ERROR 404 FILE NOT FOUND OR ERROR WITH CODE", e)
                    responseHeaders = self.createHeaders(404, 'html')

                    responseContent = """
                    <html>
                        <body>
                           <h2> Error 404 Bad Request </h2>
                        </body>
                    </html>"""

                serverResponse = str(responseHeaders) + str(responseContent)
                requestSocket.send(serverResponse)

            #-----supporting POST Methods------------
            elif requestMethod == 'POST':
                print("Serving http POST request")

                fileRequested = line.split(' ')[1]

                line = line.split('\n')

                if (line[-1].find('&') != -1):
                    line = line[-1]
                    input1 = line.split('&')[0]
                    input1 = input1.split('=')[1]

                    input2 = line.split('&')[1]
                    input2 = input2.split('=')[1]

                    cookie = input1 + '=' + input2
                    os.environ['HTTP_COOKIE'] = cookie

                if (fileRequested == '/'):
                    fileRequested = 'index.html'

                print("Serving web page: {b}".format(b=fileRequested))

                fileRequested = fileRequested.strip('/')

                try:
                    fileHander = open(fileRequested, 'rb')
                    responseContent = fileHander.read()  # read file content
                    fileHander.close()

                    if (fileRequested.endswith(".html")):
                        responseHeaders = self.createHeaders(200, 'html')

                    elif (fileRequested.endswith(".cgi")):
                        responseHeaders = self.createHeaders(200, 'cgi')

                        if (line.find('&') != -1):
                            proc = subprocess.Popen(fileRequested,
                                                    stdin=subprocess.PIPE,
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE)
                            out = proc.communicate(input=line)
                            print("TESTING OUT")
                            print(out)
                            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                        else:
                            proc = subprocess.Popen(fileRequested,
                                                    stdin=subprocess.PIPE,
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE)
                            out = proc.communicate(input=None)

                        responseContent = out[0]
                        responseContent = responseContent.split(
                            'Content-type: text/html\n')[1]

                except Exception as e:  #in case file was not found, generate 404 page
                    print(
                        "Warning, file not found OR THERE IS AN ERROR WITH YOUR CODE. Serving response code 404\n",
                        e)
                    responseHeaders = self.createHeaders(404, 'html')

                    responseContent = """
                    <html>
                        <body>
                            <h1>Error 404 File Not Found </h1>
                        </body>
                    </html>"""

                serverResponse = str(responseHeaders) + str(responseContent)
                requestSocket.send(serverResponse)

            else:
                responseHeaders = self.createHeaders(404, 'html')

                responseContent = """
                <html>
                    <body>
                        <p>unsupported HTTP method</p>
                    </body>
                </html>"""
                print("There is an Unsupported HTTP request method:",
                      requestMethod)

                serverResponse = str(responseHeaders) + str(responseContent)
                requestSocket.send(serverResponse)

            requestSocket.close()


#-------------------------------------------
#-------------------------------------------
print("Starting the HTTP Web Server\n")
tcpServer = Server()
tcpServer.startServer()
