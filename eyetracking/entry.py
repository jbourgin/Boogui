from typing import Tuple, TypeVar, Union
import math, random
from eyetracking.utils import *

class EntryException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class Entry:
    def __init__(self, time):
        self.time = time

    def __str__(self) -> str:
        return "%i\t%s" % (self.time, self.__class__.__name__)

    def check(self) -> None:
        if type(self.time) != int:
            raise EntryException('Time of Start_fixation is not int')

    def getGazePosition(self):
        return None

    def getTime(self) -> int:
        return self.time

class StartFixation(Entry):
    "Fixation begins on the next entry"

class EndFixation(Entry):
    "Fixation ended at the previous entry"

class StartSaccade(Entry):
    "Saccade begins at the next entry"

class EndSaccade(Entry):
    "Saccade ended at the previous entry"

class StartBlink(Entry):
    "Blink begins at the next entry"

class EndBlink(Entry):
    "Blink ended at the previous entry"

class Response(Entry):
    "Subject Response"

class Position(Entry):
    # (x,y) : gaze position at the given time
    def __init__(self, time: int, x: float, y: float):
        super().__init__(time)
        self.x = x
        self.y = y

    def getGazePosition(self) -> Point:
        return (self.x, self.y)

    def check(self) -> None:
        super().check()
        if type(self.x) != float:
            raise EntryException('Coordinate x at time %i is not float' % time)
        if type(self.y) != float:
            raise EntryException('Coordinate y at time %i is not float' % time)

    def __str__(self):
        return '%i\t%f\t%f' % (self.time, self.x, self.y)

class Message(Entry):
    def __init__(self, time, message: str):
        super().__init__(time)
        self.message = message

    def check(self) -> None:
        super().check()
        if type(self.message) != str:
            raise EntryException('Message is not string')

    def __str__(self):
        return '%i\t%s' % (self.time, self.message)

class TrialFeatures(Entry):
    #
    def __init__(self, time, features):
        super().__init__(time)
        self.features = features

    def __str__(self):
        return '%i\t%s' % (self.time, str(self.features))

class StartTrial(Entry):
    # (x,y) : gaze position at the given time
    def __init__(self, time, trial_number: int, stimulus: str):
        super().__init__(time)
        self.trial_number = trial_number
        self.stimulus = stimulus

    def check(self) -> None:
        super().check()
        if type(self.trial_number) != int:
            raise EntryException('Trial_number of Start_trial is not int')
        if type(self.stimulus) != str:
            raise EntryException('Stimulus of Start_trial is not str')

    def __str__(self):
        return '%i\tStart Trial %i\t%s' % (self.time, self.trial_number, self.stimulus)

class StopTrial(Entry):
    "Stop Trial"

class EntryListException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class EntryList:

    ENTRYLISTEXCEPTION_WARNING = True

    def __init__(self, trial: "Trial", begin: int, end: int):
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

    def getStartTimeFromStartTrial(self) -> int:
        return self.getStartTime() - self.trial.getStartTrial().getTime()

    def getEndTimeFromStartTrial(self) -> int:
        return self.getEndTime() - self.trial.getStartTrial().getTime()

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
            p = self.getEntry(i).getGazePosition()
            if p != None:
                return p
        return None

    def getLastGazePosition(self) -> Union[Point, None]:
        for i in reversed(range(self.begin + 1, self.end - 1)):
            p = self.getEntry(i).getGazePosition()
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

    def checkLength(self) -> None:
        if self.end - self.begin <= 1:
            raise EntryListException("Entry list is too short")

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

    def merge(self, reg2):
        self.end = reg2.end

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

    def __init__(self, trial, begin = None, end = None):
        super().__init__(trial, begin, end)

    def __str__(self):
        return 'Fixation starting at %i, ending at %i' % (self.getStartTime(), self.getEndTime())

    def check(self) -> None:
        self.checkLength()
        self.checkTimes()
        if not isinstance(self.getEntry(self.begin), StartFixation):
            raise FixationException('First entry is not a start fixation')
        if not isinstance(self.getEntry(self.end), EndFixation):
            raise FixationException('Last entry is not a stop fixation')

class SaccadeException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class Saccade(EntryList):

    def __init__(self, trial, begin, end):
        super().__init__(trial, begin, end)

    def __str__(self):
        return 'Saccade: duration %i, starting at %i, trial %i' % (self.duration(), self.begin, self.trial.getTrialId())

    def check(self) -> None:
        self.checkLength()
        self.checkTimes()
        if not isinstance(self.getEntry(self.begin), StartSaccade):
            raise SaccadeException('First entry is not a start saccade')
        if not isinstance(self.getEntry(self.end), EndSaccade):
            raise SaccadeException('Last entry is not a stop saccade')

class BlinkException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class Blink(EntryList):

    def __init__(self, trial, begin, end):
        super().__init__(trial, begin, end)
        # times are not checked for blinks

    def __str__(self):
        return 'Blink: %i' % self.duration()

    def isBlinkValid(self):
        return self.duration() >= 50

    def check(self) -> None:
        # À corriger
        #self.checkTimes()
        if not isinstance(self.getEntry(self.begin), StartBlink):
            raise BlinkException('First entry is not a start blink')
        if not isinstance(self.getEntry(self.end), EndBlink):
            raise BlinkException('Last entry is not a stop blink')

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
        clusters = [[] for i in range(k)]
        for entry in entries:
            norms = [norm(mean, entry) for mean in means]
            clusters[i_min(norms)].append(entry)

        # Computing new means
        new_means = []
        for i in range(k):
            if len(clusters[i]) == 0:
                continue
            mean = [0.0,0.0]
            for entry in clusters[i]:
                mean[0] += entry.getGazePosition()[0]
                mean[1] += entry.getGazePosition()[1]
            new_means.append(Position(0.0,
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
