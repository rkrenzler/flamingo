#pipeTools dialogs
#(c) 2016 Riccardo Treu LGPL

import FreeCAD,FreeCADGui,csv
import frameCmd, pipeCmd
from frameForms import prototypeForm
from os import listdir
from os.path import join, dirname, abspath
from PySide.QtCore import *
from PySide.QtGui import *

class protopypeForm(QWidget):
  'prototype dialog for insert pipeFeatures'
  def __init__(self,winTitle='Title', PType='Pipe', PRating='SCH-STD'):
    '''
    __init__(self,winTitle='Title', PType='Pipe', PRating='SCH-STD')
      winTitle: the window's title
      PType: the pipeFeature type
      PRating: the pipeFeature pressure rating class
    It lookups in the directory ./tables the file PType+"_"+PRating+".csv",
    imports it's content in a list of dictionaries -> .pipeDictList and
    shows a summary in the QListWidget -> .sizeList
    Also create a property -> PRatingsList with the list of available PRatings for the 
    selected PType.   
    '''
    super(protopypeForm,self).__init__()
    self.move(QPoint(100,250))
    self.PType=PType
    self.PRating=PRating
    self.setWindowFlags(Qt.WindowStaysOnTopHint)
    self.setWindowTitle(winTitle)
    self.mainHL=QHBoxLayout()
    self.setLayout(self.mainHL)
    self.sizeList=QListWidget()
    self.sizeList.setMaximumWidth(120)
    self.sizeList.setCurrentRow(0)
    self.mainHL.addWidget(self.sizeList)
    self.pipeDictList=[]
    self.fileList=listdir(join(dirname(abspath(__file__)),"tables"))
    self.fillSizes()
    self.PRatingsList=[s.lstrip(PType+"_").rstrip(".csv") for s in self.fileList if s.startswith(PType)]
    self.secondCol=QWidget()
    self.secondCol.setLayout(QVBoxLayout())
    self.ratingList=QListWidget()
    self.ratingList.setMaximumWidth(120)
    self.ratingList.addItems(self.PRatingsList)
    self.ratingList.itemClicked.connect(self.changeRating)
    self.secondCol.layout().addWidget(self.ratingList)
    self.btn1=QPushButton('Insert')
    self.btn1.setDefault(True)
    self.btn1.setFocus()
    self.secondCol.layout().addWidget(self.btn1)
    self.mainHL.addWidget(self.secondCol)
  def fillSizes(self):
    self.sizeList.clear()
    for fileName in self.fileList:
      if fileName==self.PType+'_'+self.PRating+'.csv':
        f=open(join(dirname(abspath(__file__)),"tables",fileName),'r')
        reader=csv.DictReader(f,delimiter=';')
        self.pipeDictList=[DNx for DNx in reader]
        f.close()
        for row in self.pipeDictList:
          s=row['DN']
          if row.has_key('OD'):
            s+=" - "+row['OD']
          if row.has_key('thk'):
            s+="x"+row['thk']
          self.sizeList.addItem(s)
        break
  def changeRating(self,item):
    self.PRating=item.text()
    self.fillSizes()
    
class insertPipeForm(protopypeForm):
  def __init__(self):
    super(insertPipeForm,self).__init__("Insert pipes","Pipe","SCH-STD")
    self.btn1.clicked.connect(self.insert)
    self.edit1=QLineEdit(' <insert lenght>')
    self.edit1.setAlignment(Qt.AlignHCenter)
    self.secondCol.layout().addWidget(self.edit1)
    self.show()
  def insert(self):
    d=self.pipeDictList[self.sizeList.currentRow()]
    FreeCAD.activeDocument().openTransaction('Insert pipe')
    if len(frameCmd.edges())==0:
      try:
        H=float(self.edit1.text())
      except:
        H=200
      propList=[d['DN'],float(d['OD']),float(d['thk']),H]
      pipeCmd.makePipe(propList)
    else:
      for edge in frameCmd.edges():
        if edge.curvatureAt(0)==0:
          propList=[d['DN'],float(d['OD']),float(d['thk']),edge.Length]
          pipeCmd.makePipe(propList,edge.valueAt(0),edge.tangentAt(0))
        else:
          propList=[d['DN'],float(d['OD']),float(d['thk']),200]
          pipeCmd.makePipe(propList,edge.centerOfCurvatureAt(0),edge.tangentAt(0).cross(edge.normalAt(0)))
    FreeCAD.activeDocument().commitTransaction()
    FreeCAD.activeDocument().recompute()

