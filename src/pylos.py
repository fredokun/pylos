
# Some experiments with a CLOS-inspired
# multi-dispatch mechanism for Python.

#{

# A typical CLOS example, solving the Expression problem

import inspect
import warnings
import math

class Shape:
    def perimeter(self):
        raise NotImplementedError()

class Square:
    def __init__(self, side):
        self.side = side

    def perimeter(self):
        return 4 * self.side

## Add a new kind of figure ?
## ==> easy

class Arbelos:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def perimeter(self):
        return ((math.pi * self.a) / 2.0) \
            + ((math.pi * self.b) / 2.0) \
            + ((math.pi * (self.a + self.b)) / 2.0)

## Add a new kind of operation ?
## ==> difficult

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

    def handle_instance(self, inst):
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
    def __init__(self, doc, warn_on_redefinition=True):
        self.doc = doc
        self.warn_on_redefinition = warn_on_redefinition

        self.dispatch = DispatchDict()

    def wrap(self, func):
        if not inspect.isfunction(func):
            raise ValueError("Generics can only wrap functions.")
        sig = inspect.signature(func)
        print("Signature is: {}".format(sig))

        arity = len(sig.parameters.values())
        print("Call arity = {}".format(arity))
        pdispatch = self.dispatch
        for (nth, param) in zip(range(1, arity + 1), sig.parameters.values()):
            print("Parameter #{}: {}".format(nth, param.name))
            print("   ==> annot: {}".format(param.annotation))
            print("   ==> kind: {}".format(param.kind))

            if param.annotation == param.empty:
                print("      ==> empty annotation")
                pdispatch = pdispatch.handle_default()
            elif inspect.isclass(param.annotation):
                print("      ==> it's a class !")
                pdispatch = pdispatch.handle_class(param.annotation)
            else:
                print("      ==> it's an object")
                pdispatch = pdispatch.handle_inst(param.annotation)

        pdispatch.register_func(sig, func)

    def __call__(self, *args, **kwargs):
        if kwargs:
            raise GenericError("Keyword argument not accepted in generic calls.")
        # import pdb ; pdb.set_trace()
        adispatch = self.dispatch
        for arg in args:
            tcls = type(arg)
            ndispatch = adispatch.fetch_class(tcls)
            if ndispatch:
                adispatch = ndispatch
                continue

            ndispatch = adispatch.fetch_inst(arg)
            if ndispatch:
                adispatch = ndispatch
                continue

            ndispatch = adispatch.fetch_default()
            if ndispatch:
                adispatch = ndispatch
            else:
                raise GenericError("Cannot dispatch on argument: {}".format(arg))

        if adispatch.dispatch_func:
            return adispatch.dispatch_func(*args)

        raise GenericError("No method found in generic")

perimeter = Generic("Compute the perimeter of a shape")

#print("Dispatch 1 = {}".format(perimeter.dispatch))

def method(generic):
    #print(generic)
    return generic.wrap

@method(perimeter)
def perimeter_for_square(self):
    return self.side * 4

#print("Dispatch 2 = {}".format(perimeter.dispatch))


@method(perimeter)
def perimeter_for_arbelos(self: Arbelos):
    return ((math.pi * self.a) / 2.0) \
            + ((math.pi * self.b) / 2.0) \
            + ((math.pi * (self.a + self.b)) / 2.0)


#print("Dispatch 3 = {}".format(p0erimeter.dispatch))


#}


if __name__ == "__main__":
    sq = Square(3)
    print("Perimeter = {}".format(sq.perimeter()))
    arb = Arbelos(3, 4)
    print("Perimeter = {}".format(arb.perimeter()))


    print("Perimeter = {}".format(perimeter(sq)))
    print("Perimeter = {}".format(perimeter(arb)))

