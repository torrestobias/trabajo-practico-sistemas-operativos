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

    kernel = Kernel(4)
    ## new create the Operative System Kernel
    # "booteamos" el sistema operativo
    fifs = FirstComeFirstServed()

    #noexpropiativo = NonExpropiativePriority()

    #expropiativo = ExpropiativePriority()

    #roundRobin = RoundRobin(3)

    kernel.setScheduler(fifs)



    prg1 = Program("c:/prg1.exe", [ASM.CPU(3)])
    prg2 = Program("c:/prg2.exe", [ASM.CPU(4)])
    prg3 = Program("c:/prg3.exe", [ASM.CPU(3)])
    
    
    kernel.fileSystem.write("c:/prg1.exe", prg1)
    kernel.fileSystem.write("c:/prg2.exe", prg2)
    kernel.fileSystem.write("c:/prg3.exe", prg3)
    

    # execute all programs "concurrently"
    kernel.run("c:/prg1.exe", 1)
    kernel.run("c:/prg2.exe", 3)
    kernel.run("c:/prg3.exe", 4)
    



   