class insertElbowForm(protopypeForm):
  def __init__(self):
    super(insertElbowForm,self).__init__("Insert elbows","Elbow","SCH-STD")
    self.btn1.clicked.connect(self.insert)
    self.edit1=QLineEdit('<insert angle>')
    self.edit1.setAlignment(Qt.AlignHCenter)
    self.secondCol.layout().addWidget(self.edit1)
    self.btn2=QPushButton('Trim')
    self.btn2.clicked.connect(self.trim)
    self.secondCol.layout().addWidget(self.btn2)
    self.show()
  def insert(self):
    d=self.pipeDictList[self.sizeList.currentRow()]
    try:
      ang=float(self.edit1.text())
      if ang>90:
        ang=90
    except:
      ang=float(d['BA'])
    selex=FreeCADGui.Selection.getSelectionEx()
    FreeCAD.activeDocument().openTransaction('Insert elbow')
    if len(selex)==0:     # insert one elbow at origin
      propList=[d['DN'],float(d['OD']),float(d['thk']),ang,float(d['BR'])]
      pipeCmd.makeElbow(propList)
    elif len(selex)==1 and len(selex[0].SubObjects)==1 and selex[0].SubObjects[0].ShapeType=="Vertex":   # insert one elbow on one vertex
      propList=[d['DN'],float(d['OD']),float(d['thk']),ang,float(d['BR'])]
      pipeCmd.makeElbow(propList,selex[0].SubObjects[0].Point)
    else:    # insert one elbow at intersection of two edges or "beams"
      axes=[] # selection of axes
      for objEx in selex:
        if len(frameCmd.beams([objEx.Object]))==1:
          axes.append(objEx.Object.Shape.Solids[0].CenterOfMass)
          axes.append(frameCmd.beamAx(objEx.Object))
        else:
          for edge in frameCmd.edges([objEx]):
            axes.append(edge.CenterOfMass)
            axes.append(edge.tangentAt(0))
      if len(axes)>=4:
        # get the position
        p1,v1,p2,v2=axes[:4]
        P=frameCmd.intersectionLines(p1,v1,p2,v2)
        if P!=None:
          w1=(P-p1)
          w1.normalize()
          w2=(P-p2)
          w2.normalize()
        else:
          FreeCAD.Console.PrintError('frameCmd.intersectionLines() has failed!\n')
          return None
        # calculate the bending angle and the plane fo the elbow
        from math import pi
        ang=180-w1.getAngle(w2)*180/pi # ..-acos(w1.dot(w2))/pi*180
        propList=[d['DN'],float(d['OD']),float(d['thk']),ang,float(d['BR'])]
        # create the feature
        elb=pipeCmd.makeElbow(propList,P,axes[1].cross(axes[3]))
        # mate the elbow ends with the pipes or edges
        b=frameCmd.bisect(w1*-1,w2*-1)
        elbBisect=frameCmd.beamAx(elb,FreeCAD.Vector(1,1,0))
        rot=FreeCAD.Rotation(elbBisect,b)
        elb.Placement.Rotation=rot.multiply(elb.Placement.Rotation)
    FreeCAD.activeDocument().commitTransaction()
    FreeCAD.activeDocument().recompute()
  def trim(self):
    if len(frameCmd.beams())==1:
      pipe=frameCmd.beams()[0]
      comPipeEdges=[e.CenterOfMass for e in pipe.Shape.Edges]
      eds=[e for e in frameCmd.edges() if not e.CenterOfMass in comPipeEdges]
      FreeCAD.activeDocument().openTransaction('Trim pipes')
      for edge in eds:
        frameCmd.extendTheBeam(frameCmd.beams()[0],edge)
      FreeCAD.activeDocument().commitTransaction()
    else:
      FreeCAD.Console.PrintError("Wrong selection\n")

class insertFlangeForm(protopypeForm):
  def __init__(self):
    super(insertFlangeForm,self).__init__("Insert flanges","Flange","DIN-PN16")
    self.btn1.clicked.connect(self.insert)
    self.show()
  def insert(self):
    d=self.pipeDictList[self.sizeList.currentRow()]
    propList=[d['DN'],d['FlangeType'],float(d['D']),float(d['d']),float(d['df']),float(d['f']),float(d['t']),int(d['n'])]
    FreeCAD.activeDocument().openTransaction('Insert flange')
    if len(frameCmd.edges())==0:
      pipeCmd.makeFlange(propList)
    else:
      for edge in frameCmd.edges():
        if edge.curvatureAt(0)!=0:
          pipeCmd.makeFlange(propList,edge.centerOfCurvatureAt(0),edge.tangentAt(0).cross(edge.normalAt(0)))
    FreeCAD.activeDocument().commitTransaction()
    FreeCAD.activeDocument().recompute()

