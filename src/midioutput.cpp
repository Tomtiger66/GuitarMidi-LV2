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
#include <midioutput.hpp>
#include <mutex>
using namespace GuitarMidi;

MidiOutput::MidiOutput(LV2_URID_Map *map)
    : m_midioutput(nullptr), m_frames(0)
{
    if (map) {
        lv2_atom_forge_init(&m_forge, map);
        m_midiEvent = map->map(map->handle, LV2_MIDI__MidiEvent);
    } else {
        m_midiEvent = 0;
    }
}

bool MidiOutput::forge_midimessage(const uint8_t *const buffer,
                                   uint32_t size, int64_t frames)
{
    std::lock_guard<std::mutex> lock(m_mutex);

    if (!m_midioutput) {
        fprintf(stderr, "MidiOutput::forge_midimessage: output sequence not set\n");
        return false;
    }

    if (!buffer || size == 0) {
        fprintf(stderr, "MidiOutput::forge_midimessage: invalid buffer/size\n");
        return false;
    }

    LV2_Atom midiatom;
    midiatom.type = m_midiEvent;
    midiatom.size = size;

    if (0 == lv2_atom_forge_frame_time(&m_forge, frames)) {
        fprintf(stderr, "MidiOutput: lv2_atom_forge_frame_time failed\n");
        return false;
    }

    if (0 == lv2_atom_forge_raw(&m_forge, &midiatom, sizeof(LV2_Atom))) {
        fprintf(stderr, "MidiOutput: lv2_atom_forge_raw(midatom) failed\n");
        return false;
    }

    if (0 == lv2_atom_forge_raw(&m_forge, buffer, size * sizeof(uint8_t))) {
        fprintf(stderr, "MidiOutput: lv2_atom_forge_raw(buffer) failed\n");
        return false;
    }

    lv2_atom_forge_pad(&m_forge, size * sizeof(uint8_t) + sizeof(LV2_Atom));

    return true;
}

void MidiOutput::setMidiOutput(LV2_Atom_Sequence *output)
{
    
    m_midioutput = output;
    initializeSequence();
}

void MidiOutput::initializeSequence()
{
    std::lock_guard<std::mutex> lock(m_mutex);
    if (m_midioutput) {
        const uint32_t out_capacity = m_midioutput->atom.size;
        lv2_atom_forge_set_buffer(&m_forge, reinterpret_cast<uint8_t *>(m_midioutput), out_capacity);
        lv2_atom_forge_sequence_head(&m_forge, &m_frame, 0);
        m_frames = 0;
    }
}

void MidiOutput::sendMidiMessage(uint8_t midinote[3], int64_t frames)
{
    if (!midinote) return;

    // Use provided frames if > 0 otherwise advance by 1
    int64_t at_frame = (frames > 0) ? frames : m_frames;

    bool sent = forge_midimessage(midinote, 3, at_frame);
    if (!sent) {
        fprintf(stderr, "MidiOutput: Failed to send midinote (%u,%u,%u)\n", midinote[0], midinote[1], midinote[2]);
    }

    // Advance internal frame counter conservatively
    m_frames += (frames > 0) ? frames : 1;
}