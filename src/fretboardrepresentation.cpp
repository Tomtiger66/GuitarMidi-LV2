#include "fretboardrepresentation.hpp"

GuitarMidi::FretBoardRepresentation::FretBoardRepresentation()
{
    m_frets.push_back(Fret(0, 82, 11, 147, 196, 247, 329));
    m_frets.push_back(Fret(1, 87, 117, 156, 208, 262, 349));
    m_frets.push_back(Fret(2, 92, 123, 165, 220, 277, 370));
    m_frets.push_back(Fret(3, 98, 131, 175, 233, 294, 392));
    m_frets.push_back(Fret(4, 104, 139, 185, 247, 311, 415));
    m_frets.push_back(Fret(5, 110, 147, 196, 262, 329, 440));
    m_frets.push_back(Fret(6, 117, 156, 208, 277, 349, 466));
    m_frets.push_back(Fret(7, 123, 165, 220, 294, 370, 494));
    m_frets.push_back(Fret(8, 131, 175, 233, 311, 392, 523));
    m_frets.push_back(Fret(9, 139, 185, 247, 329, 415, 554));
    m_frets.push_back(Fret(10, 147, 196, 262, 349, 440, 587));
    m_frets.push_back(Fret(11, 156, 208, 277, 370, 466, 622));
    m_frets.push_back(Fret(12, 165, 220, 294, 392, 494, 659));
}