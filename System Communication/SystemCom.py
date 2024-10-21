from SystemDB import FallDB, FallFile
import json
import time
import serial
import struct

class _Messaging(FallDB):
    def __init__(self):
        super().__init__()
        self.__ser = serial.Serial("/dev/ttyACM0", 115200, timeout=0.5)
        self.__Hi_Premeable = 0xAA
        self.__Lo_Premeable = 0x55
        self.__HiByte = 0xFF
        self.__LoByte = 0x00

        self._Hi_MyUID = 0x00
        self._Lo_MyUID = 0x00
        self._Hi_ExUID = 0xCe # 00
        self._Lo_ExUID = 0xC4 # 00

        self._CurrentStateID = 0
        self._SendingInstance = 1 # ranges from 1 to FE, it signifies the pending message address. It sends messages from 1 address to another

        time.sleep(1)
        self.__ser.reset_input_buffer()
        self.__LastMeshMessageSendTime = 0
        print('send uid cmd')
        #Now send command to get the device UID || {0xAA, 0x55, 0x00, 0x01, 0xFF, 0x00}
        self._sendOrPendMsg([0x1A])

    
    def __listenToModem(self):
        '''Listen to serial for incoming packets'''
        serial_incoming = bytearray()
        time.sleep(0.01)
        while self.__ser.in_waiting > 0:
            bytes_in = self.__ser.read()
            serial_incoming.extend(bytes_in)
        return serial_incoming

    def _sendOrPendMsg(self, sending_arr):
        ''''Function to store the hex_arr content to Pending messages for it to be accessed and sent
        sending_arr = the array intended to be sent'''
        # The preameable and ength of the sending_arr
        message_arr = [self.__Hi_Premeable, self.__Lo_Premeable, len(sending_arr) - 1] # The minus one is for remove count for cmd
        CRC_bytes = [self.__HiByte, self.__LoByte] # The HiByte and LoByte

        if sending_arr[0] == 0x07: # if it's a message to be sent then add the instanceIndex and subIndex (0)
            message_arr[2] += 4 # add the length by two [instanceIndex, subIndex]
            # look for empty instance_index on the db
            instance_index = 1
            while instance_index < 0xFD and self._getMsg(instance_index): # exit when the current index is not found in pending messages or index above ff
                instance_index += 1
            
            # Pending_Messages = self._readFileContentOf('PendingMsgs')

            message_arr.extend([0x07]) # COMMAND mesh message
            message_arr.extend([instance_index, 0]) # add the instanceIndex = register and the subIndex = 0
            message_arr.extend([0, 0]) # add the meshOpcode [still to get the value]
            
            # Add the sending_arr to the Preameable
            message_arr.extend(sending_arr[1:]) # command (sending_arr[0]) already added soexclude it here
            # Conclude the array with the CRC
            message_arr.extend(CRC_bytes)

            # it's a message, so add to pending message register
            print("adding current message")
            # Convert the hexadecimal array to a list of hex strings
            message_arr_str = [hex(x) for x in message_arr]
            # Convert the list of hex strings to a JSON string
            message_arr_json = json.dumps(message_arr_str)
            # Now add the message array as string on the pending messages database
            self._addMsg(instance_index, message_arr_json)
        
        else: # if not, then send the array to the modem
            message_arr.extend(sending_arr)
            message_arr.extend(CRC_bytes)
            self.__ser.write(message_arr)

    def _pendingMsgSend(self):
        '''Function that does the actual message transmission
        It checks through each Pending message address if there's a message to be sent and sends it
        or go to the next address if there's no pending message to be sent'''
        TimeAfterLastSent = 3
        if self.__LastMeshMessageSendTime > 0:
            TimeAfterLastSent = int(time.time()) - self.__LastMeshMessageSendTime
        if TimeAfterLastSent > 2:
            # get the next message to send [Check if a message exist for the current SendingInstance]
            message_arr_row = self._getMsg(self._SendingInstance)
            if message_arr_json:
                print("self._SendingInstance " + str(self._SendingInstance))
                # Extract the JSON string from the database result
                message_arr_json = message_arr_row[0] # gets the turple of the message string arr
                # Deserialize the JSON string back into a list of hex strings
                message_arr_str = json.loads(message_arr_json)
                # Convert the list of hex strings back to integers
                message_arr = [int(x, 16) for x in message_arr_str]
                
                # Now send the array over serial
                self.__ser.write(message_arr) # send the array in that id
                self.__LastMeshMessageSendTime = int(time.time()) # get the current message sent time
            else: # if no pending msg in that address, go to the next message address where the check will be done
                self._SendingInstance += 1
                if self._SendingInstance == 0xFF:
                    self._SendingInstance = 1
                self.__LastMeshMessageSendTime = 0 # indicating no message was sent

    def _sendMeshMessage(self, msg_destination, msg_arr):
        '''Will send the message packet {msg_arr} to {msg_destination}'''
        # Send mesh message command, Message souce and destination
        message_type = msg_arr[0]
        message_arr = [0x07, message_type]
        message_arr.extend(msg_destination) # add destination (destination is same for camera but will be different for terminal)
        message_arr.extend([self._Hi_MyUID, self._Lo_MyUID]) # add source
        
        if message_type == 4: # if it's a notification then add alert severifty
            message_timestamp = int(time.time()) # get the current timestamps
            bed_num = msg_arr[1]
            Alert_severity = msg_arr[2]
            message_arr.extend([bed_num, Alert_severity]) # add the bed_num and the alert_severity
            # add the timestamp
            message_arr.extend(struct.pack('!I', message_timestamp))
        message_arr.extend(msg_arr[3:])
        self._sendOrPendMsg(message_arr)

    def _messageHandler(self, message_arr): # array from pos 11
        '''Will handle the incoming messages and save in the database'''
        # message_arr is the source ID [0, 1], the bed [2] alert severity [3], the timestamp [4, 5, 6, 7], and the message content [19 ---]
        print(' message data')
        print(" ".join(hex(num) for num in message_arr))
        # get the source id of the incoming alert
        # the bed_id will be the camera id + the bed num
        source_bed_id = message_arr[1] + message_arr[0]*0x100 + message_arr[2]
        # get the alert severity
        alert_severity = message_arr[3]
        # get the timestamp
        message_timestamp = struct.unpack("!I", bytes(message_arr[4:8]))[0]
        # get the message content
        message_array = message_arr[8:]
        print(" ".join(hex(num) for num in message_array))
        # covert the message content to a string
        message_content = ''.join([chr(x) for x in message_array])
        # add the message to the database
        self.addAlert(message_timestamp, source_bed_id, alert_severity, message_content)
    
    def _coordinatesHandler(self, coord_key, coord_arr):
        '''Will handle the incoming coordinates and save in the database'''
        # coord_arr is the source_ID [0, 1], the number of coordinates [2, 3], the coordinates [4 ---]
        # get the source of the coords
        coord_source_id = coord_arr[0] + coord_arr[1]*0x100
        # get the number of coords
        num_coords = coord_arr[2] + coord_arr[3]*0x100
        # get the coordinates
        coord_array = coord_arr[4:]
        # add the coordinates to the database
        if coord_key == 'Bed':
            for num in range(num_coords):
                coord_str = str(coord_array[1] + coord_array[0]*0x100) + ',' + str(coord_array[3] + coord_array[2]*0x100) + ',' + str(coord_array[5] + coord_array[4]*0x100) + str(coord_array[7] + coord_array[6]*0x100)
                self.updateBed('Bed_id', coord_source_id+num, 'Coordinates', coord_str)
                # remove the first eight elements of the arr
                coord_array = coord_array[8:]
        elif coord_key == 'Patient':
            for num in range(num_coords):
                coord_str = str(coord_array[1] + coord_array[0]*0x100) + ',' + str(coord_array[3] + coord_array[2]*0x100)
                self.updateBed('Bed_id', coord_source_id+num, 'Coordinates', coord_str)
                # remove the first four elements of the arr
                coord_array = coord_array[4:]
    
    def _checkForIncoming(self):
        '''Collect and Process any serial incoming packets
        This will handle general commands and will only return the array if it's a message'''
        # incoming = bytearray()
        incoming = self.__listenToModem()
        # verify it's a valid system message packet
        if incoming and incoming[0] == self.__Hi_Premeable and incoming[1] == self.__Lo_Premeable:
            print("incoming") # 0xAA, 0x55, 0x01, 0x12, 0x00, 0xFF, 0x00
            # print(incoming[2:len(incoming)-2])
            print(" ".join(hex(num) for num in incoming[2:len(incoming)-2]))
            packet_cmd = incoming[3]
            print("packet_cmd: " + str(packet_cmd))
            # check the cmd index
            if packet_cmd == 0x12:
                print(f"Error response: {incoming[4]}")

            elif packet_cmd == 0x1B: # Response to UID
                self._Hi_MyUID = incoming[4]
                self._Lo_MyUID = incoming[5]
                # print("MyUID: " + str(Lo_MyUID + Hi_MyUID*0x100))
                print(f"My UID: 0x{format(self._Lo_MyUID + self._Hi_MyUID*0x100, '04X')}")

                # gotten UUID now request check for mesh connection
                self._sendOrPendMsg([0x10]) # Current state request

            elif packet_cmd == 0x11: # response to mesh connection check
                self._CurrentStateID = incoming[4]
                print("Mesh connection state response: " + str(self._CurrentStateID))
            
            elif packet_cmd == 0x0F: # message delivery feedback
                # message has been sent so remove the message from store
                instance_index = incoming[4]
                self._deleteMsg(instance_index)

            elif packet_cmd == 7 and incoming[9] == self._Hi_MyUID and incoming[10] == self._Lo_MyUID: # incoming message
                if incoming[8] == 0x0F: # if it a message delivery feedback then delete the current message that was being sent
                    print("gotten some feeds")
                    instance_index = incoming[4]
                    self._deleteMsg(instance_index)
                    return bytearray()
                else: # it's an incoming message
                    # Cut out the message content to send over mesh
                    delivery_feedback = incoming[0:15]
                    # swap the destination and source IDs
                    delivery_feedback[9] = incoming[11]
                    delivery_feedback[10] = incoming[12]
                    delivery_feedback[11] = incoming[9]
                    delivery_feedback[12] = incoming[10]
                    # add the CRC bytes
                    delivery_feedback[13] = self.__HiByte
                    delivery_feedback[14] = self.__LoByte
                    # Change the message typt to 0x0F to indicate delivery report and change the length to 9
                    delivery_feedback[2] = 9
                    delivery_feedback[8] = 0x0F

                    # Send a message delivery feedback to indicate message received
                    # No need storing or ensuring that it is sent
                    print('sENDING BACK FEED')
                    print(" ".join(hex(num) for num in delivery_feedback))
                    self.__ser.write(delivery_feedback)
                    return incoming
            else:
                print("Not command")
        self._pendingMsgSend() # check if there's a message to send and send it
        return bytearray()

    
    def getCurrentState(self): # CurrentStateRequest
        self._sendOrPendMsg([0x10])


