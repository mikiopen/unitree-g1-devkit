#include "protocol.h"
uint8_t frame_crc8(const uint8_t *data, size_t length) {
    uint8_t crc = 0;
    for (size_t i = 0; i < length; ++i) {
        crc ^= data[i];
        for (unsigned bit = 0; bit < 8; ++bit)
            crc = (uint8_t)((crc & 0x80) ? ((crc << 1) ^ 0x07) : (crc << 1));
    }
    return crc;
}
void frame_encode(uint8_t seq, uint16_t sensor, uint8_t buttons, uint8_t out[FRAME_SIZE]) {
    out[0]=0xa5; out[1]=0x5a; out[2]=1; out[3]=seq;
    out[4]=(uint8_t)sensor; out[5]=(uint8_t)(sensor >> 8); out[6]=buttons;
    out[7]=frame_crc8(out,7);
}
int frame_decode(const uint8_t in[FRAME_SIZE], uint8_t *seq, uint16_t *sensor, uint8_t *buttons) {
    if (in[0]!=0xa5 || in[1]!=0x5a || in[2]!=1 || frame_crc8(in,7)!=in[7]) return 0;
    *seq=in[3]; *sensor=(uint16_t)(in[4] | ((uint16_t)in[5] << 8)); *buttons=in[6];
    return 1;
}
