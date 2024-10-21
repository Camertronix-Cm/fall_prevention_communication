This repository contains the communication modules to be import by the camera and the terminal.
SystemDB.py file contains the database classes while the SystemCom.py file contains the communication module

Importing this module to a Camera
    import Camera from SystemCom as {Prefared_reference}
    This module will initialize the communication, and provied an interger variable {SharedVariable} that will hold the latest command sent from the termial.
    
    The terminal ID will also be automatically read during initialization so you wont't need to call a method to get the communication.

    Methods to be used and how they should be used.

    [Prefared_reference.checkForIncoming]
    Create a thread that will always run the method {Prefare_reference.checkForIncoming}.
    It is essential that this method runs on it's own thread so that no incoming message (in this case commands/request from the terminal) is lost. 
    Any incoming incoming command is stored in the {Prefared_reference.SharedVariable}. 
    You will need to have a variable that will hold the value stored in Prefared_reference.SharedVariable when there's a current command (that is Prefared_reference.ShareVariable > 0). Once this value is gotten, please clear Prefared_reference.SharedVariable.
    In summary:
        Say your local variable is HoldCommand
        This is what your communication thread should look like
    1    while true:
    2       Prefared_reference.checkForIncoming
    3       if Prefared_reference.SharedVariable > 0:
    4           HoldCommand = Prefared_reference.SharedVariable
    5           Prefared_reference.SharedVarible = 0
                Action_For_HoldCommand_block (explained below)
    The are three possible commands you will need to handle. That is Prefared_reference.SharedVariable/HoldCommand will either be:-
    {
        1: Bed Coordinates request
        2: Start streaming patient coordinates
        3: Stop streaming patient coordinates
    }
    So the Action_For_HoldCommand_block should look like this
    6           if HoldCommand == 1:
    7               call the send_Bed_Coordinate_method
    8               HoldCommand = 0 (clear it since the bed coordinate is to be sent just once when request)
    9           elif HoldCommand == 2:
    10              call the send_Patient_Coordinate_method
    11          eiif HoldCommand == 3:
    12              HoldCommand = 0 (HoldCommand = 3 means stop streaming patient coordinates so clear HoldCommand so that no action will be done on the next check)

    [Prefared_reference.sendBedCoordinates]
    WHEN: 
        This method should be called when you want to send bed coordinates.
    HOW: 
        Prefared_reference.sendBedCoordinates(bed_coord_arr)
    DETAILS:
        bed_coord_arr should be an int Nx4 array of the bed coordinates where N is the number of beds. Meaning this method is expecting a multidimentional int array (N > 0). 
        Each bed array should contain four positive numbers [x1, y1, x2, y2] and the bed coordinates arrays should be ordered according to the bed numbering on the terminal
        So if there is just 1 bed in a room, then it'll be a 1x4 array. meaning {bed_coord_arr} should look like [[x1, y1, x2, y2]]
        For two beds: [[x1, y1, x2, y2], [x1, y1, x2, y2]]
        For the beds: [[x1, y1, x2, y2], [x1, y1, x2, y2], [x1, y1, x2, y2]]
        and so on
    
    [Prefared_reference.SendPatientCoordinates]
    WHEN: 
        This method should be called when you want to send patient coordinates.
    HOW: 
        Prefared_reference.sendPatientCoordinates(patient_coord_arr)
    DETAILS:
        patient_coord_arr should be an int Nx2 array of the bed coordinates where N is the number of patients. Meaning this method is expecting a multidimentional int array (N > 0). 
        Each patient array should contain four positive numbers [x, y] and the patient coordinates arrays should be ordered according to the bed numbering on the terminal
        So if there is just 1 bed in a room, then it'll be a 1x2 array. meaning {patient_coord_arr} should look like [[x, y]]
        For two beds: [[x, y], [x, y]]
        For the beds: [[x, y], [x, y], [x, y]]
        and so on
    
    [Prefared_reference.sendAlert]
    WHEN: 
        This method should be called when you want to send an alert (warning).
    HOW: 
        Prefared_reference.sendAlert(notification_str, notification_type, bed_num)
    DETAILS:
        * notification_str= string content of the Alert
        * notification_type= the severity of the warning, this should be number(byte) that signifies how severe the condition your reporting is. It should either be 1/2.
        For instance, if a patient is at the edge of the bed (about falling), notification_type=1
                      if the patient has fallen, notification_type=2
        * bed_num= the bed that's triggering the notifcation, that is the bed having the patient you're report for.