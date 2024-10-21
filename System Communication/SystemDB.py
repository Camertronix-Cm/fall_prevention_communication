import sqlite3
import json

class FallDB:
    def __init__(self):
        self.__database_name = 'system.db'
        self.__MsgTable_Name = 'Ward'

        self.__WardTable_Name = 'Ward'
        self.__RefStatusTable_Name = 'RefStatus'
        self.__RoomTable_Name = 'Room'
        self.__BedTable_Name = 'Bed'
        self.__AlertTable_Name = 'Alert'
        # = sqlite3.connect('system.db')
        # self.__cursor = self.__conn.cursor()

    def __checkTable(self, cursor, Table_name, Table_Content):
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {Table_name}(
                {Table_Content}
            )
        ''')

    def __tableWrite(self, conn, sql_query, parameters):
        cursor = conn.cursor()
        try:
            cursor.execute(sql_query, parameters)
            conn.commit()
        except Exception as e:
            print(f'Error: {e}')
            self.__tableWrite(conn, sql_query, parameters)
    
    def __tableRead(self, cursor, sql_query, id=None):
        if id is None:
            cursor.execute(sql_query)
        else:
            cursor.execute(sql_query, (id,))
        return cursor.fetchall()

    def __MsgTable(self):
        # Connect to the SQLite database
        db_connect = sqlite3.connect(self.__database_name)
        cursor = db_connect.cursor()

        # Create the Ward table if not exist
        self.__checkTable(cursor, self.__MsgTable_Name, '''
            Instance_index INTEGER PRIMARY KEY,
            Msg_arr TEXT NOT NULL
        ''')
        db_connect.commit()
        return db_connect

    def deleteTabel(self, Table_name): # Test use only
        db_connect = sqlite3.connect(self.__database_name)
        cursor = db_connect.cursor()
        cursor.execute(f'DROP TABLE IF EXISTS {Table_name}')


    def __WardTable(self):
        # Connect to the SQLite database
        db_connect = sqlite3.connect(self.__database_name)
        cursor = db_connect.cursor()

        # Create the Ward table if not exist
        self.__checkTable(cursor, self.__WardTable_Name, '''
            Ward_id INTEGER PRIMARY KEY AUTOINCREMENT,
            Label TEXT NOT NULL
        ''')
        db_connect.commit()
        return db_connect

    def __Ref_StatusTable(self):
        db_connect = sqlite3.connect(self.__database_name)
        cursor = db_connect.cursor()
        # Create the possible status table if not created yet
        self.__checkTable(cursor, self.__RefStatusTable_Name, '''
            Status_id INTEGER PRIMARY KEY,
            Label TEXT NOT NULL
        ''')
        db_connect.commit()
        return db_connect

    def __RoomTable(self):
        db_connect = sqlite3.connect(self.__database_name)
        cursor = db_connect.cursor()
        # Create the Rooms table if not created yet
        self.__checkTable(cursor, self.__RoomTable_Name, f'''
            Room_id INTEGER PRIMARY KEY,
            Ward_id INTEGER NOT NULL,
            Label TEXT NOT NULL,
            Status_id INTEGER NOT NULL,
            FOREIGN KEY (Ward_id) REFERENCES {self.__WardTable_Name}(Ward_id) ON DELETE CASCADE,
            FOREIGN KEY (Status_id) REFERENCES {self.__RefStatusTable_Name}(Status_id) ON DELETE CASCADE
        ''')
        db_connect.commit()
        return db_connect

    def __BedTable(self):
        db_connect = sqlite3.connect(self.__database_name)
        cursor = db_connect.cursor()
        # Create the Bed table if not created yet
        self.__checkTable(cursor, self.__BedTable_Name, f'''
            Bed_id INTEGER PRIMARY KEY,
            Room_id INTEGER NOT NULL,
            Label TEXT NOT NULL,
            Patient TEXT,
            Coordinates TEXT,
            P_Coordinates TEXT,
            FOREIGN KEY (Room_id) REFERENCES {self.__RoomTable_Name} (Room_id) ON DELETE CASCADE
        ''')
        db_connect.commit()
        return db_connect

    def __AlertTable(self):
        db_connect = sqlite3.connect(self.__database_name)
        cursor = db_connect.cursor()
        # Create the Alerts table if not created yet
        self.__checkTable(cursor, self.__AlertTable_Name, f'''
            A_timestamp TIMESTAMP PRIMARY KEY,
            Bed_id INTEGER NOT NULL,
            Type INTEGER,
            Content TEXT,
            FOREIGN KEY (Bed_id) REFERENCES {self.__BedTable_Name} (Bed_id) ON DELETE CASCADE
        ''')
        db_connect.commit()
        return db_connect

    # MESSAGE (Messages waiting to be sent) TABLE QUERY
    def _getMsg(self, Instance_index=None):
        access_Msg = self.__MsgTable()
        return self.__tableRead(access_Msg.cursor(), f'SELECT (Msg_arr) FROM {self.__MsgTable_Name} WHERE Instance_index = ?', Instance_index)
   
    def _addMsg(self, Instance_index,  Msg_arr): 
        access_Msg = self.__MsgTable()
        self.__tableWrite(access_Msg, f'INSERT INTO {self.__MsgTable_Name} (Instance_index, Msg_arr) VALUES(?)', (Instance_index, Msg_arr))
    
    def _deleteMsg(self, Instance_index):
        access_Msg = self.__MsgTable()
        self.__tableWrite(access_Msg, f'DELETE FROM {self.__MsgTable_Name} WHERE Instance_index = ?', (Instance_index,))


    # WARD TABLE QUERY
    def getWard(self, Ward_id=None):
        access_Ward = self.__WardTable()
        if Ward_id is None: # meaning get all wards
            return self.__tableRead(access_Ward.cursor(), f'SELECT * FROM {self.__WardTable_Name}')
        else: # meaning get just a particular wards
            return self.__tableRead(access_Ward.cursor(), f'SELECT (Label) FROM {self.__WardTable_Name} WHERE Ward_id = ?', Ward_id)
   
    def addWard(self,  Label):
        access_Ward = self.__WardTable()
        self.__tableWrite(access_Ward, f'INSERT INTO {self.__WardTable_Name} (Label) VALUES(?)', (Label,))
 
    def updateWard(self, Ward_id, Label):
        access_Ward = self.__WardTable()
        self.__tableWrite(access_Ward, f'UPDATE {self.__WardTable_Name} SET Label = ? WHERE Ward_id = ?', (Label, Ward_id))
    
    def deleteWard(self, Ward_id):
        access_Ward = self.__WardTable()
        self.__tableWrite(access_Ward, f'DELETE FROM {self.__WardTable_Name} WHERE Ward_id = ?', (Ward_id,))

    # REF_STATUS_QUERY
    def getStatus(self, Status_id=None):
        access_Status = self.__Ref_StatusTable()
        if Status_id is None: # meaning get all status
            return self.__tableRead(access_Status.cursor(), f'SELECT * FROM {self.__RefStatusTable_Name}')
        else: # meaning get just a particular status
            return self.__tableRead(access_Status.cursor(), f'SELECT (Label) FROM {self.__RefStatusTable_Name} WHERE Status_id = ?', Status_id)
   
    def addStatus(self, Status_id,  Label):
        access_Status = self.__Ref_StatusTable()
        self.__tableWrite(access_Status, f'INSERT INTO {self.__RefStatusTable_Name} (Status_id, Label) VALUES(?, ?)', (Status_id, Label))
 
    def updateStatus(self, Status_id, Label):
        access_Status = self.__Ref_StatusTable()
        self.__tableWrite(access_Status, f'UPDATE {self.__RefStatusTable_Name} SET Label = ? WHERE Status_id = ?', (Label, Status_id))
    
    def deleteStatus(self, Status_id):
        access_Status = self.__Ref_StatusTable()
        self.__tableWrite(access_Status, f'DELETE FROM {self.__RefStatusTable_Name} WHERE Status_id = ?', (Status_id,))

    # ROOM_QUERY
    def getRoom(self, Field_name=None, Field_value=None):
        '''Returns the entire room object'''
        access_Room = self.__RoomTable()
        return self.__tableRead(access_Room.cursor(), f'SELECT * FROM {self.__RoomTable_Name}')
           
    def addRoom(self, Room_id, Ward_id, Label): # Add a Room to the Room table
        '''Add a new record (Room) with it 
        {Room_id} (read from camera and entered by the user),
        {Ward_id} of the ward the room is found in
        {Label} entered by the UserWarning
        Status will be set to 0 by default'''
        access_Room = self.__RoomTable()
        self.__tableWrite(access_Room, f'INSERT INTO {self.__RoomTable_Name} (Room_id, Ward_id, Label, Status_id) VALUES(?, ?, ?, ?)', (Room_id, Ward_id, Label, 0))
 
    def updateRoom(self, Ref_Field_name, Ref_Field_value, Update_Field_name, Update_Field_value):
        '''Update {Update_Field_name} to the value {Update_Field_value} for a record with {Ref_Field_name} = {Ref_Field_value}'''
        access_Room = self.__RoomTable()
        self.__tableWrite(access_Room, f'UPDATE {self.__RoomTable_Name} SET {Update_Field_name} = ? WHERE {Ref_Field_name} = ?', (Update_Field_value, Ref_Field_value))
    
    def deleteRoom(self, Field_name, Field_value): # Delete a room from the room table
        '''Delete any record with {Field_name} = {Field_value}'''
        access_Room = self.__RoomTable()
        self.__tableWrite(access_Room, f'DELETE FROM {self.__RoomTable_Name} WHERE {Field_name} = ?', (Field_value,))

    # BED_QUERY
    def getBed(self):
        '''Returns the entire bed object'''
        access_Bed = self.__BedTable()
        return self.__tableRead(access_Bed.cursor(), f'SELECT * FROM {self.__BedTable_Name}')
   
    def addBed(self, Bed_id, Room_id, Label): # Add a Bed to the Bed table
        '''Add a new record (Bed) with it 
        {Bed_id} (read from camera and entered by the user),
        {Room_id} of the Room the room is found in
        {Label} entered by the User
        Only these three are required for the creation of a new bed record'''
        access_Bed = self.__BedTable()
        self.__tableWrite(access_Bed, f'INSERT INTO {self.__BedTable_Name} (Bed_id, Room_id, Label) VALUES(?, ?, ?)', (Bed_id, Room_id, Label))
 
    def updateBed(self, Ref_Field_name, Ref_Field_value, Update_Field_name, Update_Field_value=''):
        '''Update {Update_Field_name} to the value {Update_Field_value} for a record with {Ref_Field_name} = {Ref_Field_value}
        If you want to delete an cell (like a case where patient is logged out so you want to remove the patient name from the bed)
        you won't need to enter a value for {Update_Field_value}'''
        access_Bed = self.__BedTable()
        self.__tableWrite(access_Bed, f'UPDATE {self.__BedTable_Name} SET {Update_Field_name} = ? WHERE {Ref_Field_name} = ?', (Update_Field_value, Ref_Field_value))
    
    def deleteBed(self, Field_name, Field_value): # Delete a Bed from the Bed table
        '''Delete any record with {Field_name} = {Field_value}'''
        access_Bed = self.__BedTable()
        self.__tableWrite(access_Bed, f'DELETE FROM {self.__BedTable_Name} WHERE {Field_name} = ?', (Field_value,))

    # ALERT_QUERY
    def getAlert(self, Field_name=None, Field_value=None):
        '''Returns the entire alert object'''
        access_Alert = self.__AlertTable()
        return self.__tableRead(access_Alert.cursor(), f'SELECT * FROM {self.__AlertTable_Name}')
           
    def addAlert(self, A_timestamp, Bed_id, Type, Content): # Add a Alert to the Alert table
        '''Add a new record (Alert) with it 
        {A_timestamp} timestamp of the alert
        {Bed_id} of the Bed that triggered the Alert
        {Type} (the serverity of the alert),
        {Content} of the alert
        Only these three are required for the creation of a new bed record'''
        access_Alert = self.__AlertTable()
        self.__tableWrite(access_Alert, f'INSERT INTO {self.__AlertTable_Name} (A_timestamp, Bed_id, Type, Content) VALUES(?, ?, ?, ?)', (A_timestamp, Bed_id, Type, Content))
 
    def updateAlert(self, Ref_Field_name, Ref_Field_value, Update_Field_name, Update_Field_value=''):
        '''Update {Update_Field_name} to the value {Update_Field_value} for a record with {Ref_Field_name} = {Ref_Field_value}'''
        access_Alert = self.__AlertTable()
        self.__tableWrite(access_Alert, f'UPDATE {self.__AlertTable_Name} SET {Update_Field_name} = ? WHERE {Ref_Field_name} = ?', (Update_Field_value, Ref_Field_value))
    
    def deleteAlert(self, Field_name, Field_value): # Delete a Alert from the Alert table
        '''Delete any record with {Field_name} = {Field_value}'''
        access_Alert = self.__AlertTable()
        self.__tableWrite(access_Alert, f'DELETE FROM {self.__AlertTable_Name} WHERE {Field_name} = ?', (Field_value,))


class FallFile:
    def __init__(self):
        pass
    
    def __updateFile(self, filename, msg_dictionary):
        with open(filename + '.txt', 'w') as file:
            json.dump(msg_dictionary, file)
    
    def __readFileContentOf(self, filename):
        file_content = {}
        try:
            with open(filename + '.txt', 'r') as file:
                # print("File exist")
                file_content = json.load(file)
        except FileNotFoundError: # Else create the message file and store the current msg
            print("File not found so creating one")
            self.__updateFile(filename, {})
            self.__readFileContentOf(filename)
        return file_content

    def _getTerminalUID(self):
        '''get the saved terminal ID upon power on'''
        terminal_id = 0
        terminal_info = self.__readFileContentOf('terminal')
        if 'T_ID' in terminal_info:
            terminal_id = terminal_info['T_ID']
        return terminal_id

    def _saveTerminalUID(self, t_id):
        '''to be called by the system to register the terminal ID upon pairing with the termininal'''
        terminal_info = self.__readFileContentOf('terminal')
        terminal_info['T_ID'] = t_id
        self.__updateFile('terminal', terminal_info)
