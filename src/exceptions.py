class Impossible(Exception):
    '''Exception raised when action is impossible to be performed
    
    Reason is in the exception message
    '''

class QuitWithoutSaving(SystemExit):
    '''Can be raised to exit the game without automatically saving'''