# ghpythonutil
ghpythonutil is a lightweight utility library for Grasshopper Python Scripting.

## Installation
Choose one of several destination <PATH> by runing the following in a GhPython component:
```
# in a GhPython component
# Choose a <PATH> from sys.path
import sys
for path in sys.path:
    print(path)
```
Git clone `ghpythonutil` into one IronPython Interpreter's default paths.
```
$ git clone https://github.com/v-machine/gh_python_util
$ mv -nv gh_python_util/src/ghpythonutil <PATH>/ghpythonutil
$ rm gh_python_util
```
You can also manually place the folder `ghpythonutil` into one of the paths in `sys.path`.

## TreeHandler
`treehandler.TreeHandler` is a function decorator for handling Data Trees as inputs in user-defined functions. Calls to decorated functions will avoid implicit looping behavior triggered by component inputs with `item access` or `list access`. The decorator will handle DataTree input in a fashion identical to any other default grasshopper component, i.e., automatic branch and item matching.

### Usage
On a GhPython component, right-click on all inputs for the decorated function and set `tree access`. You can decorate functions that require delegated Data Tree handling as following:
```
from ghpythonutil.treehandler import TreeHandler

@TreeHandler
def func(arg1, arg2, access=["<ACCESS_TYPE>", "<ACCESS_TYPE>"]):
    # peform tasks
    return result

output = func(arg1, arg2)
```

Arguments for the decorated function definition must include the `acces` default argument. This is because GhPython component will now parse all input as Data Trees. Thus, we must manually pass the actual access types to `TreeHandler` so that they are parsed correctly when the decorated function is called. `access` can be dynamically overwritten during function calls. 

### Example
```
from ghpythonutil.treehandler import TreeHandler
import rhinoscriptsyntax as rs
import Rhino.Geometry as rg

@TreeHandler
def circle(p, r, access=["item", "item"]):
    return rg.Circle(p, r)

@TreeHandler
def polyline(v, access=["list"]):
    return rg.Polyline(v)

@TreeHandler
def divideCurve(c, n, access=["item", "item"]):
    return rs.DivideCurve(c, n)

outputA = circle(p, r)
outputB = polyline(v)
outputC = divideCurve(c, n)
```

### Notes:
1. Functions decorated with `TreeHandler` will process Data Trees exactly like native Grasshopper components, regardless of whether the Data Tree had been grafted, flattened, or simplified, and irrespective of whether the input Data Trees have mismatched shapes (topologies).

2. TreeHandler works on composite functions, so there is no need to decorate every function that requires Data Tree handling, as long as the function is called from within the aggregated (and decorated) function. However, access types for all input must be specifed in the composite function as the `access` default argument. 

3. If an input has `item access` or `list access` set on the GhPython Component, `TreeHandler` will implicitly cast it into a Data Tree. However, function calls will still trigger implicit looping and loose the speed-up benefits.

4. Decorated function calls will see _some_ [performance increase]("https://github.com/v-machine/gh_python_util/blob/main/performance/ghpython_component_speed_benchmark.ipynb") when compared against undecorated ones running in a vanilla GhPython module. However, there's no gaurantee. Factors impacting performances include 'type hint', implicit looping triggered by 'item access' and 'list access', and mismatched Data Trees.

5. Decorated function does not support inline operations, such as: `foo(...) * 20`, even if `foo()` returns a number. This is due to the returned type of a decorated function being a Data Tree.

6. There is no current support for parallelization for decorated function. Internal parallization and other optimization will be the focus for the upcoming release.

## Context Managers
`ghpythonutil.contextmanagers` automatically manages context for needed function calls.

## RhinoDocContext
Automatically switches to RhinoDoc.ActiveDoc, perform user-defined tasks and switches back to grasshopper.doc context.

### Example
```
def do_something_in_rhino(*args, **kwargs):
    with RhinoDocContext():
        current_doc = sc.doc.ActiveDoc
        current_doc.Objects.a_rhinoscriptsyntax_func(*args, **kwargs)
```

## NewLayerContext
Context manager to call a rhinoscriptsyntax function in a new layer.

### Example
```
with NewLayerContext("my_new_layer_01"):
     do_something_in_rhino(*args, **kwargs)
```
