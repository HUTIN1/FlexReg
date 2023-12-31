import logging
import os
from functools import partial
from vtk.util.numpy_support import vtk_to_numpy
import vtk
# import sip

import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin


from qt import (QGridLayout,
                QHBoxLayout,
                QVBoxLayout,
                QCheckBox,
                QLabel,
                QLineEdit,
                QStackedWidget,
                QComboBox,
                QPushButton,
                QFileDialog,
                QWidget)


from Method.make_butterfly import butterflyPatch
from Method import ComputeNormals, drawPatch
#
# ButterfkyPatch
#

class ButterfkyPatch(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "ButterfkyPatch"  # TODO: make this more human readable by adding spaces
        self.parent.categories = ["Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#ButterfkyPatch">module documentation</a>.
"""
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#

def registerSampleData():
    """
    Add data sets to Sample Data module.
    """
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData
    iconsPath = os.path.join(os.path.dirname(__file__), 'Resources/Icons')

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # ButterfkyPatch1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='ButterfkyPatch',
        sampleName='ButterfkyPatch1',
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, 'ButterfkyPatch1.png'),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames='ButterfkyPatch1.nrrd',
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums='SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95',
        # This node name will be used when the data set is loaded
        nodeNames='ButterfkyPatch1'
    )

    # ButterfkyPatch2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='ButterfkyPatch',
        sampleName='ButterfkyPatch2',
        thumbnailFileName=os.path.join(iconsPath, 'ButterfkyPatch2.png'),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames='ButterfkyPatch2.nrrd',
        checksums='SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97',
        # This node name will be used when the data set is loaded
        nodeNames='ButterfkyPatch2'
    )


#
# ButterfkyPatchWidget
#

class ButterfkyPatchWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/ButterfkyPatch.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = ButterfkyPatchLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)
        self.ui.spinBoxnumberscan.valueChanged.connect(self.manageNumberWidgetScan)

        # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
        # (in the selected parameter node).


        # Make sure parameter node is initialized (needed for module reload)

        
        self.initializeParameterNode()


        self.number_widget_scan = 0
        self.list_widget_scan = []
        self.manageNumberWidgetScan(2)


    def manageNumberWidgetScan(self,number):
        print(f'manage number widget scan, number : {number}')
        while self.number_widget_scan != number :
            if number >= self.number_widget_scan :
                self.addWidgetScan()
                self.number_widget_scan += 1
            elif number <= self.number_widget_scan :
                self.removeWidgetScan()
                self.number_widget_scan -= 1


    def removeWidgetScan(self):
        mainwidgetscan = self.list_widget_scan.pop(-1).getMainWidget()
        mainwidgetscan.deleteLater()
        mainwidgetscan = None

    def addWidgetScan(self):
        self.list_widget_scan.append(WidgetParameter(self.ui.verticalLayout_2,self.parent))




    def cleanup(self):
        """
        Called when the application closes and the module widget is destroyed.
        """
        self.removeObservers()

    def enter(self):
        """
        Called each time the user opens this module.
        """
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self):
        """
        Called each time the user opens a different module.
        """
        # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
        self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    def onSceneStartClose(self, caller, event):
        """
        Called just before the scene is closed.
        """
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event):
        """
        Called just after the scene is closed.
        """
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self):
        """
        Ensure parameter node exists and observed.
        """
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.GetNodeReference("InputVolume"):
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.SetNodeReferenceID("InputVolume", firstVolumeNode.GetID())

    def setParameterNode(self, inputParameterNode):
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if inputParameterNode:
            self.logic.setDefaultParameters(inputParameterNode)

        # Unobserve previously selected parameter node and add an observer to the newly selected.
        # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
        # those are reflected immediately in the GUI.
        if self._parameterNode is not None:
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

        # Initial GUI update
        self.updateGUIFromParameterNode()

    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
        This method is called whenever parameter node is changed.
        The module GUI is updated to show the current state of the parameter node.
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True

        # Update node selectors and sliders
        self.ui.outputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolume"))
        self.ui.invertedOutputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolumeInverse"))
        self.ui.invertOutputCheckBox.checked = (self._parameterNode.GetParameter("Invert") == "true")

        # Update buttons states and tooltips
        if self._parameterNode.GetNodeReference("InputVolume") and self._parameterNode.GetNodeReference("OutputVolume"):
            self.ui.applyButton.toolTip = "Compute output volume"
            self.ui.applyButton.enabled = True
        else:
            self.ui.applyButton.toolTip = "Select input and output volume nodes"
            self.ui.applyButton.enabled = False

        # All the GUI updates are done
        self._updatingGUIFromParameterNode = False

    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """
        This method is called when the user makes any change in the GUI.
        The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

        self._parameterNode.SetNodeReferenceID("OutputVolume", self.ui.outputSelector.currentNodeID)
        self._parameterNode.SetParameter("Invert", "true" if self.ui.invertOutputCheckBox.checked else "false")
        self._parameterNode.SetNodeReferenceID("OutputVolumeInverse", self.ui.invertedOutputSelector.currentNodeID)

        self._parameterNode.EndModify(wasModified)



#
# ButterfkyPatchLogic
#

class ButterfkyPatchLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self):
        """
        Called when the logic class is instantiated. Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)

    def setDefaultParameters(self, parameterNode):
        """
        Initialize parameter node with default settings.
        """
        if not parameterNode.GetParameter("Threshold"):
            parameterNode.SetParameter("Threshold", "100.0")
        if not parameterNode.GetParameter("Invert"):
            parameterNode.SetParameter("Invert", "false")

    def process(self, inputVolume, outputVolume, imageThreshold, invert=False, showResult=True):
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """

        if not inputVolume or not outputVolume:
            raise ValueError("Input or output volume is invalid")

        import time
        startTime = time.time()
        logging.info('Processing started')

        # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        cliParams = {
            'InputVolume': inputVolume.GetID(),
            'OutputVolume': outputVolume.GetID(),
            'ThresholdValue': imageThreshold,
            'ThresholdType': 'Above' if invert else 'Below'
        }
        cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
        # We don't need the CLI module node anymore, remove it to not clutter the scene with it
        slicer.mrmlScene.RemoveNode(cliNode)

        stopTime = time.time()
        logging.info(f'Processing completed in {stopTime-startTime:.2f} seconds')


