import hashlib

class Packet:
    def __init__(self, packetType="dataPacket", seqno=0, dataLen=0, data=""):
        self.magicno = 0x497E
        self.type = packetType
        self.seqno = seqno
        self.dataLen = dataLen
        self.data = data
        self.checksum = hashlib.md5((data).encode()).hexdigest()