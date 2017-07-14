from __future__ import absolute_import
from .errors import LDAPError, LDAPExtensionError, LDAPSupportError
from .rfc4511 import (
    LDAPOID,
    Criticality,
    Control as _Control,
    Controls,
    ControlValue,
)
import six

_registeredControls = {}

# this gets automatically generated by the reserve_kwds.py script
_reservedKwds = set(['DN', 'OID', 'attr', 'attrs', 'attrsDict', 'attrsOnly', 'baseDN', 'cleanAttr', 'derefAliases', 'dn', 'fetchResultRefs', 'filter', 'followReferrals', 'ldapConn', 'limit', 'mID', 'mech', 'modlist', 'newParent', 'newRDN', 'password', 'rdnAttr', 'relativeSearchScope', 'requireSuccess', 'scope', 'searchTimeout', 'self', 'tag', 'username', 'value'])

def _register(ctrl):
    if ctrl.keyword in _reservedKwds:
        raise LDAPExtensionError('Control keyword "{0}" is reserved'.format(ctrl.keyword))
    if ctrl.keyword in _registeredControls:
        raise LDAPExtensionError('Control keyword "{0}" is already defined'.format(ctrl.keyword))
    _registeredControls[ctrl.keyword] = ctrl

def _processCtrlKwds(method, kwds, supportedCtrls, defaultCriticality, final=False):
    """Process keyword arguments for registered controls, returning a protocol-level Controls

     Removes entries from kwds as they are used, allowing the same dictionary to be passed on
     to another function which may have statically defined arguments. If final is True, then a
     TypeError will be raised if all kwds are not exhausted.
    """
    i = 0
    ctrls = Controls()
    for kwd in list(kwds.keys()):
        if kwd in _registeredControls:
            ctrl = _registeredControls[kwd]
            if ctrl.method != method:
                raise LDAPError('Control keyword {0} not allowed for method "{1}"'.format(kwd, method))
            ctrlValue = kwds.pop(kwd)
            if isinstance(ctrlValue, critical):
                criticality = True
                ctrlValue = ctrlValue.value
            elif isinstance(ctrlValue, optional):
                criticality = False
                ctrlValue = ctrlValue.value
            else:
                criticality = defaultCriticality
            if criticality and (ctrl.OID not in supportedCtrls):
                raise LDAPSupportError('Critical control keyword {0} is not supported by the server'.format(kwd))
            ctrls.setComponentByPosition(i, ctrl.prepare(ctrlValue, criticality))
            i += 1
    if final and (len(kwds) > 0):
        raise TypeError('Unhandled keyword arguments: {0}'.format(', '.join(kwds.keys())))
    if i > 0:
        return ctrls
    else:
        return None


class Control(object):
    # Controls are exposed by allowing additional keyword arguments on particular methods
    method = ''  # name of the method which this control is used with
    keyword = '' # keyword argument name
    OID = ''     # OID of the control

    def prepare(self, ctrlValue, criticality):
        """Accepts string controlValue and returns an rfc4511.Control instance"""
        c = _Control()
        c.setComponentByName('controlType', LDAPOID(self.OID))
        c.setComponentByName('criticality', Criticality(criticality))
        if not isinstance(ctrlValue, six.string_types):
            raise TypeError('Control value must be string')
        if len(ctrlValue) > 0:
            c.setComponentByName('controlValue', ControlValue(ctrlValue))
        return c

    @staticmethod
    def REGISTER_GENERIC(method, keyword, OID):
        """Call this to define a simple control that only needs a string controlValue"""
        c = Control()
        c.method = method
        c.keyword = keyword
        c.OID = OID
        _register(c)

    @staticmethod
    def REGISTER(cls):
        """If extending the Control class (to accept complex controlValues), use this as a class
         decorator
        """
        if issubclass(cls, Control):
            if not cls.method:
                raise ValueError('no method set on class {0}'.format(cls.__name__))
            if not cls.keyword:
                raise ValueError('no keyword set on class {0}'.format(cls.__name__))
            if not cls.OID:
                raise ValueError('no OID set on class {0}'.format(cls.__name__))
            _register(cls())
            return cls
        else:
            raise TypeError('class {0} must be subclass of Control'.format(cls.__name__))


class critical(object):
    """used to mark controls with criticality"""
    def __init__(self, value):
        self.value = value


class optional(object):
    """used to mark controls as not having criticality"""
    def __init__(self, value):
        self.value = value