class Camera(_Messaging, FallFile):
    def __init__(self):
        super().__init__()
        self.SharedVariable = 0
        
        # Read the terminal ID
        '''this ID will be the terminal ID.
        If no connection has been establised between the camera and a terminal, then this will be 0'''
        Terminal_ID = self._getTerminalUID()
        self._Hi_ExUID = (Terminal_ID >> 8) & 0xff
        self._Lo_ExUID = Terminal_ID & 0xff
        print(f"Serial OK: 0x{format(Terminal_ID, '04X')}")


    def _confirmPairRequest(self, pair_arr):
        '''Register the source as terminal and send a message command to response response pair to the source'''

        # confirming pair request is storing ExUID as Terminal ID
        self._Hi_ExUID = pair_arr[0]
        self._Lo_ExUID = pair_arr[1]

        # pair request will only come from the terminal so save the id that sent the request
        self._saveTerminalUID(self._Lo_ExUID + self._Hi_ExUID*0x100)
        print(f"Terminal UID: 0x{format(self._Lo_ExUID + self._Hi_ExUID*0x100, '04X')}")

        # Now send back a pair request accepted response
        pair_response = [0x07, 0, self._Hi_ExUID, self._Lo_ExUID, self._Hi_MyUID, self._Lo_MyUID, 0, 1]
        print("Sending pair response")
        self._sendOrPendMsg(pair_response)
      
    def _sendCoordinates(self, coordinate_array, coordinate_type):
        '''To send the {coordinate_array} as a message with messsage type = {coordinate_type}'''
        msg_arr = [coordinate_type]
        msg_arr.extend(coordinate_array)
        self._sendMeshMessage([self._Hi_ExUID, self._Lo_ExUID], msg_arr)

    def sendBedCoordinates(self, bed_coord_arr):
        coord_arr = [0, len(bed_coord_arr)]
        for bed_coord in bed_coord_arr:
            coord_x1 = bed_coord[0]
            coord_y1 = bed_coord[1]
            coord_x2 = bed_coord[2]
            coord_y2 = bed_coord[3]
            coord_arr.extend([(coord_x1 >> 8) & 0xff, coord_x1 & 0xff, (coord_y1 >> 8) & 0xff, coord_y1 & 0xff, (coord_x2 >> 8) & 0xff, coord_x2 & 0xff, (coord_y2 >> 8) & 0xff, coord_y2 & 0xff])
        self._sendCoordinates(coord_arr, 0x02)
    def sendPatientCoordinates(self, patient_coord_arr):
        coord_arr = [0, len(patient_coord_arr)]
        for patient_coord in patient_coord_arr:
            coord_x = patient_coord[0]
            coord_y = patient_coord[1]
            coord_arr.extend([(coord_x >> 8) & 0xff, coord_x & 0xff, (coord_y >> 8) & 0xff, coord_y & 0xff])
        self._sendCoordinates(coord_arr, 0x03)
    
    def sendNotification(self, notification_str, notification_type, bed_num):
        '''To send the notification packet {notification_str} to the nurses terminal'''
        msg_arr = [0x04, bed_num, notification_type] # Message type  = notification
        msg_str_arr = bytearray(notification_str, 'utf-8') # message content array
        msg_arr.extend(msg_str_arr) # join the array to the command
        self._sendMeshMessage([self._Hi_ExUID, self._Lo_ExUID], msg_arr)

    
    def checkForIncoming(self):
        '''Collect and Process any serial incoming packets'''
        incoming = self._checkForIncoming()
        if incoming: # it's getting an incoming cus it's it's a message array
            print("T message")
            message_type = incoming[8]
            if message_type == 0: # Incoming pair request
                print("Incoming pair request")
                # print(incoming)
                print(" ".join(hex(num) for num in incoming))
                self._Hi_ExUID = incoming[11]
                self._Lo_ExUID = incoming[12]
                print(f"External UID: 0x{format(self._Lo_ExUID + self._Hi_ExUID*0x100, '04X')}")
                msg_id = incoming[14] + incoming[13]*0x100

                # Ensure it's a request 
                if msg_id == 0: # it's a pair request implying from a terminal
                    self._confirmPairRequest(incoming[11:13]) # save and send a response back to that source id
                        
            elif message_type == 1: # Incoming command
                self.SharedVariable = incoming[13] # store the command in the SharedVar
                print(" SharedVariable:  " + str(self.SharedVariable))
                '''if incoming[9] == 1:
                    sendBedCoordinate(500, 300, 200, 100)'''


