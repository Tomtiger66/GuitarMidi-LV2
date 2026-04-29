#pragma once 
#include <logging.hpp>
#define OUTPUT_DIM 37
#define BUFFER_SIZE 256
#define NOTE_OFFSET 40
#define NUM_HARMONICS 4
#define NUM_NOTES 37
namespace GuitarMidi{

    struct AudioBuffer2D{
        int num_filters;
        int window_size;
        float* audio_buffer_2D;
    };
}