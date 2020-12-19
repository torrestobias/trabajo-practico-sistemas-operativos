#!/usr/bin/env python
from concurrent.futures._base import RUNNING

from hardware import *
import log
from enum import Enum
import collections


## emulates a compiled program
##from practica_3.hardware import HARDWARE, INSTRUCTION_EXIT, ASM, IO_OUT_INTERRUPTION_TYPE, IO_IN_INTERRUPTION_TYPE, \
##    KILL_INTERRUPTION_TYPE


class Program():

    def __init__(self, name, instructions):
        self._name = name
        self._instructions = self.expand(instructions)

    @property
    def name(self):
        return self._name

    @property
    def instructions(self):
        return self._instructions

    def addInstr(self, instruction):
        self._instructions.append(instruction)

    def expand(self, instructions):
        expanded = []
        for i in instructions:
            if isinstance(i, list):
                ## is a list of instructions
                expanded.extend(i)
            else:
                ## a single instr (a String)
                expanded.append(i)

        ## now test if last instruction is EXIT
        ## if not... add an EXIT as final instruction
        last = expanded[-1]
        if not ASM.isEXIT(last):
            expanded.append(INSTRUCTION_EXIT)

        return expanded

    def __repr__(self):
        return "Program({name}, {instructions})".format(name=self._name, instructions=self._instructions)


## emulates an Input/Output device controller (driver)
class IoDeviceController():

    def __init__(self, device):
        self._device = device
        self._waiting_queue = []
        self._currentPCB = None

    def runOperation(self, pcb, instruction):
        pair = {'pcb': pcb, 'instruction': instruction}
        # append: adds the element at the end of the queue
        self._waiting_queue.append(pair)
        # try to send the instruction to hardware's device (if is idle)
        self.__load_from_waiting_queue_if_apply()

    def getFinishedPCB(self):
        finishedPCB = self._currentPCB
        self._currentPCB = None
        self.__load_from_waiting_queue_if_apply()
        return finishedPCB

    def __load_from_waiting_queue_if_apply(self):
        if (len(self._waiting_queue) > 0) and self._device.is_idle:
            ## pop(): extracts (deletes and return) the first element in queue
            pair = self._waiting_queue.pop(0)
            # print(pair)
            pcb = pair['pcb']
            instruction = pair['instruction']
            self._currentPCB = pcb
            self._device.execute(instruction)

    def __repr__(self):
        return "IoDeviceController for {deviceID} running: {currentPCB} waiting: {waiting_queue}".format(
            deviceID=self._device.deviceId, currentPCB=self._currentPCB, waiting_queue=self._waiting_queue)


## emulates the  Interruptions Handlers
class AbstractInterruptionHandler():
    def __init__(self, kernel):
        self._kernel = kernel

    @property
    def kernel(self):
        return self._kernel

    def execute(self, irq):
        log.logger.error("-- EXECUTE MUST BE OVERRIDEN in class {classname}".format(classname=self.__class__.__name__))


class NewInterruptionHandler(AbstractInterruptionHandler):
    def execute(self, irq):
        pid = PCBTable.getNewPID(self.kernel.pcbTable)
        program= irq.parameters[0]
        priority = irq.parameters[1]
        baseDir = self.kernel.loader.load(program)
        pcb = PCB(pid, baseDir,priority)
        self.kernel.pcbTable.add(pcb)
        if self.kernel.pcbTable.runningPCB == None:
            pcb.state = State.RUNNING
            self.kernel.pcbTable.runningPCB = pcb
            self.kernel.dispatcher.load(pcb)

        else:
            pcb.state = State.READY
            self.kernel.scheduler.add(pcb)


class KillInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        pcbFinalizado = self.kernel.pcbTable.runningPCB
        self.kernel.dispatcher.save(pcbFinalizado)
        pcbFinalizado.state.TERMINATED
        log.logger.info(" Program Finished ")

        if not self.kernel.scheduler.isEmpty():
            nextPCB = self.kernel.scheduler.getFirstElement()
            nextPCB.state.RUNNING
            self.kernel.dispatcher.load(nextPCB)
            self.kernel.pcbTable.runningPCB = nextPCB


class IoInInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        operation = irq.parameters
        pcb = self.kernel.pcbTable.runningPCB
        self.kernel.dispatcher.save(pcb)
        self.kernel.pcbTable.runningPCB = None
        pcb.state.WAITING
        self.kernel.ioDeviceController.runOperation(pcb, operation)
        log.logger.info(self.kernel.ioDeviceController)

        if not (self.kernel.scheduler.isEmpty()):
            nextPcb = self.kernel.scheduler.getFirstElement()
            self.kernel.dispatcher.load(nextPcb)
            nextPcb.state.RUNNING
            self.kernel.pcbTable.runningPCB = nextPcb


class IoOutInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        pcb = self.kernel.ioDeviceController.getFinishedPCB()

        if self.kernel.pcbTable.runningPCB == None:
            pcb.state.RUNNING
            self.kernel.pcbTable.runningPCB = pcb
            self.kernel.dispatcher.load(pcb)

        else:
            pcb.state.READY
            self.kernel.scheduler.addToReadyQueue(pcb)

        log.logger.info(self.kernel.ioDeviceController)


# emulates the core of an Operative System
class TimeoutInterruptionHandler(AbstractInterruptionHandler):
    def execute(self, irq):
        if not self.kernel.scheduler.isEmpty():
            pcbInCpu = self.kernel.pcbTable.runningPCB
            self.kernel.dispatcher.save(pcbInCpu)
            pcbInCpu.state= State.READY
            pcbToAdd = self.kernel.scheduler.getFirstElement()
            pcbToAdd.state = State.RUNNING
            self.kernel.pcbTable.runningPCB = pcbToAdd
            self.kernel.scheduler.add(pcbInCpu)
            self.kernel.dispatcher.load(pcbToAdd)
        else:
            HARDWARE.timer.reset()


class Kernel():

    def __init__(self):
        ## setup interruption handlers
        killHandler = KillInterruptionHandler(self)
        HARDWARE.interruptVector.register(KILL_INTERRUPTION_TYPE, killHandler)

        ioInHandler = IoInInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_IN_INTERRUPTION_TYPE, ioInHandler)

        ioOutHandler = IoOutInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_OUT_INTERRUPTION_TYPE, ioOutHandler)

        newHandler = NewInterruptionHandler(self)
        HARDWARE.interruptVector.register(NEW_INTERRUPTION_TYPE, newHandler)

        timeoutHandler = TimeoutInterruptionHandler(self)
        HARDWARE.interruptVector.register(TIMEOUT_INTERRUPTION_TYPE, timeoutHandler)
        ## controls the Hardware's I/O Device


        ## controls the Hardware's I/O Device
        self._ioDeviceController = IoDeviceController(HARDWARE.ioDevice)
        self._pcbTable = PCBTable()
        self._readyQueue = ReadyQueue()
        self._loader = Loader()
        self._ioDeviceController = IoDeviceController(HARDWARE.ioDevice)
        self._dispatcher = Dispatcher()
        self._kernel = self
        self._scheduler = Scheduler()


    @property
    def ioDeviceController(self):
        return self._ioDeviceController



    def load_program(self, program):
        # loads the program in main memory
        progSize = len(program.instructions)
        for index in range(0, progSize):
            inst = program.instructions[index]
            HARDWARE.memory.write(index, inst)


    ## emulates a "system call" for programs execution
    def run(self, program, prioridad):
        tuple = [program,prioridad]
        newIRQ = IRQ(NEW_INTERRUPTION_TYPE, tuple)
        HARDWARE.interruptVector.handle(newIRQ)
        log.logger.info("\n Executing program: {name}".format(name=program.name))
        log.logger.info(HARDWARE)
    def __repr__(self):
        return "Kernel "

    @property
    def pcbTable(self):
        return self._pcbTable

    @property
    def dispatcher(self):
        return self._dispatcher

    @property
    def loader(self):
        return self._loader

    @property
    def scheduler(self):
        return self._scheduler


    def setScheduler(self, scheduler):
        self._scheduler = scheduler
        scheduler.setKernel(self)



class PCBTable():

    def __init__(self):
        self._pcbTable = []
        self._runningPCB = None
        self._next = 0

    def get(self, pid):
        n = 0
        lista = self._pcbTable
        while n < len(self.pcbTable) or lista[n].pid != pid:
            n += 1
        if n < len(self.pcbTable):
            return lista[n]
        else:
            return None

    def add(self, pcb):
        self._pcbTable.append(pcb)

    def remove(self, pcb):
        self._pcbTable.remove(pcb)

    @property
    def runningPCB(self):
        return self._runningPCB

    @property
    def pcbTable(self):
        return self._pcbTable

    @runningPCB.setter
    def runningPCB(self, pcb):
        self._runningPCB = pcb

    def getNewPID(self):
        nuevaDireccion = self._next
        self._next += 1
        return nuevaDireccion


