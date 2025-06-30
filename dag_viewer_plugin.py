#
#  Copyright (c) 2025 Sam Richards
#  All rights reserved.
#
#  SPDX-License-Identifier: Apache-2.0
#

from __future__ import print_function

import os
import sys
import datetime

try:
    from PySide2 import QtGui, QtCore, QtWidgets
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    from PySide2.QtUiTools import QUiLoader
except ImportError:
  try:
    from PySide6 import QtGui, QtCore, QtWidgets
    from PySide6.QtGui import *
    from PySide6.QtCore import *
    from PySide6.QtWidgets import *
    from PySide6.QtUiTools import QUiLoader
  except ImportError:
    pass

from rv import commands, extra_commands
from rv import rvtypes

from dagViewer import DAGVisualizerWidget, DefaultDAGNode

class RVDAGNode(DefaultDAGNode):
    def __init__(self, node, dagtree):
        DefaultDAGNode.__init__(self, node, node, {})
        self._dagtree = dagtree

    def get_type(self):
        return commands.nodeType(self.id)

    def get_inputs(self):
        inputs, outputs = commands.nodeConnections(self.id)
        children = []
        for input in inputs:
            if input == self.id:
                continue
            if input not in self._dagtree:
                self._dagtree[input] = RVDAGNode(input, self._dagtree)
            children.append(self._dagtree[input]) 
        return children


    def get_outputs(self):
        inputs, outputs = commands.nodeConnections(self.id)
        children = []
        for output in outputs:
            if output == self.id:
                continue
            if output not in self._dagtree:
                self._dagtree[output] = RVDAGNode(output, self._dagtree)
            children.append(self._dagtree[output]) 
        return children

    def get_children(self):
        children = []

        # children = self.get_outputs()
        
        try:
            for child in commands.nodesInGroup(self.id):
                if child == self.id:
                    continue
                if child not in self._dagtree:
                    self._dagtree[child] = RVDAGNode(child, self._dagtree)
                children.append(self._dagtree[child])
            #print(self.id, " children type:", commands.nodeType(self.id))
        except Exception as e:        
            #print(self.id, " no children type:", commands.nodeType(self.id), " outputs:", children)

            pass
        return children
    
    def get_parents(self):
        nodeGroup = commands.nodeGroup(self.id)
        parents = []
        if nodeGroup is not None:
            if nodeGroup not in self._dagtree:
                    self._dagtree[nodeGroup] = RVDAGNode(nodeGroup, self._dagtree)
            parents.append(self._dagtree[nodeGroup])

        # parents.extend(self.get_inputs())

        return parents
    
    def get_attributes(self):
        props = {'type': commands.nodeType(self.id)}
        for prop in commands.properties(self.id):
            propinfo = commands.propertyInfo(prop)
            if propinfo['type'] == 8:
                props[prop] = commands.getStringProperty(prop)
            if propinfo["type"] == 1:
                props[prop] = commands.getFloatProperty(prop)
            if propinfo["type"] == 2:
                props[prop] = commands.getIntProperty(prop)
        return props


    def __str__(self):
        
        return "RVDAGNode({})".format(
            repr(self.id)
        )

    def __repr__(self):
        return "RVDAGNode(id={})".format(
            repr(self.id)
        )

class DAGViewerPlugin(rvtypes.MinorMode):

    def __init__(self):
        super(DAGViewerPlugin, self).__init__()

        self.init(
            "dagviewer",
            [
            ],
            None,
            [
                ("Tools",
                [
                        ("DAG Viewer", self.dag_viewer, None, None),
                ]
                )
            ]
        )


    def dag_viewer(self, event):
        dag_nodes = {}

        # toplevel = RVDAGNode(commands.viewNode(), dag_nodes)

        def walkTree(node, dag_nodes, visted=None):
            nodes = visted or []
            if node in nodes:
                return
            nodes.append(node)
        
            for child in node.get_children():
                walkTree(child, dag_nodes, nodes)

            for child in node.get_outputs():
                walkTree(child, dag_nodes, nodes)
            
            for parent in node.get_parents():
                walkTree(parent, dag_nodes, nodes)
        
        #for nodename in commands.nodesOfType("RVSourceGroup"):
        #    walkTree(RVDAGNode(nodename, dag_nodes), dag_nodes)
        for nodename in commands.nodes():
           node = RVDAGNode(nodename, dag_nodes)
           dag_nodes[nodename] = node

        self.dag_widget = DAGVisualizerWidget(dag_nodes)
        self.dag_widget.resize(1000, 800)
        self.dag_widget.show()

def createMode():
    return DAGViewerPlugin()
