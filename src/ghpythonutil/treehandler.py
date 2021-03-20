__author__ = "Vincent Mai"
__version__ = "2021.03.15"

from Grasshopper import DataTree
from collections import namedtuple
import inspect
import ghpythonlib.treehelpers as th

class TreeHandler:
    """Decorator to handle DataTree as input for user-defined functions.

    Decorator for user-defined functions in custom python components in 
    Grasshopper. Calls to decorated functions will avoid implicit looping 
    behavior triggered by component parameters with "item" or "list" access. 
    The decorator will handle DataTree input in the identical fashion of any 
    default grasshopper components.

    Params:
        func : Callable.
        The function to be decorated by TreeHandler.

    Note:
        Argument access must be specified as a list of keywords in a default
        argument in the function definition, i.e., `access=["list", "item"]`.

    Example:
        ```
        >>> @TreeHandler
            def circle(p, r, access=["item", "item"]):
                return rs.AddCircle(p, r)
        >>> @TreeHandler
            def polyline(v, access=["list"]):
                return rs.AddPolyline(v)
        >>> output_a = circle(p, r)
        >>> output_b = polyline(v)
    """
    _DEFAULT_ARG = "access"
    _AccessTypes = namedtuple("_AccessTypes", ["item", "tree", "list"])
    _ACCESS = _AccessTypes(0, 0, 1)
    _ACCESS_DICT = {"item": _ACCESS.item, 
                   "tree": _ACCESS.tree, 
                   "list": _ACCESS.list} 

    def __init__(self, func):
        self.func = func
        paramsAccess = self.__parseDefaultArgs()
        self.access = map(self.__parseAccess, paramsAccess)
        
    def __call__(self, *args, **kwargs):
        """Returns the result of decorated function"""
        args = map(self.__toTree, args)
        if kwargs:
            access = [self.__parseAccess(key) for key in 
                      kwargs.get(TreeHandler._DEFAULT_ARG)]
        else:
            access = self.access
        depths = [self.__treeDepth(arg) for arg in args]
        lsts = [th.tree_to_list(arg) for arg in args]
        return th.list_to_tree(
            self.__interlaceDepth(lsts, access, depths))

    def __parseDefaultArgs(self):
        """Returns a list of default access from self.func's default argument.
        Raises exception if keyword doesn't match _DEFAULT_ARG"""
        args = inspect.getargspec(self.func).args
        numPosArgs = len(args) - len(self.func.__defaults__)
        try:
            idx = args.index(TreeHandler._DEFAULT_ARG)
        except ValueError:
            msg0 = ("'%s' default argument not found." % TreeHandler._DEFAULT_ARG)
            msg1 = (" It must be specified in function's definition: \n" +
                    ">>> def func(arg1, arg2, access=['item', 'item']): pass")
            raise Exception(msg0+msg1)
        return list(self.func.__defaults__)[idx - numPosArgs]

    def __parseAccess(self, key):
        """Returns the parameter access type in _ACCESS_DICT given input key.
        Raises exception if key is not found"""
        access = TreeHandler._ACCESS_DICT.get(key)
        if access is None:
            msg = ("Invalid parameter access: {name}. Access type" +
                   "must be 'item', 'list', or 'tree'.").format(name=key)
            raise KeyError(msg)
        else:
            return access

    def __treeDepth(self, tree):
        """Returns the depth of the tree [DataTree]"""
        path = tree.Path(tree.BranchCount-1)
        return path.Length - 1

    def __interlaceLength(self, lsts, depth):
        """Returns the result of interlacing then applying self.func to two 
        lists with equal depth but varying in sizes per depth level."""
        result = []
        for i in range(max([len(lst) for lst in lsts])): 
            items = [lst[min(i, len(lst)-1)] for lst in lsts]
            if depth > 0:
                result.append(self.__interlaceLength(items, depth-1))
            else:
                result.append(self.func(*items))
        return result

    def __interlaceDepth(self, lsts, access, depths):
        """Returns the result of interlacing then applying self.func
        to two lists possibly differ in depths and sizes"""
        maxDepth = max(depths)
        for idx, d in enumerate(depths):
            if access[idx] is TreeHandler._ACCESS.list:
                lsts[idx] = self.__appendDepth(lsts[idx], d)
            for j in range(maxDepth-d):
                lsts[idx] = [lsts[idx]]
        return self.__interlaceLength(lsts, maxDepth)

    def __appendDepth(self, lst, depth):
        """Append one level to the inner most depth"""
        result = []
        if depth == 0:
            return [lst]
        else:
            for idx in range(len(lst)):
                result.append(self.__appendDepth(lst[idx], depth-1))
        return result

    def __toTree(self, arg):
        """Converts arg to Grasshopper.DataTree"""
        if isinstance(arg, DataTree[object]):
            return arg
        elif isinstance(arg, list):
            return th.list_to_tree(arg)
        else:
            return th.list_to_tree([arg])