class rotateForm(prototypeForm):
  '''
  dialog for rotateTheTubeAx()
  '''
  def __init__(self):
    super(rotateForm,self).__init__('rotateForm','Rotate','Reverse','90','Angle - deg:')
    self.btn1.clicked.connect(self.rotate)
    self.btn2.clicked.connect(self.reverse)
    self.vShapeRef = FreeCAD.Vector(0,0,1)
    self.shapeAxis=QWidget()
    self.shapeAxis.setLayout(QFormLayout())
    self.xval=QLineEdit("0")
    self.xval.setMinimumWidth(40)
    self.xval.setAlignment(Qt.AlignHCenter)
    self.xval.setMaximumWidth(60)
    self.shapeAxis.layout().addRow("Shape ref. axis - x",self.xval)
    self.yval=QLineEdit("0")
    self.yval.setMinimumWidth(40)
    self.yval.setAlignment(Qt.AlignHCenter)
    self.yval.setMaximumWidth(60)
    self.shapeAxis.layout().addRow("Shape ref. axis - y",self.yval)
    self.zval=QLineEdit("1")
    self.zval.setMinimumWidth(40)
    self.zval.setAlignment(Qt.AlignHCenter)
    self.zval.setMaximumWidth(60)
    self.shapeAxis.layout().addRow("Shape ref. axis - z",self.zval)    
    self.mainVL.addWidget(self.shapeAxis)
    self.btnGet=QPushButton("Get")
    self.btnGet.setDefault(True)
    self.btnX=QPushButton("-X-")
    self.btnGet.setDefault(True)
    self.btnY=QPushButton("-Y-")
    self.btnGet.setDefault(True)
    self.btnZ=QPushButton("-Z-")
    self.mainVL.addWidget(self.btnGet)
    self.buttons3=QWidget()
    self.buttons3.setLayout(QHBoxLayout())
    self.buttons3.layout().addWidget(self.btnX)
    self.buttons3.layout().addWidget(self.btnY)
    self.buttons3.layout().addWidget(self.btnZ)
    self.mainVL.addWidget(self.buttons3)
    self.btnX.clicked.connect(self.setX)
    self.btnY.clicked.connect(self.setY)
    self.btnZ.clicked.connect(self.setZ)
    self.btnGet.clicked.connect(self.getAxis)
    self.btnX.setMaximumWidth(40)
    self.btnY.setMaximumWidth(40)
    self.btnZ.setMaximumWidth(40)
    self.btn1.setMaximumWidth(180)
    self.btn2.setMaximumWidth(180)
    self.btnGet.setMaximumWidth(180)
    self.show()
  def rotate(self):
    if len(FreeCADGui.Selection.getSelection())>0:
      obj = FreeCADGui.Selection.getSelection()[0]
      self.vShapeRef=FreeCAD.Vector(float(self.xval.text()),float(self.yval.text()),float(self.zval.text()))
      FreeCAD.activeDocument().openTransaction('Rotate')
      if self.radio2.isChecked():
        FreeCAD.activeDocument().copyObject(FreeCADGui.Selection.getSelection()[0],True)
      pipeCmd.rotateTheTubeAx(obj,self.vShapeRef,float(self.edit1.text()))
      FreeCAD.activeDocument().commitTransaction()
  def reverse(self):
    if len(FreeCADGui.Selection.getSelection())>0:
      obj = FreeCADGui.Selection.getSelection()[0]
      FreeCAD.activeDocument().openTransaction('Reverse rotate')
      pipeCmd.rotateTheTubeAx(obj,self.vShapeRef,-2*float(self.edit1.text()))
      self.edit1.setText(str(-1*float(self.edit1.text())))
      FreeCAD.activeDocument().commitTransaction()
  def setX(self):
    if self.xval.text()=='1':
      self.xval.setText('-1')
    elif self.xval.text()=='0':
      self.xval.setText('1')
    else:
      self.xval.setText('0')
  def setY(self):
    if self.yval.text()=='1':
      self.yval.setText('-1')
    elif self.yval.text()=='0':
      self.yval.setText('1')
    else:
      self.yval.setText('0')
  def setZ(self):
    if self.zval.text()=='1':
      self.zval.setText('-1')
    elif self.zval.text()=='0':
      self.zval.setText('1')
    else:
      self.zval.setText('0')
  def getAxis(self):
    coord=[]
    selex=FreeCADGui.Selection.getSelectionEx()
    if len(selex)==1 and len(selex[0].SubObjects)>0:
      sub=selex[0].SubObjects[0]
      if sub.ShapeType=='Edge' and sub.curvatureAt(0)>0:  
        axObj=sub.tangentAt(0).cross(sub.normalAt(0))
        obj=selex[0].Object
    #elif[..]
    coord=list(pipeCmd.shapeReferenceAxis(obj,axObj))
    if len(coord)==3:
      self.xval.setText(str(coord[0]))
      self.yval.setText(str(coord[1]))
      self.zval.setText(str(coord[2]))

class rotateEdgeForm(prototypeForm):
  'dialog for rotateTheTubeEdge()'
  def __init__(self):
    super(rotateEdgeForm,self).__init__('rotateEdgeForm','Rotate','Reverse','90','Angle - deg:')
    self.btn1.clicked.connect(self.rotate)
    self.btn2.clicked.connect(self.reverse)
    self.show()
  def rotate(self):
    if len(FreeCADGui.Selection.getSelection())>0:
      FreeCAD.activeDocument().openTransaction('Rotate')
      if self.radio2.isChecked():
        FreeCAD.activeDocument().copyObject(FreeCADGui.Selection.getSelection()[0],True)
      pipeCmd.rotateTheTubeEdge(float(self.edit1.text()))
      FreeCAD.activeDocument().commitTransaction()
  def reverse(self):
    FreeCAD.activeDocument().openTransaction('Reverse rotate')
    pipeCmd.rotateTheTubeEdge(-2*float(self.edit1.text()))
    self.edit1.setText(str(-1*float(self.edit1.text())))
    FreeCAD.activeDocument().commitTransaction()
