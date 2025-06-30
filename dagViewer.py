#
#  Copyright (c) 2025 Sam Richards
#  All rights reserved.
#
#  SPDX-License-Identifier: Apache-2.0
#

import sys
import math

try:
    from PySide2.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QGraphicsView, QGraphicsScene, 
                                QGraphicsEllipseItem, QGraphicsLineItem, 
                                QGraphicsTextItem, QTextEdit, QLabel, 
                                QSplitter, QFrame)
    from PySide2.QtCore import Qt, QRectF, QPointF, Signal, QObject
    from PySide2.QtGui import QPen, QBrush, QColor, QFont, QWheelEvent, QPainter, QPolygonF
except ImportError:
  try:
    from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QGraphicsView, QGraphicsScene, 
                                QGraphicsEllipseItem, QGraphicsLineItem, 
                                QGraphicsTextItem, QTextEdit, QLabel, 
                                QSplitter, QFrame)
    from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QObject
    from PySide6.QtGui import QPen, QBrush, QColor, QFont, QWheelEvent, QPainter, QPolygonF

  except ImportError:
    pass

class DAGNodeInterface:
    """
    Interface/Protocol for DAG nodes. Your existing DAG nodes should implement these methods.
    You can either inherit from this class or just ensure your nodes have these methods.
    """
    def get_id(self):
        """Return unique identifier for the node"""
        raise NotImplementedError
    
    def get_name(self):
        """Return display name for the node"""
        raise NotImplementedError
    
    def get_children(self):
        """Return list of child nodes"""
        raise NotImplementedError
    
    def get_parents(self):
        """Return list of parent nodes"""
        raise NotImplementedError
    
    def get_attributes(self):
        """Return dictionary of node attributes for display"""
        raise NotImplementedError


class DefaultDAGNode(DAGNodeInterface):
    """Default implementation - you can replace this with your own node class"""
    def __init__(self, node_id, name, attributes=None):
        self.id = node_id
        self.name = name
        self.attributes = attributes or {}
        self.children = []
        self.parents = []
    
    def add_child(self, child_node):
        if child_node not in self.children:
            self.children.append(child_node)
            child_node.parents.append(self)
    
    def get_id(self):
        return self.id
    
    def get_type(self):
        return None
    
    def get_name(self):
        return self.name
    
    def get_children(self):
        return self.children
    
    def get_parents(self):
        return self.parents
    
    def get_attributes(self):
        return self.attributes
    
    def __str__(self):
        return f"Node({self.get_id()}: {self.get_name()})"


class GraphicsNode(QGraphicsEllipseItem):
    """Visual representation of a DAG node"""
    def __init__(self, dag_node, x, y, radius=30):
        super().__init__(-radius, -radius, radius*2, radius*2)
        self.dag_node = dag_node
        self.radius = radius
        self.setPos(x, y)
        
        # Visual styling
        self.setPen(QPen(QColor(0, 0, 0), 2))

        type = self.dag_node.get_type()

        if "Group" in type:
            self.setBrush(QBrush(QColor(235, 206, 235)))  
        else:
            self.setBrush(QBrush(QColor(135, 206, 235)))  # Light blue
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        
        # Add text label
        self.text_item = QGraphicsTextItem(dag_node.get_name(), self)
        self.text_item.setPos(-len(dag_node.get_name())*3, -8)
        self.text_item.setFont(QFont("Arial", 8))

        self.text_type_item = QGraphicsTextItem(type, self)
        self.text_type_item.setPos(-len(type)*3, 8)
        self.text_type_item.setFont(QFont("Arial", 8))
        
        # Store connected edges for updates
        self.edges = []
    
    def itemChange(self, change, value):
        # Update connected edges when node is moved
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_position()
        return super().itemChange(change, value)
    
    def mouseMoveEvent(self, event):
        """Override mouse move to update edges during drag"""
        super().mouseMoveEvent(event)
        # Update edges while dragging
        for edge in self.edges:
            edge.update_position()
    
    def mousePressEvent(self, event):
        # Handle selection
        super().mousePressEvent(event)
        if self.scene() and hasattr(self.scene(), 'node_selection_handler'):
            self.scene().node_selection_handler(self.dag_node)
    
    def mouseReleaseEvent(self, event):
        """Update edges when mouse is released after dragging"""
        super().mouseReleaseEvent(event)
        for edge in self.edges:
            edge.update_position()


