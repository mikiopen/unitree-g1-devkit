#ifndef G1_TEACHING_PROTOCOL_H
#define G1_TEACHING_PROTOCOL_H
#include <stdint.h>
#include <stddef.h>
/* A5 5A version=1 seq sensor_lo sensor_hi buttons crc8(first 7 bytes). */
#define FRAME_SIZE 8
uint8_t frame_crc8(const uint8_t *data, size_t length);
void frame_encode(uint8_t sequence, uint16_t sensor, uint8_t buttons, uint8_t out[FRAME_SIZE]);
int frame_decode(const uint8_t in[FRAME_SIZE], uint8_t *sequence, uint16_t *sensor, uint8_t *buttons);
#endif