class Terminal(_Messaging):
    def __init__(self): 
        super().__init__()


    def _sendPairRequest(self, des_ID):
        '''Send mesh message command to request pair to the destination {des_ID}'''
        pair_cmd = [0x07, 0, (des_ID >> 8) & 0xff, des_ID & 0xff, self._Hi_MyUID, self._Lo_MyUID, 0, 0]
        print("Sending pair request")
        self._sendOrPendMsg(pair_cmd)
        print(pair_cmd)

    def sendCommand(self, cmd_destination, the_cmd):
        '''To send the command {the_cmd} to {cmd_destination}'''
        cmd_arr = [0x01, the_cmd]
        self._sendMeshMessage(cmd_destination, cmd_arr)
    
    def checkForIncoming(self):
        '''Collect and Process any serial incoming packets'''
        incoming = self._checkForIncoming()
        if incoming: # it's getting an incoming cus it's it's a message array
            print("T message from ")
            print(" ".join(hex(num) for num in incoming[11:13]))
            message_type = incoming[8]
            if message_type == 0: # Incoming pair response
                print("Incoming pair response")
                self._Hi_ExUID = incoming[11]
                self._Lo_ExUID = incoming[12]
                print(f"External UID: 0x{format(self._Lo_ExUID + self._Hi_ExUID*0x100, '04X')}")
                msg_id  = incoming[14] + incoming[13]*0x100

                # Ensure it's a response 
                if msg_id == 1: # it's a pair response implying it's from a camera
                    self.saveCameraInfo(incoming[10] + incoming[9]*0x100, "", 'status') # update camera status to active
                  
            elif message_type == 2: # Incoming bed coordinates
                print(" ---------------Bed coordinate------------- ")
                number_of_coords = incoming[14] + incoming[13]*0x100
                print(f'Number of coordinates: {number_of_coords}')
                cd_ar = incoming[15:15+number_of_coords*8]
                print("".join(hex(num) for num in cd_ar))
                for cd in range(number_of_coords*8):
                    print(f'{cd_ar[cd+1] + cd_ar[cd+0]}, {cd_ar[cd+3] + cd_ar[cd+2]}, {cd_ar[cd+5] + cd_ar[cd+4]}, {cd_ar[cd+7] + cd_ar[cd+6]}')
                    cd += 8
                # Save the coordinates
                self._coordinatesHandler('Bed', incoming[11:15+number_of_coords*8]) # 0, 1 source, 2, 3 number of coords, 4-num_of_coords*8 bed coords
               
            elif message_type == 3: # Incoming Patient coordinates
                print("---------------Patient coordinate--------------- ")
                num_of_coords = incoming[14] + incoming[13]*0x100
                print(f'Number of coordinates: {num_of_coords}')
                cd_ar = incoming[15:15+num_of_coords*4]
                print("".join(hex(num) for num in cd_ar))
                for cd in range(num_of_coords*4):
                    print(f'{cd_ar[cd+1] + cd_ar[cd+0]}, {cd_ar[cd+3] + cd_ar[cd+2]}')
                    cd += 4
                # Save the coordinates
                self._coordinatesHandler('Patient', incoming[11:15+num_of_coords*4]) # 0, 1 source, 2, 3 number of coords, 4-num_of_coords*4 patient coords

            elif message_type == 4: # Incoming Notifications
                print("---------------Notifications--------------- ")
                print(" ".join(hex(num) for num in incoming[13:15])) # message id
                print(incoming[15:len(incoming)-2])
                self._messageHandler(incoming[11 : len(incoming)-2])
                print("done")
