#include "protocol.h"
#include <assert.h>
int main(void) {
    uint8_t frame[FRAME_SIZE], seq, buttons; uint16_t sensor;
    frame_encode(255,1023,1,frame);
    assert(frame_decode(frame,&seq,&sensor,&buttons));
    assert(seq==255 && sensor==1023 && buttons==1);
    frame[4]^=1; assert(!frame_decode(frame,&seq,&sensor,&buttons));
    assert(frame_crc8((const uint8_t *)"123456789",9)==0xf4);
    return 0;
}