class GraphicsEdge(QGraphicsLineItem):
    """Visual representation of an edge between nodes"""
    def __init__(self, start_node, end_node, color):
        super().__init__()
        self.start_node = start_node
        self.end_node = end_node
        self.myPenColor = QPen(color, 2)
        self.arrowHead = QPolygonF()

        # Visual styling
        self.setPen(self.myPenColor)
        
        # Add to nodes' edge lists
        start_node.edges.append(self)
        end_node.edges.append(self)
        
        self.update_position()
    
    def update_position(self):
        # Calculate line from edge of start circle to edge of end circle
        start_pos = self.start_node.pos()
        end_pos = self.end_node.pos()
        
        # Calculate direction vector
        dx = end_pos.x() - start_pos.x()
        dy = end_pos.y() - start_pos.y()
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0:
            return
            
        # Normalize direction
        dx /= length
        dy /= length
        
        # Offset by radius to start/end at circle edges
        start_x = start_pos.x() + dx * self.start_node.radius
        start_y = start_pos.y() + dy * self.start_node.radius
        end_x = end_pos.x() - dx * self.end_node.radius
        end_y = end_pos.y() - dy * self.end_node.radius
        
        self.setLine(start_x, start_y, end_x, end_y)


    def paint(self, painter: QPainter, option, widget=None):
        # Draw the line first
        super().paint(painter, option, widget)

        # Calculate arrow head points
        arrowSize = 15
        line = self.line()
        angle = math.atan2(-line.dy(), line.dx()) # Angle of the line

        p1 = line.p2() - QPointF(math.sin(angle + math.pi / 3) * arrowSize,
                                 math.cos(angle + math.pi / 3) * arrowSize)
        p2 = line.p2() - QPointF(math.sin(angle + math.pi - math.pi / 3) * arrowSize,
                                 math.cos(angle + math.pi - math.pi / 3) * arrowSize)

        self.arrowHead.clear()
        self.arrowHead.append(line.p2())
        self.arrowHead.append(p1)
        self.arrowHead.append(p2)

        painter.setBrush(self.pen().color()) # Fill arrow head with pen color
        painter.drawPolygon(self.arrowHead)

    def boundingRect(self):
        # This is crucial! You need to expand the bounding rect to include the arrowhead.
        # Otherwise, the arrowhead might not be redrawn correctly when the item moves.
        extra = (self.pen().width() + 15) / 2 # Add some padding for arrow size
        return super().boundingRect().adjusted(-extra, -extra, extra, extra)


