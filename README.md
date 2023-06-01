# Series Elastic Actuation - FYP

This repo contains all code written for my Master's project on 'Series Elastic Actuation for High Bandwidth Force Control', submitted as part of my Mechanical Engineering degree at Imperial College London.

This code is not intended to be used for replication, although it may be used freely. The Arduino code makes up embedded C code running on two Arduino Unos interfacing with an RMD X8 V2 actuator and a magnetic encoder. The Python code contains all control software for interfacing with the Arduinos, as well as various processing and calibration scripts.

## Abstract

Series Elastic Actuators (SEAs) are a class of robotic actuator technologies that fly in the face of
conventional wisdom by purposefully reducing the stiffness of transmission through the introduction
of a spring. By exploiting the relationship between extension and force in a spring, this transforms
the actuator into a powerful force transducer. This project aims to test the implementation of SEA
in a previous under-explored field; by retrofitting one to an existing all-in-one actuator. Whereas
most previous implementations use highly performant components and accept the slight bandwidth
reduction in favour of the other control benefits, it is hypothesised that a bandwidth gain may be
possible for an original motor with relatively poor performance.
To test this hypothesis a target motor was chosen, and an SEA module was designed to be retrofitted
to it. A custom torsional spring was required, and through the aid of an FE study, a suitable
topology was designed resulting in a spring of stiffness 2155.4Nm/rad, a 5.65% discrepancy to
simulation. This was paired with a magnetic encoder, mounted to directly measure the deflection.
Communication was achieved with a micrcontroller interfacing with the various nodes over serial,
CAN and I2C achieving a sampling frequency of 603Hz. Finally a combined feedforward-feedback
control architecture was used, with modelling parameters measured using system identification.
The open-loop bandwidth was measured for the original motor and the SEA module, as well as
closed-loop bandwidth with feedback both from the SEA and the reference torque transducer, an
ATI Gamma. Bandwidth was increased by a factor of 2.93 from 10.32Hz to 30.32Hz. The SEA
even outperformed the ATI Gamma by 7.63%, demonstrating experimental results that support the
project hypothesis. Finally this was achieved at a manufacturing cost of around £25, a fraction of
the price of the ATI Gamma, presenting a high value force transducer.

![Series Elastic Actuator Proof of Concept Prototype](sea_final_image.png)