#
# ButterfkyPatchTest
#

class ButterfkyPatchTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_ButterfkyPatch1()

    def test_ButterfkyPatch1(self):
        """ Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData
        registerSampleData()
        inputVolume = SampleData.downloadSample('ButterfkyPatch1')
        self.delayDisplay('Loaded test data set')

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = ButterfkyPatchLogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay('Test passed')






class WidgetParameter:
    def __init__(self,layout,parent) -> None:
        self.parent_layout = layout
        self.parent = parent
        self.surf = None
        self.main_widget = QWidget()
        layout.addWidget(self.main_widget)
        self.maint_layout = QVBoxLayout(self.main_widget)
        self.setup(self.maint_layout)

    def setup(self,layout):

        self.layout_file = QHBoxLayout()
        layout.addLayout(self.layout_file)
        self.label_1 = QLabel('Scan T1')
        self.lineedit = QLineEdit()
        self.button_select_scan = QPushButton('Select')
        self.button_select_scan.pressed.connect(self.selectFile)
        

        self.layout_file.addWidget(self.label_1)
        self.layout_file.addWidget(self.lineedit)
        self.layout_file.addWidget(self.button_select_scan)

        self.combobox_choice_method = QComboBox()
        self.combobox_choice_method.addItems(['Parameter','Landmark','Outline'])
        self.combobox_choice_method.activated.connect(self.changeMode)
        layout.addWidget(self.combobox_choice_method)



        self.stackedWidget = QStackedWidget()
        layout.addWidget(self.stackedWidget)

        #widget paramater
        widget_full_paramater = QWidget()
        self.stackedWidget.insertWidget(0,widget_full_paramater)
        self.layout_widget = QGridLayout(widget_full_paramater)

        self.layout_left_top = QGridLayout()
        self.layout_right_top = QGridLayout()
        self.layout_left_bot = QGridLayout()
        self. layout_right_bot = QGridLayout()

        self.layout_widget.addLayout(self.layout_left_top,0,0)
        self.layout_widget.addLayout(self.layout_right_top,0,1)
        self.layout_widget.addLayout(self.layout_left_bot,1,0)
        self.layout_widget.addLayout(self.layout_right_bot,1,1)


        (self.lineedit_teeth_left_top , 
         self.lineedit_ratio_left_top ,
            self.lineedit_adjust_left_top) = self.displayParamater(self.layout_left_top,1,[5,0.3,0])
        
        (self.lineedit_teeth_right_top , 
         self.lineedit_ratio_right_top ,
            self.lineedit_adjust_right_top) = self.displayParamater(self.layout_right_top,2,[12,0.3,0])
        
        (self.lineedit_teeth_left_bot , 
         self.lineedit_ratio_left_bot ,
            self.lineedit_adjust_left_bot) = self.displayParamater(self.layout_left_bot,3,[3,0.33,0])

        (self.lineedit_teeth_right_bot , 
         self.lineedit_ratio_right_bot ,
            self.lineedit_adjust_right_bot) = self.displayParamater(self.layout_right_bot,4,[14,0.33,0])
        


        #widget outline
        widget_outline = QWidget()
        self.stackedWidget.insertWidget(1,widget_outline)

        self.layout_outline = QGridLayout(widget_outline)
        self.button_loadmarkups = QPushButton('Load Landmarks')
        self.button_loadmarkups.pressed.connect(self.loadLandamrk)
        self.layout_outline.addWidget(self.button_loadmarkups,0,0)

        self.button_curvepoint = QPushButton('Point Curve')
        self.button_curvepoint.pressed.connect(self.curvePoint)
        self.layout_outline.addWidget(self.button_curvepoint,1,0)  

        self.button_placepoint = QPushButton('Middle point')
        self.button_placepoint.pressed.connect(self.placeMiddlePoint)
        self.layout_outline.addWidget(self.button_placepoint,2,0)

        self.button_draw = QPushButton('Draw')
        self.button_draw.pressed.connect(self.draw)
        self.layout_outline.addWidget(self.button_draw,3,0)

        self.layout_button_display = QGridLayout()
        layout.addLayout(self.layout_button_display)

        self.button_view = QPushButton('View')
        self.button_view.pressed.connect(self.viewScan)
        self.layout_button_display.addWidget(self.button_view)

        self.button_update = QPushButton('Update')
        self.button_update.pressed.connect(self.processPatch)
        self.layout_button_display.addWidget(self.button_update)

    def getMainWidget(self):
        return self.main_widget
    
    def changeMode(self,index):
        self.stackedWidget.setCurrentIndex(index)



    def displayParamater(self,layout,number,parameter):
        label_teeth= QLabel(f'Teeth {number}')
        lineedit_teeth= QLineEdit(str(parameter[0]))
        label_ratio= QLabel('Ratio')
        lineedit_ratio= QLineEdit(str(parameter[1]))
        label_adjust = QLabel('Adjust')
        lineedit_adjust = QLineEdit(str(parameter[2]))

        layout.addWidget(label_teeth,0,0)
        layout.addWidget(lineedit_teeth,0,1)
        layout.addWidget(label_ratio,1,0)
        layout.addWidget(lineedit_ratio,1,1)
        layout.addWidget(label_adjust,2,0)
        layout.addWidget(lineedit_adjust,2,1)

        return lineedit_teeth, lineedit_ratio, lineedit_adjust


    def selectFile(self):
        # path_file = QFileDialog.getOpenFileName(self.parent,
        #                                         'Open a file',
        #                                         '/home',
        #                                         'VTK File (*.vtk) ;; STL File (*.stl)')
        # self.lineedit.insert(path_file)

        self.lineedit.insert('/home/luciacev/Desktop/MEG/T1/ExtractionT1/P1_T1_IOS_U_outOr.vtk')


    def viewScan(self):
        if self.surf == None :
            self.surf = slicer.util.loadModel(self.lineedit.text)


    def processPatch(self):
        modelNode = self.surf.GetPolyData()
        butterflyPatch(modelNode,
                        int(self.lineedit_teeth_left_top.text),
                       int(self.lineedit_teeth_right_top.text),
                       int(self.lineedit_teeth_left_bot.text),
                       int(self.lineedit_teeth_right_bot.text),
                       float(self.lineedit_ratio_left_top.text),
                       float(self.lineedit_ratio_right_top.text),
                       float(self.lineedit_ratio_left_bot.text),
                       float(self.lineedit_ratio_right_bot.text),
                       float(self.lineedit_adjust_left_top.text),
                       float(self.lineedit_adjust_right_top.text),
                       float(self.lineedit_adjust_left_bot.text),
                       float(self.lineedit_adjust_right_bot.text))
        

        modelNode.Modified()
        self.displaySegmentation(self.surf)



    def loadLandamrk(self):
        # node = slicer.util.loadMarkups('/home/luciacev/Desktop/Data/ButterflyPatch/F.mrk.json')
        # node.SetCurveTypeToSpline()
        self.curve = slicer.app.mrmlScene().AddNewNodeByClass("vtkMRMLMarkupsClosedCurveNode", 'First curve')
        self.curve.AddControlPoint([0,10,0],'F1')
        self.curve.AddControlPoint([0,-10,0],'F2')
        self.curve.AddControlPoint([0,10,10],'F3')
        self.curve.AddControlPoint([0,10,-10],'F4')


        # curve.SetAndObserveSurfaceConstrainNode(self.surf)


    def curvePoint(self):


        surf = self.surf.GetPolyData()
        surf_normal = ComputeNormals(surf)
        points = surf.GetPoints()
        normal_point = surf_normal.GetPointData().GetArray('Normal')
        point_curve = self.curve.GetCurvePointsWorld() #return point on curve
        out_point = vtk.vtkPoints()
        # out = self.curve.ConstrainPointsToSurface(points,normal_point,surf,out_point)
        self.curve.SetAndObserveSurfaceConstraintNode(self.surf)
        # print(f'out point {out_point}')
        # print(f'out function {out}')

        # markups_node = slicer.app.mrmlScene().AddNewNodeByClass('vtkMRMLMarkupsFiducialNode')
        # for i , point in enumerate(vtk_to_numpy(self.curve.GetCurvePointsWorld().GetData())) :
        #     markups_node.AddControlPoint(point,f'F{i}')


    def placeMiddlePoint(self):
        self.middle_point = slicer.app.mrmlScene().AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
        self.middle_point.AddControlPoint([0,0,0],'F1')


    def draw(self):
        modelNode = self.surf.GetPolyData()
        drawPatch(list(vtk_to_numpy(self.curve.GetCurvePointsWorld().GetData())),modelNode,self.middle_point.GetNthControlPointPositionWorld(0))
        modelNode.Modified()
        self.displaySegmentation(self.surf)


    def displaySurf(self,surf):
        mesh = slicer.app.mrmlScene().AddNewNodeByClass("vtkMRMLModelNode", 'First data')
        mesh.SetAndObservePolyData(surf)
        mesh.CreateDefaultDisplayNodes()




    def displaySegmentation(self,model_node):
        displayNode = model_node.GetModelDisplayNode()
        displayNode.SetScalarVisibility(False)
        disabledModify = displayNode.StartModify()
        displayNode.SetActiveScalarName("Butterfly")
        displayNode.SetScalarVisibility(True)
        displayNode.EndModify(disabledModify)