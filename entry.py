from sumtypes import sumtype, match, constructor

class EntryException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

# Class that represents a line in the trial
# Each constructor has a time
@sumtype
class Entry:

    # (x,y) : gaze position at the given time
    Position = constructor('time', 'x', 'y')

    # Fixation begins on the next entry
    Start_fixation = constructor ('time')
    # Fixation ended at the previous entry
    End_fixation = constructor ('time')

    # Saccade begins at the next entry
    Start_saccade = constructor ('time')
    # Saccade ended at the previous entry
    End_saccade = constructor ('time')

    # Blink begins at the next entry
    Start_blink = constructor ('time')
    # Blink ended at the previous entry
    End_blink = constructor ('time')

    # Subject response
    Response = constructor ('time')

    # Trial features
    Experiment_variables = constructor ('time', 'variables')

    Start_trial = constructor('time', 'trial_number', 'stimulus')
    Stop_trial = constructor ('time')

    def __str__(self):
        return entry_to_string(self)

    def check(self) -> None:
        return checkEntry(self)

    def getTime(self) -> int:
        return getTime(self)

    def getGazePosition(self):
        return getGazePosition(self)

@match(Entry)
class entry_to_string(object):
    def Position(time, x, y): return '%i %f %f' % (time, x, y)
    def Start_fixation(time): return 'Start Fixation at %i' % time
    def End_fixation(time): return 'End Fixation at %i' % time

    def Start_saccade(time): return 'Start Saccade at %i' % time
    def End_saccade(time): return 'End Saccade at %i' % time

    def Start_blink(time): return 'Start Blink at %i' % time
    def End_blink(time): return 'End Blink at %i' % time

    def Response(time): return 'Response at %i' % time

    def Experiment_variables(time, variables): return 'Variables at %i: %s' % (time, str(variables))

    def Start_trial(time, trial_number, stimulus): return 'Start Trial number %i at %i: %s' % (trial_number, time, stimulus)
    def Stop_trial(time): return 'Stop Trial at %i' % time

# Checks if attributes of each constructor have correct types
@match(Entry)
class checkEntry(object):
    def Position(time, x, y):
        if type(time) != int: raise EntryException('Time of Position is not int')
        if type(x) != float: raise EntryException('Coordinate x at time %i is not float' % time)
        if type(y) != float: raise EntryException('Coordinate y at time %i is not float' % time)

    def Start_fixation(time):
        if type(time) != int: raise EntryException('Time of Start_fixation is not int')
    def End_fixation(time):
        if type(time) != int: raise EntryException('Time of End_fixation is not int')

    def Start_saccade(time):
        if type(time) != int: raise EntryException('Time of Start_saccade is not int')
    def End_saccade(time):
        if type(time) != int: raise EntryException('Time of End_saccade is not int')

    def Start_blink(time):
        if type(time) != int: raise EntryException('Time of Start_blink is not int')
    def End_blink(time):
        if type(time) != int: raise EntryException('Time of End_blink is not int')

    def Response(time):
        if type(time) != int: raise EntryException('Time of Response is not int')

    # TODO: tester features
    def Experiment_variables(time, variables):
        if type(time) != int: raise EntryException('Time of Features is not int')

    def Start_trial(time, trial_number, stimulus):
        if type(time) != int: raise EntryException('Time of Start_trial is not int')
        if type(trial_number) != int: raise EntryException('Trial_number of Start_trial is not int')
        if type(stimulus) != str: raise EntryException('Stimulus of Start_trial is not str')
    def Stop_trial(time):
        if type(time) != int: raise EntryException('Time of Stop_trial is not int')

@match(Entry)
class getTime(object):
    def Position(time, x, y): return time
    def Start_fixation(time): return time
    def End_fixation(time): return time
    def Start_saccade(time): return time
    def End_saccade(time): return time
    def Start_blink(time): return time
    def End_blink(time): return time
    def Response(time): return time
    def Experiment_variables(time, variables): return time
    def Start_trial(time, trial_number, stimulus): return time
    def Stop_trial(time): return time

@match(Entry)
class getGazePosition(object):
    def Position(time, x, y): return (x,y)
    def _(_): return None

class EntryListException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class EntryList:
    entries = []

    def __init__(self, entries):
        self.entries = entries
        self.check()

    def duration(self) -> int:
        if len(self.entries) == 0:
            return 0
        return self.entries[len(self.entries)-1].getTime() - self.entries[0].getTime()

    def checkTimes(self) -> None:
        n = len(self.entries)
        # Time must increase for all lines except the first and last ones.
        for i in range(1,n-3):
            if getTime(self.entries[i]) > getTime(self.entries[i+1]):
                raise EntryListException('Time is decreasing between %s and %s' % (str(self.entries[i]), str(self.entries[i+1])))

        # The first line must give the time of the second one
        if self.entries[0].getTime() != self.entries[1].getTime():
             raise EntryListException('Incorrect time for the first line %s' % str(self.entries[0]))

        # The last line must give the time of the prevous one
        if self.entries[n-1].getTime() != self.entries[n-2].getTime():
             raise EntryListException('Incorrect time for the last line %s' % str(self.entries[n-1]))

    def check(self) -> None:
        pass

class FixationException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class Fixation(EntryList):

    entries = []

    def __str__(self):
        return 'Fixation: %i' % self.duration()

    def check(self) -> None:
        @match(Entry)
        class checkStart(object):
            def Start_fixation(_): pass
            def _(_): raise FixationException('First entry is not a start fixation')
        @match(Entry)
        class checkEnd(object):
            def End_fixation(_): pass
            def _(_): raise FixationException('Last entry is not a stop fixation')

        self.checkTimes()
        checkStart(self.entries[0])
        checkEnd(self.entries[len(self.entries) - 1])

class SaccadeException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class Saccade(EntryList):

    entries = []

    def __str__(self):
        return 'Saccade: %i' % self.duration()

    def check(self) -> None:
        @match(Entry)
        class checkStart(object):
            def Start_saccade(_): pass
            def _(_): raise SaccadeException('First entry is not a start saccade: %s' % str(self))
        @match(Entry)
        class checkEnd(object):
            def End_saccade(_): pass
            def _(_): raise SaccadeException('Last entry is not a stop saccade')

        self.checkTimes()
        checkStart(self.entries[0])
        checkEnd(self.entries[len(self.entries) - 1])

class BlinkException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class Blink(EntryList):

    entries = []

    def __str__(self):
        return 'Blink: %i' % self.duration()

    def check(self) -> None:
        @match(Entry)
        class checkStart(object):
            def Start_blink(_): pass
            def _(_): raise BlinkException('First entry is not a start blink: %s' % str(self))
        @match(Entry)
        class checkEnd(object):
            def End_blink(_): pass
            def _(_): raise BlinkException('Last entry is not a stop blink')

        # À corriger
        #self.checkTimes()
        checkStart(self.entries[0])
        checkEnd(self.entries[len(self.entries) - 1])
