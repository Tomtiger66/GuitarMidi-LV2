#pragma once 
namespace GuitarMidi{

    struct AudioBuffer2D{
        int num_filters;
        int window_size;
        float* audio_buffer_2D;
    };
}