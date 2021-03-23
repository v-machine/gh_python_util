__author__ = "Vincent Mai"
__version__ = "2021.03.15"

from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path
import ghpythonlib.treehelpers as th
from collections import namedtuple
import inspect

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
        if kwargs:
            access = [self.__parseAccess(key) for key in 
                      kwargs.get(TreeHandler._DEFAULT_ARG)]
        else:
            access = self.access
        
        # TODO: refactor args, dims, access to argWrapper object
        args = map(self.__toTree, args)
        dims = [_Dimension.getDim(arg) for arg in args]
        matchedDim = _Dimension.matchDims(dims)
        for dim in dims:
            dim.matchedDim = matchedDim
        pathsIndices = self.__generatePathsIndices(matchedDim)
        result = DataTree[object]()
        
        for indices in pathsIndices:
            branches = [self.__branchWrapper(args[i], dims[i], indices, access[i])
                        for i in range(len(args))]
            entries = map(self.__funcWrapper, self.__dataWrapper(branches))
            if isinstance(entries[0], list):
                for i, entry in enumerate(entries):
                    subIndices = indices + [i]
                    result.AddRange(entry, GH_Path(*subIndices))
            else:
                result.AddRange(entries, GH_Path(*indices))
        return result
    
    def __parseDefaultArgs(self):
        """Returns a list of default access from self.func's default argument.
        Raises exception if keyword doesn't match _DEFAULT_ARG"""
        args = inspect.getargspec(self.func).args
        try:
            idx = args.index(TreeHandler._DEFAULT_ARG)
        except ValueError:
            msg0 = ("'%s' default argument not found." % TreeHandler._DEFAULT_ARG)
            msg1 = (" It must be specified in function's definition: \n" +
                    ">>> def func(arg1, arg2, access=['item', 'item']): pass")
            raise Exception(msg0+msg1)
        numPosArgs = len(args) - len(self.func.__defaults__)
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

    def __toTree(self, arg):
        """Converts arg to Grasshopper.DataTree"""
        if isinstance(arg, DataTree[object]):
            return arg
        elif isinstance(arg, list):
            return th.list_to_tree(arg)
        else:
            return th.list_to_tree([arg])

    def __generatePathsIndices(self, dim):
        """Returns all possible paths indices given a tree's dimension"""
        def product(iterable):
            return reduce(lambda a, b: a*b, iterable)
        indices = dim.indices
        size = product(indices)
        rep = [size // product(indices[ : i+1]) for i, d in enumerate(indices)]
        return [[j // r % d for r, d in zip(rep, indices)] for j in range(size)]

    def __branchWrapper(self, tree, dim, pathIndices, access):
        """Returns the list of data in the branch as specified by the 
        path. Returns the next closet branch if path does not exist"""
        unmatchedIndices = [min(i, d-1) for i, d in 
                            zip(dim.unmatch(pathIndices), dim.indices)]
        path = GH_Path(*unmatchedIndices)
        if access is TreeHandler._ACCESS.list:
            return [tree.Branch(path)]
        else:
            return tree.Branch(path)

    def __dataWrapper(self, branches):
        """Returns a list of zipped data item from a list of branches.
        Repeat the last item if a branch is shorter than the lgerongest."""
        # TODO: handles exceptions if branch content is None
        l = max([len(b) for b in branches])
        return [[b[min(len(b)-1, i)] for b in branches] for i in range(l)]
    
    def __funcWrapper(self, args):
        return self.func(*args)

class _Dimension(object):
    def __init__(self, indices, trailingZeroes=0):
        self._indices = indices
        self._trailingZeroes = trailingZeroes
        self._length = len(self._indices) - self._trailingZeroes
        self._matchedDim = None
        self._unmatchIndex = None
   
    @property
    def indices(self):
        """Returns a tuple of indices within the dimension"""
        return self._indices
    
    @property
    def trailingZeroes(self):
        """Get the number of trailing zeroes"""
        return self._trailingZeroes

    @property
    def length(self):
        """Returns length of dimension indices without trailing zeroes"""
        return self._length
    
    @property
    def matchedDim(self):
        """Returns a tuple of indices from a dimension with which
        this dimension had been matched to"""
        return self._matchedDim.indices

    @matchedDim.setter
    def matchedDim(self, matchedDim):
        """Sets the matched dimension"""
        self._matchedDim = matchedDim
        self._unmatchIndex = self.__getUnmatchIndex(matchedDim)

    def unmatch(self, indices):
        """Returns a tuple of indices that which undoes the
        effect of dimensional matching"""
        j, k = self._unmatchIndex
        return indices[j : k]
    
    @staticmethod
    def matchDims(dims):
        """Return the matched dimension as a result of matching
        an iterable of dimensions"""
        length = max([dim.length for dim in dims])
        trailingZeroes = max([dim.trailingZeroes for dim in dims])
        matchedIndices = [1 for _ in range(length + trailingZeroes)]
        for dim in dims:
            for i, d in enumerate(dim.indices):
                j = length - dim.length + i
                if d > matchedIndices[j]:
                    matchedIndices[j] = d
        return _Dimension(tuple(matchedIndices),
                          trailingZeroes=trailingZeroes)

    @staticmethod
    def getDim(tree):
        """Returns a Dimension object given the input tree"""
        branchCount = tree.BranchCount
        indices = tree.Path(branchCount - 1).Indices
        trailingZeroes = 0
        if branchCount > 1:
            for i in indices[: : -1]:
                if i != 0: break
                trailingZeroes += 1
        indices = [i+1 for i in indices]
        return _Dimension(tuple(indices),
                          trailingZeroes=trailingZeroes)

    def __getUnmatchIndex(self, matchedDim):
        """Returns a tuples as slicing indices for undoing the effect 
        of dimension matching"""
        start = matchedDim.length - self.length
        end = start + len(self.indices)
        return (start, end)