class Loader():

    def __init__(self):
        self._proxBaseDir = 0

    def load(self, program):
        # loads the program in main memory
        # program = irq.parameters
        baseDir = self._proxBaseDir
        progSize = len(program.instructions)

        for index in range(0, progSize):
            inst = program.instructions[index]
            HARDWARE.memory.write(self._proxBaseDir, inst)
            self._proxBaseDir += 1
        return baseDir

    @property
    def proxBaseDir(self):
        return self._proxBaseDir


class State(Enum):
    NEW = 0
    READY = 1
    RUNNING = 2
    WAITING = 3
    TERMINATED = 4


class PCB():

    def __init__(self, pid, baseDir,priority):
        self._pid = pid
        self._baseDir = baseDir
        self._pc = 0
        self._state = State.NEW
        self._path = ""
        self._priority = priority


    @property
    def priority(self):
        return self._priority

    @property
    def pid(self):
        return self._pid

    @property
    def baseDir(self):
        return self._baseDir

    @property
    def pc(self):
        return self._pc

    @property
    def state(self):
        return self._state

    @property
    def path(self):
        return self._path

    @pc.setter
    def pc(self, pc):
        self._pc = pc

    @state.setter
    def state(self, state):
        self._state = state


class Dispatcher():

    def load(self, pcb):
        HARDWARE.cpu.pc = pcb.pc
        HARDWARE.mmu.baseDir = pcb.baseDir
        HARDWARE.timer.reset()

    def save(self, pcb):
        pcb.pc = HARDWARE.cpu.pc
        HARDWARE.cpu.pc = -1


class ReadyQueue():

    def __init__(self):
        self._readyQueue = []

    def getFirstElement(self):
        return self._readyQueue.pop(0)

    def isEmpty(self):
        return len(self._readyQueue) == 0

    def addToReadyQueue(self, pcb):
        self._readyQueue.append(pcb)

    @property
    def readyQueue(self):
        return self._readyQueue

    @readyQueue.setter
    def readyQueue(self, rQ):
        self._readyQueue = rQ



class Scheduler():

    def __init__(self):
        self._readyQueue = ReadyQueue()
        self._kernel = None


    def add(self, pcb):
        self._readyQueue.addToReadyQueue(pcb)


    def getFirstElement(self):
        return self._readyQueue.getFirstElement()

    def getPrioritario(self):
        nro = 10
        pcbPrioritario = None
        queue = self.readyQueue.readyQueue
        for elem in queue:
            if(elem.priority <= nro):
                nro = elem.priority
                pcbPrioritario = elem

        self.readyQueue.readyQueue.remove(pcbPrioritario)
        return pcbPrioritario


    def isEmpty(self):
        return self._readyQueue.isEmpty()

    def mustExpropiate(self, pcbEnCPU, pcbAComparar):
        pass

    def prioritySorting(self):
        self.readyQueue.sort(key=lambda x: x.priority, reverse=True)

    def expropiate(self, pcbInCpu, pcbToAdd):
        self.kernel.dispatcher.save(pcbInCpu)
        pcbInCpu.state= State.READY
        pcbToAdd.state = State.RUNNING
        self.kernel.pcbTable.runningPCB = pcbToAdd
        self.kernel.scheduler.add(pcbInCpu)
        self.kernel.dispatcher.load(pcbToAdd)
        #self.kernel.scheduler.getFirstElement

    @property
    def kernel(self):
        return self._kernel

    @property
    def readyQueue(self):
        return self._readyQueue


    def setKernel(self,kernel):
        self._kernel = kernel

class FirstComeFirstServed(Scheduler):

    def mustExpropiate(self, pcbEnCPU, pcbAComparar):
        return False

class NonExpropiativePriority(Scheduler):
    def mustExpropiate(self, pcbEnCPU, pcbAComparar):
        return False

    def getFirstElement(self):
        return self.getPrioritario()



class ExpropiativePriority(Scheduler):

    def mustExpropiate(self, pcbEnCPU, pcbAComparar):
        return pcbAComparar.priority < pcbEnCPU.priority

    def add(self, pcbToAdd):

        pcbCpu= self._kernel.pcbTable.runningPCB

        if self.mustExpropiate(pcbCpu, pcbToAdd):
            self.expropiate(pcbCpu, pcbToAdd)

        else:
            super().add(pcbToAdd)

    def getFirstElement(self):
        return self.getPrioritario()

class RoundRobin(Scheduler):
    def __init__(self, quantum):
        super().__init__()
        HARDWARE.timer.quantum = quantum

    def mustExpropiate(self, pcbEnCPU, pcbAComparar):
        return False

