"""
pipeTools workbench
(c) 2016 Riccardo Treu LGPL
"""

# import FreeCAD modules
import FreeCAD, FreeCADGui,inspect, os

# helper -------------------------------------------------------------------
# FreeCAD TemplatePyMod module  
# (c) 2007 Juergen Riegel LGPL

def addCommand(name,cmdObject):
	(list,num) = inspect.getsourcelines(cmdObject.Activated)
	pos = 0
	# check for indentation
	while(list[1][pos] == ' ' or list[1][pos] == '\t'):
		pos += 1
	source = ""
	for i in range(len(list)-1):
		source += list[i+1][pos:]
	FreeCADGui.addCommand(name,cmdObject,source)

#---------------------------------------------------------------------------
# The command classes
#---------------------------------------------------------------------------

class insertPipe:
  def Activated (self):
    import pipeForms
    pipeFormObj=pipeForms.insertPipeForm()
  def GetResources(self):
    return{'Pixmap':os.path.join(os.path.dirname(os.path.abspath(__file__)),"icons","pipe.svg"),'MenuText':'Insert a tube','ToolTip':'Insert a tube'}

class insertElbow: 
  def Activated (self):
    import pipeForms
    pipeFormObj=pipeForms.insertElbowForm()
  def GetResources(self):
    return{'Pixmap':os.path.join(os.path.dirname(os.path.abspath(__file__)),"icons","elbow.svg"),'MenuText':'Insert a curve','ToolTip':'Insert a curve'}

class insertFlange:
  def Activated (self):
    import pipeForms
    pipeFormObj=pipeForms.insertFlangeForm()
  def GetResources(self):
    return{'Pixmap':os.path.join(os.path.dirname(os.path.abspath(__file__)),"icons","flange.svg"),'MenuText':'Insert a flange','ToolTip':'Insert a flange'}

class tank:
  def Activated (self):
    import pipeCmd
    from PySide import QtGui as qg
    thk=float(qg.QInputDialog.getText(None,"make a shell out of a solid","Shell thickness (mm):")[0])
    pipeCmd.makeTank(thk)
  def GetResources(self):
    return{'Pixmap':'python','MenuText':'Create tank','ToolTip':'Create a tank shell from an existing object'}

class rotateAx:
  def Activated (self):
    import pipeForms
    pipeFormObj=pipeForms.rotateForm()
  def GetResources(self):
    return{'Pixmap':os.path.join(os.path.dirname(os.path.abspath(__file__)),"icons","rotateAx.svg"),'MenuText':'Rotate through axis','ToolTip':'Rotate an object around an axis of its Shape'}

class rotateEdge:
  def Activated (self):
    import pipeForms
    pipeFormObj=pipeForms.rotateEdgeForm()
  def GetResources(self):
    return{'Pixmap':os.path.join(os.path.dirname(os.path.abspath(__file__)),"icons","rotateEdge.svg"),'MenuText':'Rotate through edge','ToolTip':'Rotate an object around the axis of a circular edge'}

class mateEdges:
  def Activated (self):
    import pipeCmd
    FreeCAD.activeDocument().openTransaction('Mate')
    pipeCmd.alignTheTube()
    FreeCAD.activeDocument().commitTransaction()
    FreeCAD.activeDocument().recompute()
  def GetResources(self):
    return{'Pixmap':os.path.join(os.path.dirname(os.path.abspath(__file__)),"icons","mate.svg"),'MenuText':'Mate pipes edges','ToolTip':'Mate two terminations through their edges'}

class flat:
  def Activated (self):
    import pipeCmd, frameCmd
    if len(frameCmd.beams())>=2:
      p1,p2=[b.Placement.Base for b in frameCmd.beams()[:2]]
      v1,v2=[frameCmd.beamAx(b) for b in frameCmd.beams()[:2]]
      fittings=[o for o in FreeCADGui.Selection.getSelection() if hasattr(o,'PType') and (o.PType=='Elbow' or o.PType=='Flange')]
      if len(fittings)>0:
        FreeCAD.activeDocument().openTransaction('Flatten')
        pipeCmd.flattenTheTube(fittings[0],v1,v2)
        fittings[0].Placement.Base=frameCmd.intersectionLines(p1,v1,p2,v2)
        FreeCAD.activeDocument().commitTransaction()
    FreeCAD.activeDocument().recompute()
  def GetResources(self):
    return{'Pixmap':os.path.join(os.path.dirname(os.path.abspath(__file__)),"icons","flat.svg"),'MenuText':'Put in the plane','ToolTip':'Put the selected component in the plane defined by 2 axis'}

class extend2intersection:
  def Activated (self):
    import pipeCmd
    FreeCAD.activeDocument().openTransaction('Xtend2int')
    pipeCmd.extendTheTubes2intersection()
    FreeCAD.activeDocument().commitTransaction()
    FreeCAD.activeDocument().recompute()
  def GetResources(self):
    return{'Pixmap':os.path.join(os.path.dirname(os.path.abspath(__file__)),"icons","intersect.svg"),'MenuText':'Extends pipes to intersection','ToolTip':'Extends pipes to intersection'}

#---------------------------------------------------------------------------
# Adds the commands to the FreeCAD command manager
#---------------------------------------------------------------------------
addCommand('insertPipe',insertPipe()) 
addCommand('insertElbow',insertElbow())
addCommand('insertFlange',insertFlange())
addCommand('mateEdges',mateEdges())
addCommand('rotateAx',rotateAx())
addCommand('rotateEdge',rotateEdge())
addCommand('flat',flat())
addCommand('extend2intersection',extend2intersection())
addCommand('tank',tank())
