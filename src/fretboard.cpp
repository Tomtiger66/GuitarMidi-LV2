/* GuitarMidi-LV2 Library
 * Copyright (C) 2022 Gerald Mwangi
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General
 * Public License along with this program; if not, write to the
 * Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
 * Boston, MA  02110-1301  USA
 */
#include <fretboard.hpp>
#include <omp.h>

using namespace GuitarMidi;
FretBoard::FretBoard(LV2_URID_Map *map, float samplerate)
{
    m_midioutput = make_shared<MidiOutput>(map);
    m_frets.push_back(Fret(0,82,11,147,196,247,329));
    m_frets.push_back(Fret(1,87,117,156,208,262,349));
    m_frets.push_back(Fret(2,92,123,165,220,277,370));
    m_frets.push_back(Fret(3,98,131,175,233,294,392));
    m_frets.push_back(Fret(4,104,139,185,247,311,415));
    m_frets.push_back(Fret(5,110,147,196,262,329,440));
    m_frets.push_back(Fret(6,117,156,208,277,349,466));
    m_frets.push_back(Fret(7,123,165,220,294,370,494));
    m_frets.push_back(Fret(8,131,175,233,311,392,523));
    m_frets.push_back(Fret(9,139,185,247,329,415,554));
    m_frets.push_back(Fret(10,147,196,262,349,440,587));
    m_frets.push_back(Fret(11,156,208,277,370,466,622));
    m_frets.push_back(Fret(12,165,220,294,392,494,659));


}





void FretBoard::setAudioInput(const float *input)
{
    // for (auto notecl : m_noteClassifiers)
    // {
    //     notecl->input = input;
    // }
}

void FretBoard::setAudioOutput(float *output)
{

}

void FretBoard::setMidiOutput(LV2_Atom_Sequence *output)
{
    // if (m_midioutput)
    // {
    //     m_midioutput->setMidiOutput(output);

    //     for (auto notecl : m_noteClassifiers)
    //     {
    //         notecl->setMidiOutput(m_midioutput);
    //     }
    // }
}

void FretBoard::initialize()
{
    // if (m_midioutput)
    //     m_midioutput->initializeSequence();
    // omp_set_num_threads(1);
    // for (auto notecl : m_noteClassifiers)
    // {
    //     notecl->initialize();
    // }
}

void FretBoard::finalize()
{
    // for (auto notecl : m_noteClassifiers)
    // {
    //     notecl->finalize();
    // }
}

void FretBoard::process(int nsamples)
{

}