#pragma once 
#define OUTPUT_DIM 89
namespace GuitarMidi{

    struct AudioBuffer2D{
        int num_filters;
        int window_size;
        float* audio_buffer_2D;
    };
}