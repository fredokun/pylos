

"""This is the implementation
of the Pylos object system for Python 3.

This is a thin extension of the Python object system
 to support generic functions/methods "a la" Lisp/CLOS
 (with multi-dispatch and all.).
"""

import inspect
import warnings

class GenericWarning(UserWarning):
    def __init__(self, msg):
        super().__init__(msg)

class GenericError(Exception):
    def __init_(self, msg):
        super().__init__(msg)

class DispatchDict:
    def __init__(self, warn_on_redefinition=True):
        self.warn_on_redefinition = warn_on_redefinition
        self.dispatch_class = None
        self.dispatch_inst = None
        self.dispatch_default = None
        self.dispatch_func = None

    def handle_class(self, cls):
        if self.dispatch_class:
            ndispatch = self.dispatch_class.get(cls, None)
            if ndispatch:
                return ndispatch
        else:
            self.dispatch_class = dict()

        ndispatch = DispatchDict()
        self.dispatch_class[cls] = ndispatch

        return ndispatch

    def handle_inst(self, inst):
        if self.dispatch_inst:
            ndispatch = self.dispatch_inst.get(inst, None)
            if ndispatch:
                return ndispatch
        else:
            self.dispatch_inst = dict()

        ndispatch = DispatchDict()
        self.dispatch_inst[inst] = ndispatch

        return ndispatch

    def handle_default(self):
        if not self.dispatch_default:
            self.dispatch_default = DispatchDict()

        return self.dispatch_default

    def register_func(self, sig, func):
        if self.dispatch_func and self.warn_on_redefinition:
            warnings.warn("Redefinition of generic call for signature: {}".format(sig), GenericWarning)
        self.dispatch_func = func

    def fetch_class(self, cls):
        if self.dispatch_class:
            return self.dispatch_class.get(cls, None)

        return None

    def fetch_inst(self, inst):
        if self.dispatch_inst:
            return self.dispatch_inst.get(inst, None)

        return None

    def fetch_default(self):
        return self.dispatch_default

    def __repr__(self):
        return "<DispatchDict[classes={}, insts={}, default={}, func={}]>".format(self.dispatch_class,
                                                                                  self.dispatch_inst,
                                                                                  self.dispatch_default,
                                                                                  self.dispatch_func)

class Generic:
    def __init__(self, name, doc, gen_func, warn_on_redefinition=True):
        self.name = name
        self.doc = doc
        self.gen_func = gen_func
        self.warn_on_redefinition = warn_on_redefinition

        self.dispatch = DispatchDict()

    def wrap(self, func):
        # call the generic function (pre-hook for debugging)
        self.gen_func()

        sig = inspect.signature(func)
        #print("Signature is: {}".format(sig))

        arity = len(sig.parameters.values())
        #print("Call arity = {}".format(arity))
        pdispatch = self.dispatch
        for (nth, param) in zip(range(1, arity + 1), sig.parameters.values()):
            #print("Parameter #{}: {}".format(nth, param.name))
            #print("   ==> annot: {}".format(param.annotation))
            #print("   ==> kind: {}".format(param.kind))

            if param.annotation == param.empty:
                #print("      ==> empty annotation")
                pdispatch = pdispatch.handle_default()
            elif inspect.isclass(param.annotation):
                #print("      ==> it's a class !")
                pdispatch = pdispatch.handle_class(param.annotation)
            else:
                #print("      ==> it's an object")
                pdispatch = pdispatch.handle_inst(param.annotation)

        pdispatch.register_func(sig, func)

    def __call__(self, *args, **kwargs):
        if kwargs:
            raise GenericError("Keyword argument not accepted in generic calls.")
        # import pdb ; pdb.set_trace()
        adispatch = self.dispatch
        for arg in args:

            # first try: instance-based dispatch
            import collections.abc
            if isinstance(arg, collections.abc.Hashable):
                ndispatch = adispatch.fetch_inst(arg)
                if ndispatch:
                    adispatch = ndispatch
                    continue

            # second try: class-based dispatch in MRO order
            class_found = False
            for tcls in type(arg).__mro__:
                ndispatch = adispatch.fetch_class(tcls)
                if ndispatch:
                    adispatch = ndispatch
                    class_found = True
                    continue

            if class_found:
                continue

            # third try: default dispatch
            ndispatch = adispatch.fetch_default()
            if ndispatch:
                adispatch = ndispatch
            else:
                raise GenericError("Cannot dispatch on argument: {}".format(arg))

        if adispatch.dispatch_func:
            return adispatch.dispatch_func(*args)

        raise GenericError("No method found in generic")


# def generic(warn_on_redefinition=True):
#     def mk_generic(func):
#         # print("Wrapping the generic function.")
#         if not inspect.isfunction(func):
#             raise ValueError("Generics can only wrap functions.")
#         class GenericMethod(Generic):
#             def __init__(self, *args):
#                 super().__init__(*args)

#         GenericMethod.__doc__ = "Generic method:\n{}".format(func.__doc__)
#         generic_obj = GenericMethod(func.__name__, func.__doc__, func, warn_on_redefinition)
#         return generic_obj

#     return mk_generic

def generic(func):
    # print("Wrapping the generic function.")
    if not inspect.isfunction(func):
        raise ValueError("Generics can only wrap functions.")
    class GenericMethod(Generic):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    GenericMethod.__doc__ = "Generic method:\n{}".format(func.__doc__)
    generic_obj = GenericMethod(func.__name__, func.__doc__, func, warn_on_redefinition=True)
    return generic_obj

def method(generic):
    #print(generic)
    return generic.wrap

if __name__ == "__main__":

    class A:
        pass

    class B:
        pass

    class C:
        pass

    #import pdb; pdb.set_trace()

    @generic
    def gen_meth():
        """This is a generic method."""
        print("Generic method gen_meth() is extending")

    @method(gen_meth)
    def _(a : A):
        print("Call for class A")

    @method(gen_meth)
    def _(b : B):
        print("Call for class B")

    a = A()
    b = B()

    gen_meth(a)
    gen_meth(b)

    c = C()
    try:
        gen_meth(c)
        raise Error("Should not be here ...")
    except GenericError:
        print("Failed call for class C (as expected)")


    print("----")
    print("Enjoy Pylos !")



