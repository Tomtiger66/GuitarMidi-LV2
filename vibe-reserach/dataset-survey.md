https://hackmd.io/@soravolk/ryW-jw3nY


Try  HackMD Logo HackMD
A survey of electric guitar related datasets

    GUITAR-FX-DIST
        Release: November 30, 2020
        Reference:
            Guitar Effects Recognition and Parameter Estimation with Convolutional Neural Networks
        Attribute:
            Samples length: 2 sec
            Unprocessed：
                624 monophonic notes
                420 polyphonic (2, 3 and 4 notes intervals and chords)
                2 guitars, with up to 2 pick-up settings and up to 3 plucking styles (finger pluck - hard, finger pluck - soft, pick)
                Schecter Diamond C-1 Classic
                Chester Stratocaster
                from IDMT-SMT-Audio-Effects
            Processed：
                Mono Discrete: ~160k
                Poly Discrete: ~110k
                Mono Continuous: 140k
                Poly Continuous: 140k
                the most common and representative settings a person might use

    GuitarSet
        Release: 2018
        Reference:
            Guitarset: A Dataset for Guitar Transcription
        Attribute:
            provide recordings of the individual strings
            time-aligned annotations of pitch contours, string and fret positions, chords, beats, downbeats, and playing style
            360 excerpts that are close to 30 seconds in length
            annotation
                6 pitch_contour annotations (1 per string)
                6 midi_note annotations (1 per string)
                1 beat_position annotation
                1 tempo annotation
                2 chord annotations (instructed and performed)*

    AudioSet
        Release: 2017
        Reference:
            Audio Set: An ontology and human-labeled dataset for audio events
        Attribute:
            10-seconds youtube clips
            estimated accuracy: 80%
        Might be helpful to the solo detection

    GuitarSoloDetection
        release: 2017
        reference:
            AES International Conference on Semantic Audio. Audio Engineering Society, 2017
        Attribute:
            containing 60 full-length rock songs
            annotated the location of the guitar solos within the song
        Might be useful for the solo detection

    IDMT-SMT-Guitar
        Release: 2014
        Reference:
            Automatic Tablature Transcription of Electric Guitar Recordings by Estimation of Score- and Instrument-related Parameters
        Attribute:
            7 different guitars in standard tuning and varying pick-up
            different string measures to ensure diversification in electric and acoustic guitars
            record with audio interfaces directly connected to the guitar output or in one case to a condenser microphone
            4 subsets
                playing techniques
                400 monophonic and polyphonic note events
                five short monophonic and polyphonic guitar recordings
                64 short musical pieces grouped by genre. Each piece has been recorded at two different tempi
        The third and the fourth subsets might be useful for the solo detection

    Guitar playing techniques dataset (GPT)
        release: 2014

    Physically_augmented_guitar_chord_dataset
        Release:
        Attribute:
            recorded directly from the guitar playing robot
            consists of 12 root notes and 10 types of chord quality in a total of 97 classes of chords
            Each chord was played individually with five types of stroking patterns.
        This dataset is related to only chords that might not be suitable for the solo detection

Last changed by 
 
soravolk·
0
1499
Read more
Empire

＃＃Data model
Mar 24, 2024
Read more from soravolk
Published on HackMD
