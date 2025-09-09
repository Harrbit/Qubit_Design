# Interposer PCB Design

To design a PCB, we can use Altium Designer software, here the introduction of designing process is based on Altium Designer version 25.6.2

---

## General Steps

Define you PCB footprint（the geometry and layer of wirebond launchpad;

Arrange the components on the schematic(define the network);

Define PCB layer stack;

Updadte the PCB schematic;

Define signal lines;

Add via fencing;

S-param simulation;

Fabricate.

---

Below is a more detailed description of the procedure.

---

## Step 1, Define PCB footprint

It is very likely the wirebond launchpad and connector are not standard issued universal parts. In order to correctly describe the geometry and layering of these components, we need to define them ahead of time.

To do this, we need to do define two things: the schematic symbol and the PCB footprint. The first is used for creating a 'net' that will be useful when adding via fencing using the automated tool built-in in Altium Designer. We'll get to this later, right now what you need to do is watch this youtube video and create a schematic simbol for your wirebond launchpad and connector: https://www.youtube.com/watch?v=9vEEEaegH90

After watching this video, you are able to make schematic symbols to logically present the elements, now define physical elements, PCB footprint, and map them to the schematic symbols so that we can continue to making PCB designs, to learn how to do this please watch this youtube video: https://www.youtube.com/watch?v=pNEjjspZpNg

After these two videos you will be ready to do the following:
define all the pads and connectors in your design, plan the layout first in schematic file, then update your PCB file from your schematic design(Design-update PCB document ***.PcbDoc).
