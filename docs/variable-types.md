> **NOTE:** _As of this documentation being created, Behavior Graphs are undergoing rapid development. This has the effect of making it challenging to update this documentation quickly enough to make sure it has parity with the current state of the tech behind it. Thank you for your patience and please consider contributing edits to this documentation as needed._

- [Intro to Behavior Graphs](./intro-behavior-graphs.md)
- [List of Flow Nodes](./nodes-flow.md)
- [List of Event Nodes](./nodes-event.md)
- [List of Animation Nodes](./nodes-animation.md)
- Variable Types

---
# Variable Types

Variables are an abstract form of storing information that can be passed between nodes via sockets. Hubs Behavior Graphs support different **Variable Types** that can be distinguished by the color coding of sockets and connections.
Some variable types can be connected to sockets of another type, like for example a boolean socket can be connected to an integer one. In that case a conversion node will be automatically placed inbetween.

## Boolean
![Boolean Pale Purple](img/BG-VarTypes_Boolean.png)

The pale purple **Boolean** variable type has only two states and can either be **True** or **False**. True can also be interpreted as **1** and false as **0** which means you can use booleans with the math nodes.

## Integer
![Integer Dark Green](img/BG-VarTypes_Integer.png)

The dark green **Integer** variable type represents whole numbers and can also be negative. It is often used for counting or indexing.

## Float
![Float Gray](img/BG-VarTypes_Float.png)

The gray **Float** variable type is the one most commonly used in computer graphics, usually in single precision with 32 bit.. It represents number with a decimal point like 1.234 or -123.4. 
The variable types **Color** and **Vector3** are both internally three floats combined.

## Vector3 or Euler

![Vector3 Purple](img/BG-VarTypes_Vector3.png)

The purple **Vector3** or **Euler** variable types combine three **Float** variables into a special type that comes in handy when doing operations in 3D space. Beware that Vector3 and Euler cannot be interconnected even though they use the same color for sockets and connections. Vector3 is used for location and scale, Euler for rotation.

## Color

![Color Yellow](img/BG-VarTypes_Color.png)

The yellow **Color** variable type is storing color information as three floats with the first one for the Red channel, the second one for the green channel and the third one for the blue channel (**RGB**). 

## String
![String Sky Blue](img/BG-VarTypes_String.png)

The sky blue **String** variable type stores a sequences of characters or in other words a text. 

## Material

![Material Pale Red](img/BG-VarTypes_Material.png)

The pale red **Material** variable type stores information about the shading of a surface, which in Blender and others contexts is called a material.

## AnimationAction

![AnimationAction Cyan](img/BG-VarTypes_AnimationAction.png) 

The cyan **AnimationAction** variable type stores so called **Actions** which in turn contain an **Animation**. An Animation is a definition how properties or entities change over time like for example the movement of a door that is opening. Beware that AnimationActions need to be created from Blender actions using the **CreateAnimationAction** node.

## Entity

![Entity Green](img/BG-VarTypes_Entity.png)

The green **Entity** variable type stores an entity which normally corresponds to a Blender object. 

## Player

![Player Light Yellow](img/BG-VarTypes_Player.png)

The light yellow **Player** variable type stores information about a user in the room like position, rotation, head transform or permissions. 

[Back to the Intro to Behavior Graphs](./intro-behavior-graphs.md)