from sumtypes import sumtype, match, constructor
from typing import Tuple, TypeVar, Union
import math, random
from eyetracking.utils import *

class EntryException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

# Type for entries
Entry = TypeVar('Entry')

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

    # Message
    Message = constructor ('time', 'message')

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
    def Position(time, x, y): return '%i\t%f\t%f' % (time, x, y)
    def Start_fixation(time): return 'Start Fixation at %i' % time
    def End_fixation(time): return 'End Fixation at %i' % time

    def Start_saccade(time): return 'Start Saccade at %i' % time
    def End_saccade(time): return 'End Saccade at %i' % time

    def Start_blink(time): return 'Start Blink at %i' % time
    def End_blink(time): return 'End Blink at %i' % time

    def Response(time): return 'Response at %i' % time

    def Message(time, message): return '%s at %i' % (message, time)

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

    def Message(time, message):
        if type(message) != str: raise EntryException('Message is not string')
        if type(time) != int: raise EntryException('Time of %s is not int' % message)

    # TODO: tester features
    def Experiment_variables(time, variables):
        if type(time) != int: raise EntryException('Time of Features is not int')

    def Start_trial(time, trial_number, stimulus):
        if type(time) != int: raise EntryException('Time of Start_trial is not int')
        if type(trial_number) != int: raise EntryException('Trial_number of Start_trial is not int')
        if type(stimulus) != str: raise EntryException('Stimulus of Start_trial is not str')
    def Stop_trial(time):
        if type(time) != int: raise EntryException('Time of Stop_trial is not int')

# Returns the entry time (integer value)
# The time is given in ms.
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
    def Message(time, message): return time
    def Experiment_variables(time, variables): return time
    def Start_trial(time, trial_number, stimulus): return time
    def Stop_trial(time): return time

@match(Entry)
class getGazePosition(object):
    def Position(time, x, y) -> Point: return (x,y)
    def _(_): return None

class EntryListException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class EntryList:

    ENTRYLISTEXCEPTION_WARNING = True

    def __init__(self, trial, begin, end):
        # Begin is the index of the first line, and end the index of the last line.
        self.trial = trial
        self.begin = begin
        self.end = end

    def __str__(self):
        return 'EntryList starting at %i' % self.getStartTime()

    def entries_to_string(self):
        return '\n'.join([str(self.getEntry(i_line)) for i_line in range(self.begin, self.end)])

    def getBegin(self) -> int:
        return self.begin

    def getEnd(self) -> int:
        return self.end

    def getStartTime(self) -> int:
        return self.getEntry(self.getBegin()).getTime()

    def getEndTime(self) -> int:
        return self.getEntry(self.getEnd()).getTime()

    def getEntry(self, line : int) -> Entry:
        if line <= self.end and line >= self.begin:
            return self.trial.entries[line]
        else:
            raise EntryListException('Index %i out of bound' % line)

    def getFirstGazePosition(self) -> Union[Point, None]:
        for i in range(self.begin + 1, self.end - 1):
            p = getGazePosition(self.getEntry(i))
            if p != None:
                return p
        return None

    def getLastGazePosition(self) -> Union[Point, None]:
        for i in reversed(range(self.begin + 1, self.end - 1)):
            p = getGazePosition(self.getEntry(i))
            if p != None:
                return p
        return None

    def duration(self) -> int:
        if self.begin == None or self.end == None:
            return 0
        return self.getEntry(self.getEnd()).getTime() - self.getEntry(self.getBegin()).getTime()

    def raiseException(self, e):
        if self.ENTRYLISTEXCEPTION_WARNING:
            logTrace(str(e), Precision.ERROR)
        else:
            raise e

    def checkTimes(self) -> None:
        # Time must increase for all lines except the first and last ones.
        for i in range(self.begin+1, self.end-2):
            if self.getEntry(i).getTime() > self.getEntry(i+1).getTime():
                self.raiseException(
                    EntryListException(
                        'Time is decreasing between %s and %s' % (
                            str(self.getEntry(i)),
                            str(self.getEntry(i+1))
                        )
                    )
                )

        # The first line must give the time of the second one
        if (self.getEntry(self.begin+1).getTime() - self.getEntry(self.begin).getTime()) > 2 :
            self.raiseException(
                EntryListException('Incorrect time for the first line: %s' % self.entries_to_string())
            )

        # The last line must give the time of the prevous one
        if (self.getEntry(self.end).getTime() - self.getEntry(self.end-1).getTime()) > 2:
            self.raiseException(
                EntryListException('Incorrect time for the last line %s' % str(self.getEntry(self.end)))
            )
            #logTrace ('Incorrect time for the last line %s' % str(self.getEntry(self.end)), Precision.ERROR)

    def check(self) -> None:
        pass

    def barycentre(self) -> Point:
        i_line = self.begin
        counter = 0
        # We look for the first point
        while i_line <= self.end and self.getEntry(i_line).getGazePosition() == None:
            i_line += 1
        if i_line <= self.end:
            (x,y) = self.getEntry(i_line).getGazePosition()
            counter = 1
            i_line += 1
        while i_line <= self.end:
            if self.getEntry(i_line).getGazePosition() != None:
                (x2,y2) = self.getEntry(i_line).getGazePosition()
                x += x2
                y += y2
                counter += 1
            i_line += 1

        return (x / counter, y / counter)