class DAGScene(QGraphicsScene):
    """Custom scene that handles node selection"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.node_selection_handler = None  # Will be set by the visualizer widget
        
    def mousePressEvent(self, event):
        # Clear selection if clicking on empty space
        item = self.itemAt(event.scenePos(), self.views()[0].transform())
        if not item:
            self.clearSelection()
            if self.node_selection_handler:
                self.node_selection_handler(None)
        super().mousePressEvent(event)


class DAGGraphicsView(QGraphicsView):
    """Custom graphics view with pan and zoom functionality"""
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        # Enable pan and zoom
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Variables for panning
        self.last_pan_point = QPointF()
        self.is_panning = False
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle zoom with mouse wheel"""
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        
        # Set anchor to mouse position for smooth zooming
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
            
        self.scale(zoom_factor, zoom_factor)
    
    def mousePressEvent(self, event):
        """Handle mouse press for panning"""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = True
            self.last_pan_point = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for panning"""
        if self.is_panning:
            delta = event.position() - self.last_pan_point
            self.last_pan_point = event.position()
            
            # Pan the view
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_F:
            # Fit to view
            self.fit_to_view()
        elif event.key() == Qt.Key.Key_R:
            # Reset zoom
            self.resetTransform()
        else:
            super().keyPressEvent(event)
    
    def fit_to_view(self):
        """Fit all items in view"""
        self.fitInView(self.scene().itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)


class DAGVisualizerWidget(QWidget):
    """
    Main DAG visualizer widget that can be embedded in any Qt application.
    This is NOT a QMainWindow, so it can be used as a regular widget.
    """
    def __init__(self, dag_nodes=None, parent=None):
        super().__init__(parent)
        self.dag_nodes = dag_nodes.copy() or {}
        self.setup_ui()
        if self.dag_nodes:
            self.visualize_dag()
    
    def setup_ui(self):
        """Setup the UI layout"""
        layout = QHBoxLayout(self)
        
        # Create splitter for main layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Graphics view for DAG visualization
        self.scene = DAGScene()
        self.scene.node_selection_handler = self.on_node_selected
        
        self.view = DAGGraphicsView(self.scene)
        
        # Properties panel
        properties_widget = QWidget()
        properties_layout = QVBoxLayout(properties_widget)
        
        # Add instructions
        instructions = QLabel("<H2>RV Dag Viewer</H2><P>Controls:</P><BL><LI>Mouse wheel: Zoom</LI><LI>Middle mouse: Pan</LI><LI>F: Fit to view</LI><LI>R: Reset zoom</LI><LI>Click node: Select</LI></BL>")
        instructions.setStyleSheet("QLabel { background-color: #f0f0f0; font-color: #000000; padding: 5px; border: 1px solid #ccc; }")
        properties_layout.addWidget(instructions)
        
        properties_layout.addWidget(QLabel("Node Properties:"))
        self.properties_text = QTextEdit()
        self.properties_text.setReadOnly(True)
        #self.properties_text.setMaximumWidth(300)
        properties_layout.addWidget(self.properties_text)
        
        # Add widgets to splitter
        splitter.addWidget(self.view)
        splitter.addWidget(properties_widget)
        splitter.setSizes([800, 300])
        
        # Set focus to view for keyboard shortcuts
        self.view.setFocus()
    
    def set_dag_nodes(self, dag_nodes):
        """
        Set the DAG nodes to visualize. 
        dag_nodes should be a dictionary where keys are node IDs and values are node objects
        that implement the DAGNodeInterface methods.
        """
        self.dag_nodes = dag_nodes
        self.visualize_dag()
    
    def visualize_dag(self):
        """Create visual representation of the DAG"""
        # Clear existing items
        self.scene.clear()
        
        if not self.dag_nodes:
            return
        
        graphics_nodes = {}
        positions = self.calculate_layout()
        
        # Create graphics nodes
        for node_id, dag_node in self.dag_nodes.items():
            x, y = positions.get(node_id, (0, 0))
            graphics_node = GraphicsNode(dag_node, x, y)
            graphics_nodes[node_id] = graphics_node
            self.scene.addItem(graphics_node)
        
        # Create edges
        for node_id, dag_node in self.dag_nodes.items():
            start_graphics = graphics_nodes[node_id]
            for child in dag_node.get_children():
                child_id = child.get_id()
                if child_id in graphics_nodes:
                    end_graphics = graphics_nodes[child_id]
                    edge = GraphicsEdge(start_graphics, end_graphics, QColor(0, 0, 0))
                    self.scene.addItem(edge)

            for child in dag_node.get_outputs():
                child_id = child.get_id()
                if child_id in graphics_nodes:
                    end_graphics = graphics_nodes[child_id]
                    #print("Making child:", node_id, " to ", child_id)
                    edge = GraphicsEdge(start_graphics, end_graphics, QColor(100, 100, 190))
                    self.scene.addItem(edge)
                else:
                    print("Child - ", child_id, " missing for output")
        # Fit view to content initially
        self.view.fit_to_view()
    
    def calculate_layout(self):
        """Improved layered layout algorithm with better spacing"""
        positions = {}
        layer_height = 200  # Increased vertical spacing
        base_node_width = 150  # Base horizontal spacing
        # find nodes with no parents.
        roots = []
        for node_id, node in self.dag_nodes.items():
            if len(node.get_parents()) == 0:
                roots.append(node_id)


        def walk_outputs(node_id, dag_nodes, level, foundnodes, rootchains, children_ids):
            if node_id not in children_ids:
                return
            if node_id not in foundnodes:
                foundnodes[node_id] = level
                rootchains.append(node_id)

            for child in dag_nodes[node_id].get_outputs():
                walk_outputs(child.get_id(), dag_nodes, level + 1, foundnodes, rootchains, children_ids)

        def walk_tree(node_id, dag_nodes, x, y, positions):
            """ This handles a single root tree of nodes getting their positions."""

            # Set thie position for the root node.
            positions[node_id] = (x, y)
            y = y + layer_height

            # Now we need to figure out how the inputs and outputs are organized, so whever possible go left to right.

            childroots = [] # The list of children roots.
            foundnodes = {} # Have we found all the child nodes.
            rootchains = {} # A root chain is a chain of outputs, that cannot repeat, all linked to the same childroot.
            children = dag_nodes[node_id].get_children()
            children_ids = [c.get_id() for c in children]
            for child in children:
                if len(child.get_inputs()) == 0:
                    childroots.append(child.get_id())
                    rootchains[child.get_id()] = []
                    walk_outputs(child.get_id(), dag_nodes, 0, foundnodes, rootchains[child.get_id()], children_ids)
            
            for child in children:
                if child.get_id() not in foundnodes:
                    print("Lost child:", child.get_id())
                    foundnodes[child.get_id()] = -1
                    childroots.append(child.get_id())
                    rootchains[child.get_id()] = []

            start_x = x
            max_x = start_x + base_node_width
            for root in childroots:
                chain = rootchains[root]
                x = start_x
                # Handle the childroot node
                positions[root] = (x, y)

                x = x + base_node_width
                
                for child in chain:
                    #positions[child] = (x, y)
                    #x = x + base_node_width
                    # This is a catch all, really this should be another recursive layer of this whole thing, so we are banking on
                    # not needing to sort chains, (although we probably do)
                    x = walk_tree(child, dag_nodes, x, y, positions)
                y = y + 100
                max_x = max(x, max_x) # we do this to ensure that we are getting the biggest of the chains.
            #for child in sortchildren:
            #    x = walk_tree(child.get_id(), dag_nodes, x, y, positions)
            return max_x

        x = 0
        y = 0
        for root in roots:
            x = walk_tree(root, self.dag_nodes, x, y, positions)
            y = y + layer_height / 2

        # Double check we have everyone... (which we should)

        for node_id, node in self.dag_nodes.items():
            if node_id not in positions:
                print("New lost child:", node_id, node.get_parents(), node.get_children())
                positions[node_id] = (x, 0)
                x = x + base_node_width
    
        return positions
        # Topological sort to determine layers
        layers = self.topological_layers()
        
        # Calculate layout parameters

        
        for layer_idx, layer_nodes in enumerate(layers):
            y = layer_idx * layer_height
            layer_count = len(layer_nodes)
            
            # Dynamic width based on number of nodes in layer
            if layer_count == 1:
                # Single node centered
                positions[layer_nodes[0]] = (0, y)
            else:
                # Multiple nodes spread out
                total_width = (layer_count - 1) * base_node_width
                start_x = -total_width / 2
                
                for node_idx, node_id in enumerate(layer_nodes):
                    x = start_x + node_idx * base_node_width
                    positions[node_id] = (x, y)
        
        return positions
    
    def topological_layers(self):
        """Group nodes into layers for visualization"""
        # Find nodes with no parents (roots)
        in_degree = {node_id: len(node.get_parents()) for node_id, node in self.dag_nodes.items()}
        layers = []
        remaining = set(self.dag_nodes.keys())
        
        while remaining:
            # Find nodes with no remaining dependencies
            current_layer = [node_id for node_id in remaining if in_degree[node_id] == 0]
            if not current_layer:
                # Handle cycles by taking any remaining node
                current_layer = [next(iter(remaining))]
            
            layers.append(current_layer)
            
            # Remove current layer nodes and update in-degrees
            for node_id in current_layer:
                remaining.remove(node_id)
                for child in self.dag_nodes[node_id].get_children():
                    child_id = child.get_id()
                    if child_id in in_degree:
                        in_degree[child_id] -= 1
        
        return layers
    
    def on_node_selected(self, dag_node):
        """Handle node selection"""
        if dag_node is None:
            self.properties_text.clear()
            return
        
        # Display node properties using the interface methods
        parents = [p.get_name() for p in dag_node.get_parents()]
        children = [c.get_name() for c in dag_node.get_children()]
        inputs = [c.get_name() for c in dag_node.get_inputs()]
        outputs = [c.get_name() for c in dag_node.get_outputs()]
        
        properties = [
            f"Node ID: {dag_node.get_id()}",
            #f"Name: {dag_node.get_name()}",
            f"Parents: {parents}",
            f"Children: {children}",
            f"Inputs: {inputs}",
            f"Outputs: {outputs}",
            "",
            "Attributes:"
        ]
        
        for key, value in dag_node.get_attributes().items():
            properties.append(f"  {key}: {value}")
        
        self.properties_text.setPlainText("\n".join(properties))


def create_sample_dag():
    """Create a sample DAG for demonstration - you can replace this with your own data"""
    nodes = {}
    
    # Create nodes with various attributes
    node_data = [
        ("A", "Source1", {"type": "data_source", "format": "csv", "size": "1.2MB"}),
        ("B", "Source2", {"type": "data_source", "format": "json", "size": "800KB"}),
        ("C", "Filter", {"type": "transform", "operation": "filter", "rows_processed": 15000}),
        ("D", "Aggregate", {"type": "transform", "operation": "aggregate", "group_by": "category"}),
        ("E", "Join", {"type": "merge", "join_type": "inner", "key": "id"}),
        ("F", "Validate", {"type": "quality_check", "rules": 5, "pass_rate": "98.5%"}),
        ("G", "Export", {"type": "sink", "destination": "database", "table": "results"}),
        ("H", "Archive", {"type": "sink", "destination": "s3", "bucket": "data-archive"}),
    ]
    
    for node_id, name, attrs in node_data:
        nodes[node_id] = DefaultDAGNode(node_id, name, attrs)
    
    # Define connections to create a more interesting DAG structure
    connections = [
        ("A", "C"),  # Source1 -> Filter
        ("B", "D"),  # Source2 -> Aggregate  
        ("C", "E"),  # Filter -> Join
        ("D", "E"),  # Aggregate -> Join
        ("E", "F"),  # Join -> Validate
        ("F", "G"),  # Validate -> Export
        ("F", "H"),  # Validate -> Archive
    ]
    
    for parent_id, child_id in connections:
        nodes[parent_id].add_child(nodes[child_id])
    
    return nodes


# Example usage as a standalone window (for testing)
class DAGVisualizerWindow(QMainWindow):
    """Example window for standalone usage - you probably won't need this"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DAG Node Network Visualizer - PySide6")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create the widget and set it as central widget
        dag_nodes = create_sample_dag()
        self.dag_widget = DAGVisualizerWidget(dag_nodes)
        self.setCentralWidget(self.dag_widget)


def main():
    """Example of how to use the widget standalone"""
    app = QApplication(sys.argv)
    
    # Option 1: Use as a standalone window
    window = DAGVisualizerWindow()
    window.show()
    
    # Option 2: Use as a widget in your existing application
    # dag_nodes = your_existing_dag_nodes  # Your DAG data
    # dag_widget = DAGVisualizerWidget(dag_nodes, parent=your_parent_widget)
    # your_layout.addWidget(dag_widget)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()