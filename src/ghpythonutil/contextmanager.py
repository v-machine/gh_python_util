__author__ = "Vincent Mai"
__version__ = "2020.10.05"

import scriptcontext as sc

class RhinoDocContext:
    """Context Manager to enter the RhinoDoc.ActiveDoc Context

    Automatically switches to RhinoDoc.ActiveDoc, perform user-defined tasks
    and switches back to grasshopper.doc context.

    Example:
        ```
        >>> with RhinoDocContext():
                current_doc = sc.doc.ActiveDoc
                current_doc.Objects.a_rhinoscriptsyntax_func(*args, **kwargs)
        ```
    """
    def __init__(self):
        self.ghdoc = sc.doc
        self.rhinodoc = Rhino.RhinoDoc.ActiveDoc

    def __enter__(self):
        sc.doc = self.rhinodoc

    def __exit__(self, type, value, traceback):
        sc.doc = self.ghdoc

class NewLayerContext:
    """Context manager to call a rhinoscriptsyntax function in a new layer

    Example:
        ```
        >>> def do_something_in_rhino(*args, **kwargs):
            with RhinoDocContext():
                current_doc = sc.doc.ActiveDoc
                current_doc.Objects.a_rhinoscriptsyntax_func(*args, **kwargs)

        >>> with NewLayerContext("my_new_layer_01"):
                do_something_in_rhino(*args, **kwargs)
        ```
    """
    def __init__(self, layer_name):
        self.layer_name = layer_name

    def __enter__(self):
        self.__deleteLayer(self.layer_name)
        self.__createAndSetCurrentLayer(self.layer_name)

    def __exit__(self, type, value, traceback):
        self.__resetLayer()

    def __createAndSetCurrentLayer(self, layer_name):
        """Creates a new layer and set it as the current layer
        """
        with RhinoDocContext():
            layer = sc.doc.Layers.FindName(layer_name)
            if layer is None:
                layer_idx = sc.doc.Layers.Add(layer_name, System.Drawing.Color.Black)
            else:
                layer_idx = layer.Index
            sc.doc.Layers.SetCurrentLayerIndex(layer_idx, True)
            
    def __resetLayer(self):
        """Resets current layer to the default (first) layer
        """
        with RhinoDocContext():
            sc.doc.Layers.SetCurrentLayerIndex(0, True)
            
    def __deleteLayer(self, layer_name):
        """Deletes a layer and all objects inside
        """
        with RhinoDocContext():
            rhinoObjects = sc.doc.Objects.FindByLayer(layer_name)
            if rhinoObjects:
                for obj in rhinoObjects:
                    sc.doc.Objects.Delete(obj)
            sc.doc.Layers.SetCurrentLayerIndex(0, True)
            sc.doc.Layers.Delete(sc.doc.Layers.FindName(layer_name), True)