class FixationException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class Fixation(EntryList):

    def __init__(self, trial, begin, end):
        super().__init__(trial, begin, end)
        self.check()
        self.checkTimes()

    def __str__(self):
        return 'Fixation starting at %i, ending at %i' % (self.getStartTime(), self.getEndTime())

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
        checkStart(self.getEntry(self.begin))
        checkEnd(self.getEntry(self.end))

class SaccadeException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class Saccade(EntryList):

    def __init__(self, trial, begin, end):
        super().__init__(trial, begin, end)
        self.check()
        self.checkTimes()

    def __str__(self):
        return 'Saccade: duration %i, starting at %i, trial %i' % (self.duration(), self.begin, self.trial.getTrialId())

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
        checkStart(self.getEntry(self.begin))
        checkEnd(self.getEntry(self.end))

class BlinkException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class Blink(EntryList):

    def __init__(self, trial, begin, end):
        super().__init__(trial, begin, end)
        self.check()
        # times are not checked for blinks

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
        checkStart(self.getEntry(self.begin))
        checkEnd(self.getEntry(self.end))

def k_clusters(entries, k, means = None, epsilon = 0.5):
    print('k_clusters')
    def norm(e1, e2):
        (x1,y1) = e1.getGazePosition()
        (x2,y2) = e2.getGazePosition()
        return math.sqrt((x2-x1)*(x2-x1) + (y2-y1)*(y2-y1))

    def i_min(l):
        i = 0
        min = l[0]
        for j in range(len(l)):
            if l[j] < min:
                min = l[j]
                i = j
        return i

    if means == None:
        # Initialization
        means = []
        for i in range(k):
            mean = random.randint(0,len(entries))
            while mean in means:
                mean = random.randint(0,len(entries))
            means.append(mean)
        means = [entries[i_mean] for i_mean in means]
    else:
        if k != len(means):
            raise "K clusters: means length is not k"

    while True:
        print(means)
        clusters = [[] for i in range(k)]
        for entry in entries:
            norms = [norm(mean, entry) for mean in means]
            clusters[i_min(norms)].append(entry)

        # Computing new means
        new_means = []
        for i in range(k):
            mean = [0.0,0.0]
            for entry in clusters[i]:
                mean[0] += entry.getGazePosition()[0]
                mean[1] += entry.getGazePosition()[1]
            new_means.append(Entry.Position(0.0,
                mean[0] / len(clusters[i]),
                mean[1] / len(clusters[i])
            ))

        stop = True
        for i in range(k):
            if norm(new_means[i], means[i]) > epsilon:
                stop = False
                break
        if stop:
            break
        else:
            means = new_means

    return means
