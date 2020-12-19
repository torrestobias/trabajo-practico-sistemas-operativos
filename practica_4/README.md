# Práctica 4
## Scheduler

Ahora que tenemos un sistema multiprogramación, necesitamos optimizar el uso del __CPU__.

Para esto vamos a tener que implementar algunos de los algoritmos de planificación de CPU que vimos en la teoría.



## Lo que tenemos que hacer es:


- __1:__ A partir de ahora vamos a usar el codigo de la práctica anterior como base de la actual.... hacer copy/paste del so.py de la practica anterior

- __2:__ Implementar el componente __Scheduler__ que será el encargado de administrar la __ready queue__. 


- __3:__ Implementar al menos estas variantes de scheduling :
  - FCFS
  - Priority no expropiativo 
  - Round Robin
  - Priority expropiativo 

  Nuestro sistema operativo se ejecutará con un solo Scheduler a la vez, pero es requerido que podamos intercambiarlo "en Frio", es decir, bajar el S.O., configurar el Scheduler y volver a levantar todo desde cero con el nuevo algoritmo de planificación 


- __4:__ __Deseable__: imprimir el diagrama de Gantt de la ejecucion actual 


__Nota__ Cuando implementen Priority, debemos extender el modelo de ejecucion y #NewHandler para recibir la priordad como parametro del run


```python
    prg1 = Program("prg1.exe", [ASM.CPU(2)])
    prg2 = Program("prg2.exe", [ASM.CPU(4)])
    prg3 = Program("prg3.exe", [ASM.CPU(3)])

    # execute all programs
    kernel.run(prg1, 1)  ## 1 = prioridad del proceso
    kernel.run(prg2, 2)  ## 2 = prioridad del proceso
    kernel.run(prg3, 3)  ## 3 = prioridad del proceso
```