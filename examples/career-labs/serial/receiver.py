"""Stream framing reference: fragmented UART bytes, CRC rejection and resync."""
import json


def crc8(data):
    crc=0
    for byte in data:
        crc ^= byte
        for _ in range(8): crc=((crc<<1)^0x07 if crc&0x80 else crc<<1)&255
    return crc


def encode(sequence,sensor,buttons):
    if not 0<=sequence<=255 or not 0<=sensor<=65535 or not 0<=buttons<=255:
        raise ValueError('Unsigned field range exceeded')
    data=bytes([0xa5,0x5a,1,sequence,sensor&255,sensor>>8,buttons])
    return data+bytes([crc8(data)])


class Receiver:
    def __init__(self): self.buffer=bytearray(); self.rejected=0
    def feed(self,data):
        self.buffer.extend(data); frames=[]
        while len(self.buffer)>=8:
            if self.buffer[:3]!=b'\xa5\x5a\x01' or crc8(self.buffer[:7])!=self.buffer[7]:
                del self.buffer[0]; self.rejected+=1; continue
            frames.append({'sequence':self.buffer[3],'sensor':self.buffer[4]|(self.buffer[5]<<8),'buttons':self.buffer[6]})
            del self.buffer[:8]
        return frames


if __name__=='__main__':
    receiver=Receiver(); first=encode(0,1023,1); broken=bytearray(encode(1,50,0)); broken[4]^=1
    stream=b'noise'+first+broken+encode(2,2048,0)
    results=[]
    for offset in range(0,len(stream),3): results.extend(receiver.feed(stream[offset:offset+3]))
    print(json.dumps({'source':'synthetic UART bytes','frames':results,'rejected_bytes':receiver.rejected}))
