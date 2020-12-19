from hardware import *
from so import *
import log


##
##  MAIN 
##
##from practica_4.hardware import *
##from practica_4.so import *

if __name__ == '__main__':
    log.setupLogger()
    log.logger.info('Starting emulator')

    ## setup our hardware and set memory size to 25 "cells"
    HARDWARE.setup(25)

    ## Switch on computer
    HARDWARE.switchOn()

    kernel = Kernel()
    ## new create the Operative System Kernel
    # "booteamos" el sistema operativo
    fifs = FirstComeFirstServed()

    noexpropiativo = NonExpropiativePriority()

    expropiativo = ExpropiativePriority()

    roundRobin = RoundRobin(3)

    kernel.setScheduler(roundRobin)

    # Ahora vamos a intentar ejecutar 3 programas a la vez
    ##################
    prg1 = Program("prg1.exe", [ASM.CPU(2)])
    prg2 = Program("prg2.exe", [ASM.CPU(4)])
    prg3 = Program("prg3.exe", [ASM.CPU(3)])
    # execute all programs#
    kernel.run(prg1, 1)
    ## 1 = prioridad del proceso
    kernel.run(prg2, 2)
    ## 2 = prioridad del proceso
    kernel.run(prg3, 3)
    ## 3 = prioridad del proceso
    # execute all programs "concurrently"

     ##HARDWARE.switchOn()



