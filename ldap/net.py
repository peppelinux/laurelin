from socket import create_connection, error as SocketError
from urlparse import urlparse
from pyasn1.codec.ber.encoder import encode as berEncode
from pyasn1.codec.ber.decoder import decode as berDecode
from pyasn1.error import SubstrateUnderrunError

from rfc4511 import LDAPMessage, MessageID, ProtocolOp
from base import LDAPError

_nextSockID = 0

class LDAPSocket(object):
    RECV_BUFFER = 4096

    def __init__(self, hostURI, connectTimeout=5):
        parsedURI = urlparse(hostURI)
        if parsedURI.scheme == 'ldap':
            ap = parsedURI.netloc.split(':', 1)
            address = ap[0]
            if len(ap) == 1:
                port = 389
            else:
                port = int(ap[1])
        else:
            raise LDAPError('Unsupported scheme "{0}"'.format(parsedURI.scheme))
        try:
            self._sock = create_connection((address, port), connectTimeout)
        except SocketError as e:
            raise LDAPConnectionError('{0} ({1})'.format(e.strerror, e.errno))
        self._messageQueue = []
        self._nextMessageID = 1
        self._rawBuffer = ''

        global _nextSockID
        self.ID = _nextSockID
        _nextSockID += 1
        self.URI = hostURI
        self.bound = False
        self.unbound = False
        self.abandonedMIDs = []

    def sendMessage(self, op, obj):
        mID = self._nextMessageID
        lm = LDAPMessage()
        lm.setComponentByName('messageID', MessageID(mID))
        po = ProtocolOp()
        po.setComponentByName(op, obj)
        lm.setComponentByName('protocolOp', po)
        self._nextMessageID += 1
        self._sock.sendall(berEncode(lm))
        return mID

    def recvResponse(self, wantMessageID=0, limit=0, raw=''):
        ret = []
        raw = self._rawBuffer + raw
        self._rawBuffer = ''
        for obj in self._messageQueue:
            if (wantMessageID <= 0) or (obj.getComponentByName('messageID') == wantMessageID):
                ret.append(obj)
                self._messageQueue.remove(obj)
                if (limit > 0) and (len(ret) == limit):
                    return ret
        if wantMessageID in self.abandonedMIDs:
            return ret
        try:
            raw += self._sock.recv(LDAPSocket.RECV_BUFFER)
            while len(raw) > 0:
                response, raw = berDecode(raw, asn1Spec=LDAPMessage())
                if wantMessageID > 0:
                    if wantMessageID == response.getComponentByName('messageID'):
                        ret.append(response)
                    else:
                        self._messageQueue.append(response)
                else:
                    ret.append(response)
                if (limit > 0) and (len(ret) == limit):
                    self._rawBuffer = raw
                    break
            return ret
        except SubstrateUnderrunError:
            if (limit > 0) and (len(ret) == limit):
                self._rawBuffer = raw
                return ret
            ret += self.recvResponse(wantMessageID, limit, raw)
            return ret

    def close(self):
        return self._sock.close()

class LDAPConnectionError(LDAPError):
    pass
