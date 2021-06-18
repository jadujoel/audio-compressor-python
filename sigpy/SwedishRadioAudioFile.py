""" TODO:
fmtChunk: weird indexes in array - done
Bext: reserved, reserved umid, check into, there is something in reserved, what is it? - done
DataChunk: what happens after frame header??
levlChunk: "unknown part"
auxChunk: what is saved here? - plotting data

Question: What chunks are written in a BWF file?
Ánswer: Broadcast Wave Format (BWF) includes a "bext" (broadcast extension) chunk.
In the case of an MPEG data, a "mext" chunk as well as a "fmt" chunk that is actually an element of the WAVE format.
Also a "fact chunk and a "cue" chunk (in the case of markers).
For the waveform there is a "levl" chunk (Digas writes/reads from a DAVID exclusive "aux" chunk).
The Multitrack editors 'cut list data' is stored in a DAVID-exclusive "DAVD" chunk.

"""
#import ctypes
# ctypes.c_int16
# ctypes.c_char
#import struct

def intb(byte):
    return int.from_bytes(byte, byteorder = 'little')

def byte_to_bits(byte, byteorder='little'):
    bits = ""
    for i in range(8):
        bits = bits + str(bit_is_set(byte, i))
    if byteorder=='little':
        bits = bits[::-1]

    return bits

def bytes_to_bits(bytearr):
    allbits = ""
    for byte in bytearr:
        allbits = allbits + byte_to_bits(byte)
    return allbits

def byte_to_bit(b):
    return 8*b

def magic(numList):         # [1,2,3]
    s = map(str, numList)   # ['1','2','3']
    s = ''.join(s)          # '123'
    s = int(s)              # 123
    return s

def bits(byte):
    byte = (ord(b) for b in byte)
    for b in byte:
        for i in range(8):
            yield (b >> i) & 1

def bit_is_set(x, n):
    return int(x & 2 ** n != 0)

class Chunk:
    def __init__(self):
        self.BextChunk = BextChunk
        self.fmtChunk = fmtChunk
        self.mextChunk = mextChunk
        self.dataChunk = dataChunk
        self.levlChunk = levlChunk
        self.cueChunk = cueChunk
        self.LISTchunk = LISTchunk
        self.r64mChunk = r64mChunk
        self.auxChunk = auxChunk
        self.factChunk = factChunk

class BextChunk(Chunk):
    """
        # http://bwfmetaedit.sourceforge.net/bext.html
    ASCII string (maximum 256 characters) containing a free description of the sequence.
    To help applications which only display a short description,
    it is recommended that a resume of the description is contained in the first 64 characters,
    and the last 192 characters are used for details.
    """

    def __init__(self, ckData):
        #print('\nBEXT')
        self.description            =      ckData[0  :256].decode('iso-8859-1')
        self.originator             =      ckData[256:288].decode('iso-8859-1')
        self.originatorReference    =      ckData[288:320].decode('iso-8859-1')
        self.originationDate        =      ckData[320:330].decode('ascii')

        # Eight ASCII characters containing the time of creation of the audio sequence. The format is HH-MM-SS (hours-minutes-seconds).
        self.originationTime        =      ckData[330:338].decode('ascii')

        # This field contains the timecode of the sequence.
        # It is a 64-bit value which contains the first sample count since midnight.
        # The number of samples per second depends on the sample frequency which is defined in the field <nSamplesPerSec> from the <format chunk>.
        self.TimeReference          = intb(ckData[338:346])
        self.TimeReferenceLow       = intb(ckData[338:342]) # First sample count since midnight, low word
        self.TimeReferenceHigh      = intb(ckData[342:346]) # First sample count since midnight, high word
        # BWF Version 1
        # Version 1 differs from Version 0 only in that 64 of the 254 reserved bytes in Version 0 are used to contain a SMPTE UMID [1].
        self.bextVersion            = intb(ckData[346:348]) # version of bext
        self.smpteumid              =      ckData[348:412]
        self.smpteumidhex           = self.smpteumid.hex()
        #### Only used in Version 2
        self.loudnessValue          = intb(ckData[412:414])
        self.loudnessRange          = intb(ckData[414:416])
        self.maxTruePeakLevel       = intb(ckData[416:418])
        self.maxMomentaryLoudness   = intb(ckData[418:420])
        self.maxShortTermLoudness   = intb(ckData[420:422])
        self.reserved               =      ckData[422:602]
        self.codingHistory          =      ckData[602:].decode('ascii')

    def print(self):
        print('')
        for k, v in self.__dict__.items():
            print(' ', k, '=', v)

class fmtChunk(Chunk):
    # Definition of WAVEFORMATX https://github.com/tpn/winddk-8.1/blob/master/Include/shared/mmreg.h
    def __init__(self, fmtData):
        # https://forum.dbpoweramp.com/showthread.php?3285-The-Lengthof-a-WAV-file
        # https://tech.ebu.ch/docs/tech/tech3285s1.pdf
        #print('\nWAVE Format Chunk - fmt-ck')

        self.wFormatTagDict = {
                        0 : 'UNKNOWN',
                        1 : 'PCM',
                        2 : 'ADPCM',
                        3 : 'IEEE_FLOAT',
                        48 : 'DOLBY_AC2',
                        49 : 'GSM610',
                        50 : 'MSNAUDIO',
                        80 : 'MPEG',
                        85 : 'MPEGLAYER3',
                        146 : 'DOLBY_AC3_SPDIF',
                        255 : 'RAW_AAC1',
                        352 : 'MSAUDIO1',
                        353 : 'WMA',
                        354 : 'WMA_PRO',
                        355 : 'WMA_LOSSLESS',
                        356 : 'WMA_SPDIF',
                        5632 : 'MPEG_ADTS_AAC',
                        5633 : 'MPEG_RAW_AAC',
                        5634 : 'MPEG_LOAS',
                        5648 : 'MPEG_HEAAC',
                        -2 : 'EXTENSIBLE'}

        self.wFormatTag         = intb(fmtData[0:2]) # Defines the type of Wave File
        self.wFormatType        = self.wFormatTagDict[self.wFormatTag]

        self.nChannels          = intb(fmtData[2 :4])
        self.nSamplesPerSec     = intb(fmtData[4 :8]) # Specifies the sampling frequency, if the sampling frequency is fixed. If it is variable, set this field to zero.
        self.nAvgBytesPerSec    = intb(fmtData[8 :12]) # Specifies the average data rate. If variable bitrate encoding is used under layer 3, the value might not be a legal MPEG-1 bit rate.
        self.nBlockAlign        = intb(fmtData[12:14]) # Frame size : Layers 2 and 3: (int)(144 * bitrate / sampling frequency)
        self.wBitsPerSample     = intb(fmtData[14:16]) # Only for linear files, otherwise set to 0
        self.cbSize             = intb(fmtData[16:18]) # size of extra info

        # Format Specific Field
        if self.wFormatType == 'MPEG':

            self.fwHeadLayer    = intb(fmtData[18:20]) # Mpeg Layer 1/2/3
            self.dwHeadBitrate  = intb(fmtData[20:24]) # bitrate
            self.fwHeadMode     = intb(fmtData[24:26])
            self.fwHeadModeExt  = intb(fmtData[26:28])
            self.wHeadEmphasis  = intb(fmtData[28:30])
            self.fwHeadFlags    = intb(fmtData[30:32]) # see fwHeadFlagsType
            self.dwPTSLow       = intb(fmtData[32:36]) # Specifies the least signifcant 32 bits of the presentation time stamp (PTS) of the first frame of the audio stream.
            self.dwPTSHigh      = intb(fmtData[36:40]) # Specifies the most significant bit of the PTS. The dwPTSLow and dwPTSHigh fields can be treated as a single 64-bit value.

            if self.fwHeadLayer     == 1:
                self.fwHeadLayerType = 'ACM_MPEG_LAYER1'
            elif self.fwHeadLayer   == 2:
                self.fwHeadLayerType = 'ACM_MPEG_LAYER2'
            elif self.fwHeadLayer   == 4:
                self.fwHeadLayerType = 'ACM_MPEG_LAYER4'

            if self.fwHeadMode     == 1:
                self.fwHeadModeType = 'ACM_MPEG_STEREO'
            elif self.fwHeadMode   == 2:
                self.fwHeadModeType = 'ACM_MPEG_JOINTSTEREO'
            elif self.fwHeadMode   == 4:
                self.fwHeadModeType = 'ACM_MPEG_DUALCHANNEL'
            elif self.fwHeadMode   == 8:
                self.fwHeadModeType = 'ACM_MPEG_SINGLECHANNEL'

            if self.fwHeadModeExt     == 1:  #b'\x00\x01':
                self.fwHeadModeExtCode = '00'
                self.fwHeadModeExtType = 'sub–bands 4–31 in intensity stereo'
            elif self.fwHeadModeExt   == 2: #b'\x00\x02':
                self.fwHeadModeExtCode = '01'
                self.fwHeadModeExtType = 'sub–bands 8–31 in intensity stereo'
            elif self.fwHeadModeExt   == 4: #b'\x00\x04':
                self.fwHeadModeExtCode = '10'
                self.fwHeadModeExtType = 'sub–bands 12–31 in intensity stereo'
            elif self.fwHeadModeExt   == 8: #b'\x00\x08':
                self.fwHeadModeExtCode = '11'
                self.fwHeadModeExtType = 'sub–bands 16–31 in intensity stereo'

            if self.wHeadEmphasis == 0:
                self.wHeadEmpasisType = 'no emphasis'
            elif self.wHeadEmphasis == 1:
                self.wHeadEmpasisType = '50/15 ms emphasis'
            elif self.wHeadEmphasis == 2:
                self.wHeadEmpasisType = 'reserved'
            elif self.wHeadEmphasis == 3:
                self.wHeadEmpasisType = 'CCITT J.17'

            if self.fwHeadFlags   == 1:
                self.fwHeadFlagsType = 'ACM_MPEG_SINGLECHANNEL'
            elif self.fwHeadFlags == 2:
                self.fwHeadFlagsType = 'ACM_MPEG_COPYRIGHT'
            elif self.fwHeadFlags == 4:
                self.fwHeadFlagsType = 'ACM_MPEG_ORIGINALHOME'
            elif self.fwHeadFlags == 8:
                self.fwHeadFlagsType = 'ACM_MPEG_PROTECTIONBIT'
            elif self.fwHeadFlags == 10:
                self.fwHeadFlagsType = 'ACM_MPEG_ID_MPEG1'

    def print(self):
        print('')
        for k, v in self.__dict__.items():
            print(' ', k, '=', v)

class mextChunk(Chunk):
    def __init__(self, mextData):
        self.soundInfo                      = mextData[0:2] # /* more information about sound */
        self.soundInfo_homoSoundData        = bit_is_set(self.soundInfo[0], 0)
        self.soundInfo_padding              = bit_is_set(self.soundInfo[0], 1)
        self.soundInfo_paddingZero_sr44or22 = bit_is_set(self.soundInfo[0], 2)
        self.soundInfo_freeFormat           = bit_is_set(self.soundInfo[0], 3)
        # what do the other 14 bits do???
        self.frameSize                      = intb(mextData[2:4]) # /* nominal size of a frame */
        self.ancillaryDataLength            = intb(mextData[4:6]) #
        self.ancillaryDataDef               = mextData[6:8] # /* Type of ancillary data */
        self.ancillary_energy_left          = bit_is_set(self.ancillaryDataDef[0], 0)
        self.ancillary_private              = bit_is_set(self.ancillaryDataDef[0], 1)
        self.ancillary_energy_right         = bit_is_set(self.ancillaryDataDef[0], 2)
        self.ancillary_adr                  = bit_is_set(self.ancillaryDataDef[0], 3)
        self.ancillary_dab                  = bit_is_set(self.ancillaryDataDef[0], 4)
        self.ancillary_j52                  = bit_is_set(self.ancillaryDataDef[0], 5)
        self.ancillary_reserve              = 'bits 5 to 15 reserved for future use'
        self.other_reserved                 = mextData[8:12].decode('ascii') # CHAR /* Reserved for future use; set to null */

    def print(self):
        print(' self.soundInfo :', self.soundInfo)
        print('  Homogeneous sound data :', self.soundInfo_homoSoundData) # A non homogeneous file contains a sequence of MPEG frames without any restriction.
        if self.soundInfo_homoSoundData: print('    Homogeneous sound data')
        else: print('    non homogeneous sound data')

        print('  self.soundInfo_padding :', self.soundInfo_padding)
        if self.soundInfo_padding: print('    Padding bit is used in the file so may alternate between ’0’or ’1’ ')
        else: print('    Padding bit is set to ’0’ in the whole file')

        print('  self.soundInfo_paddingZero_sr44or22 :', self.soundInfo_paddingZero_sr44or22)
        if self.soundInfo_paddingZero_sr44or22: print('    The file contains a sequence of frames with padding bit set to ’0’ and sample frequency equal to 22.05 or 44.1 kHz')
        else: print('    The file DOES NOT contain a sequence of frames with padding bit set to ’0’ and sample frequency equal to 22.05 or 44.1 kHz')

        print('  self.soundInfo_freeFormat :', self.soundInfo_freeFormat)
        if self.soundInfo_freeFormat: print('    Free format is used.')
        else: print('    No free format audio frame')

        print(' frameSize :', self.frameSize, " : Frame size is always 1152 samples for Layer II, This field has a meaning only for homogeneous files, otherwise it is set to ’0’.")
        print('\n Ancillary:')
        print('  ancillaryDataLength :', self.ancillaryDataLength, ': 16 bit number giving minimal number of known bytes for ancillary data in the full sound file. The value is relative from the end of the audio frame.')
        print('  ancillaryDataDef :', self.ancillaryDataDef.decode('ascii'))
        print('  ancillary_energy_left :', self.ancillary_energy_left, 'Energy of left channel present in ancillary data')
        print('  ancillary_private :', self.ancillary_private, 'A private byte is free for internal use in ancillary data')
        print('  ancillary_energy_right :', self.ancillary_energy_right, 'Energy of right channel present in ancillary data')
        print('  ancillary_adr :', self.ancillary_adr, 'reserved for future use for ADR data')
        print('  ancillary_dab :', self.ancillary_dab, 'reserved for future use for DAB data')
        print('  ancillary_j52 :', self.ancillary_j52, 'reserved for future use for J 52 data')
        print('  ancillary_reserve :', self.ancillary_reserve)
        print('\n other reserved :', self.other_reserved)

class dataChunk(Chunk):
    def __init__(self, data):
        self.dataFrames = {}
        self.numFrames = int(len(data)/1152)
        for i in range(self.numFrames):
            frame = dataFrame(data[i*1152 : i*1152+1152])
            self.dataFrames[f'frame {i}'] = frame
        #self.len_samples = len(self.samples)
        #self.test = len(self.samples)/1120

    def print(self):
        for k, v in self.__dict__.items():
            if k != 'signal':
                print(k, '=', v)

class dataFrame(dataChunk):
    def __init__(self, data):
        # frame len is calculated with 144 * bitrate(384) / sample rate (48000) = 1152
        self.fh = data[0:4] #frame header
        self.fhb                   = bytes_to_bits(self.fh)
        self.frame_sync            = self.fhb[0:11]
        self.mpeg_audio_version_ID = self.fhb[11:13]
        self.layer_description     = self.fhb[13:15]
        self.protection_bit        = self.fhb[15]
        self.bitrate_index         = self.fhb[16:20]
        self.sampling_rate         = self.fhb[20:22]
        self.padding_bit           = self.fhb[22]
        self.private_bit           = self.fhb[23]
        self.channel_mode          = self.fhb[24:26]
        self.mode_extension        = self.fhb[26:28]
        self.copyright             = self.fhb[28]
        self.original              = self.fhb[29]
        self.emphasis              = self.fhb[30:31]
        self.original              = self.fhb[31]

        self.crc = data[4:6]
        self.bit_allocation = data[6:134]
        self.scale_factors = data[134:518]
        self.samples = data[518:]

    def print(self):
        print('all bits in frame header', self.fhb)
        print('frame_sync', self.frame_sync)
        print('mpeg_audio_version_ID:', self.mpeg_audio_version_ID, ' - 00 = MPEG Version 2.5, 01 = reserved, 10 = MPEG Version 2 (ISO/IEC 13818-3) , 11 = MPEG Version 1 (ISO/IEC 11172-3)')
        print('layer_description:', self.layer_description, ' - 00 = reserved, 01 = Layer III, 10 = Layer II , 11 = Layer I')
        print('protection_bit:', self.protection_bit, ' - 0 = Protected by CRC (16bit crc follows header), 1 = Not protected')
        print('bitrate_index:', self.bitrate_index, ' expected = 1100 or 1110 = 384kbits')
        print('sampling_rate:', self.sampling_rate, ' - 00 = 44100, 01 = 48000, 10 = 32000 , 11 = reserv')
        print('padding_bit:', self.padding_bit, ' - 0 = frame is not padded, 1 = frame is padded with one extra slot')
        print('private_bit:', self.private_bit, ' - Private bit. It may be freely used for specific needs of an application, i.e. if it has to trigger some application specific events.')
        print('channel_mode:', self.channel_mode, ' - 00 = stereo, 01 = joint stereo, 10 = dual channel , 11 = single channel(mono)')
        print('mode_extension:', self.mode_extension, ' - 00 = bands 4-31, 01 = bands 8-31, 10 = bands 12-31 , 11 = bands 16-31, only if joint stereo')
        print('copyright:', self.copyright, ' - 0 = Audio not copyrighted, 1 = Audio is copyrighted')
        print('original:', self.original, ' - 0 = Copy of original media, 1 = Original media')
        print('emphasis:', self.emphasis, ' - 00 = none, 01 = 50/15ms, 10 = reserved, 11 = CCIT J.17')
        print('original:', self.original, ' - 0 = Copy of original media, 1 = Original')

class levlChunk(Chunk):
    def __init__(self, levlData):
        # https://tech.ebu.ch/docs/tech/tech3285s3.pdf

        self.dwVersion          = bytes_to_bits(levlData[0:4])
        self.dwFormat           = intb(levlData[4:8]) # 1 = unsigned char for each peak point, 2 = unsigned short int for each peak point
        self.dwPointsPerValue   = intb(levlData[8:12]) # It is recommended to use two peak points (dwPointsPerValue = 2) because unsymmetrical wave forms (e.g. a DC offset) will be correctly displayed.
        self.dwBlockSize        = intb(levlData[12:16]) # This number is variable. The default and recommended block size is 256.
        self.dwPeakChannels     = intb(levlData[16:20])

        # The number of peak frames. The number of peak frames is the integer obtained by rounding down the following calculation:
        # dwNumPeakFrames = int(floor((numAudioFrame + dwBlockSize) / dwBlockSize))
        self.dwNumPeakFrames    = intb(levlData[20:24])
        # The peak-of-peaks is first audio sample whose absolute value is the maximum value of the entire audio file.
        self.dwPosPeakOfPeaks   = intb(levlData[24:28]) # If the value is 0xFFFFFFFF = 4294967295, then that means that the peak of the peaks is unknown
        if self.dwPosPeakOfPeaks == 4294967295:
            self.dwPosPeakOfPeaksKnown = False
        else: self.dwPosPeakOfPeaksKnown = True

        # Offset of the peak data from the start of the header. Usually this equals to the size of the header, but it could be higher.
        self.dwOffsetToPeaks    = intb(levlData[28:32])
        self.strTimestamp       = levlData[32:56].decode('ascii') # 23 bytes
        #  "2000:08:24:13:55:40:967"

        #b'\xa0'.decode('utf-8')
        self.unknown                 = levlData[56:60]
        self.test = intb(levlData[56:60])
        #self.unknown_int                 = intb(levlData[56:60])

        self.reserved           = levlData[60:120].decode('ascii')
        self.peak_envelope_data = levlData[self.dwOffsetToPeaks-8:]

        self.peakEnvArr = [intb(self.peak_envelope_data[i:i+self.dwFormat]) for i in range(0, len(self.peak_envelope_data), self.dwFormat)]
        self.len_peakEnvArr   = len(self.peakEnvArr)

        #import matplotlib
        #import matplotlib.pyplot as plt
        #plt.plot(self.peakEnvArr)
        #plt.savefig('fig.png')
        #print(int.from_bytes(b'\x08\x09', byteorder = 'little'))
        #quit()
        #for peak in self.peak_envelope_data:
        #    self.peakEnvArr.append(peak)

        #self.len = len(levlData)
        #self.remain_len = len(levlData[60:])
        #self.len_peak = len(self.peak_envelope_data)

    def print(self):
        for k, v in self.__dict__.items():
            if k == 'peakEnvArr':
                print(k, '=', v[0:10], '...')
            elif k == 'peak_envelope_data':
                print(k, '=', v[0:10], '...')
            else:
                print(k, '=', v)
        #print('\n', self.levl_ckID)
        #print('levl_ckSize', self.levl_ckSize)
        # print('dwVersion', self.dwVersion)
        # print('dwFormat', self.dwFormat)
        # print('dwPointsPerValue', self.dwPointsPerValue, '- 1 = only positive peak point, 2 = positive AND negative peak point')
        # print('dwBlockSize frames per value', self.dwBlockSize)
        # print('dwPeakChannels number of channels:', self.dwPeakChannels)
        # print('dwNumPeakFrames, number of peak frames', self.dwNumPeakFrames)
        # print('dwPosPeakOfPeaks, audio sample frame index', self.dwPosPeakOfPeaks)
        # print('dwOffsetToPeaks, offset to peaks', self.dwOffsetToPeaks, 'should usually be equal to the size of this header, but could also be higher')
        # print('time stamp of the peak data', self.strTimestamp)
        # print('unknown', self.unknown)
        # print('reserved', self.reserved)
        # print('peak envelope data', self.peak_envelope_data)

class cueChunk(Chunk):
    def __init__(self, cueData):
        self.cueNumPoints  = intb(cueData[0:4])
        self.cueDict = {}
        for i in range(self.cueNumPoints):
            start = i*24+4
            end = i*24+24+4
            self.currentCue = cueData[start:end]
            self.ID            = intb(self.currentCue[0:4])
            self.position      = intb(self.currentCue[4:8])
            self.riffID        =      self.currentCue[8:12].decode('ascii')
            self.chunkStart    = intb(self.currentCue[12:16])
            self.blockStart    = intb(self.currentCue[16:20])
            self.sampleOffset  = intb(self.currentCue[20:25])

            self.cueDict[i] = { 'ID'           : self.ID,
                                'position'     : self.position,
                                'riffID'       : self.riffID,
                                'chunkStart'   : self.chunkStart,
                                'blockStart'   : self.blockStart,
                                'sampleOffset' : self.sampleOffset }

    def print(self):
        print('cueNumPoints', self.cueNumPoints)
        for i, d in self.cueDict.items():
            print()
            for k, v in d.items():
                print(k, '=', v)

class LISTchunk(Chunk):
    def __init__(self, LISTdata):
        # Associated Data Listdata # https://sites.google.com/site/musicgapi/technical-documents/wav-file-format#listdata
        self.LISTdict = {}
        self.type_id = LISTdata[0:4].decode('ascii') # The type ID is used to identify the type of associated data listdata and is always adtl.')
        # The listdata type adtl is specific to the wave file format.
        #print(LISTdata)
        i = 0
        offset = 4
        while offset < len(LISTdata):
            self.current_ckID = LISTdata[offset:offset+4].decode('ascii')
            #print(self.current_ckID)
            if self.current_ckID == 'labl':
                self.subck = lablSubChunk(LISTdata, offset)
                self.subck.print()

            elif self.current_ckID == 'mtyp':
                self.subck = mtypSubChunk(LISTdata, offset)
                #self.subck.print()
            else:
                #print('LIST chunk id not defined.')
                pass
                #quit()
            offset = self.subck.new_offset
            self.LISTdict[i] = {'ckID' : self.current_ckID,
                                'subck' : self.subck.__dict__ }

            i += 1

    def print(self):
        for i, d in self.LISTdict.items():
            #print()
            for k, v in d.items():
                print(k, '=', v)

class lablSubChunk(LISTchunk):
    """ child of LISTchunk"""
    def __init__(self, LISTdata, offset):
        self.ID         =      LISTdata[ offset    : offset+4  ].decode('ascii')
        self.ckSize     = intb(LISTdata[ offset+4  : offset+8  ])

        self.cksp = self.ckSize + self.ckSize % 2 # checksize with padding if not even

        self.cuePointID = intb(LISTdata[ offset+8  : offset+12 ])
        self.text       =      LISTdata[ offset+12 : offset+8 + self.cksp ].decode('ascii')
        self.new_offset = offset + 8 + self.cksp

    def print(self):
        print('')
        for k, v in self.__dict__.items():
            print(' ', k, '=', v)

class mtypSubChunk(LISTchunk):
    def __init__(self, LISTdata, offset):
        self.ID            =      LISTdata[ offset+0 : offset+4 ].decode('ascii')
        self.ckSize        = intb(LISTdata[ offset+4 : offset+8 ])
        self.cksp          = self.ckSize + self.ckSize % 2
        self.cuePointID    = intb(LISTdata[ offset+8 : offset+12])
        self.text          =      LISTdata[ offset+12 : offset+8+self.cksp].decode('ascii')
        self.new_offset    = offset + 8 + self.cksp
    def print(self):
        for k, v in self.__dict__.items():
            print(k, '=', v)

class r64mChunk(Chunk):
    def __init__(self, r64mData):
        self.r64mDict = {}
        offset = 0
        i = 0
        while offset < len(r64mData):
            self.marker_entry = MarkerEntry(r64mData, offset)
            offset = self.marker_entry.new_offset
            self.r64mDict[i] = self.marker_entry.__dict__
            i += 1

    def print(self):
        #print('\nRF64 is a BWF-compatible multichannel audio file format enabling file sizes to exceed 4 GB. It has been specified by the European Broadcasting Union.')
        #print('The 2009 version of RF64 added a <r64m> marker chunk to replace the functionality of the <cue> chunk for files larger than 4 Gbyte. This removed an ambiguous interpretation of the cue chunk that was observed by the EBU in some manufacturers’ products.')
        for i, d in self.r64mDict.items():
            print()
            for k, v in d.items():
                print(k, '=', v)

class MarkerEntry(r64mChunk):
    #### RF64 Marker Chunk
    def __init__(self, r64m, offset=0):
        self.offset = offset
        self.new_offset = self.offset + 320

        self.flags                  = intb(r64m[self.offset + 0   : self.offset + 4]) # flags field
        self.sampleOffsetLow        = intb(r64m[self.offset + 4   : self.offset + 8]) # marker's offset in samples in data chunk
        self.sampleOffsetHigh       = intb(r64m[self.offset + 8   : self.offset + 12])
        self.byteOffsetLow          = intb(r64m[self.offset + 12  : self.offset + 16]) # byte of the beginning of the nearest compressed frame next to marker (timely before)
        self.byteOffsetHigh         = intb(r64m[self.offset + 16  : self.offset + 20])
        self.intraSmplOffsetHigh    = intb(r64m[self.offset + 20  : self.offset + 24]) # marker's offset in samples relative to the position of the first sample in frame
        self.intraSmplOffsetLow     = intb(r64m[self.offset + 24  : self.offset + 28])
        self.labelText              =      r64m[self.offset + 28  : self.offset + 284].decode('ascii') # null terminated label string, (the encoding depends on the Bit 4 of "flags" field)
        self.labelChunkIdentifier   = intb(r64m[self.offset + 284 : self.offset + 288]) #link to 'labl' subchunk of 'list' chunk8
        self.guid                   =      r64m[self.offset + 288 : self.offset + 304]
        self.userData1              =      r64m[self.offset + 304 : self.offset + 308]
        self.userData2              =      r64m[self.offset + 308 : self.offset + 312]
        self.userData3              =      r64m[self.offset + 312 : self.offset + 316]
        self.userData4              =      r64m[self.offset + 316 : self.offset + 320]

    def print(self):
        print('\n')
        for k, v in self.__dict__.items():
            print(' ', k, '=', v)

class auxChunk(Chunk):
    def __init__(self, auxData):
        self.auxLevlLen = intb(auxData[0:4])
        self.auxLevl = []
        for i in range(self.auxLevlLen):
            self.auxLevl.append(intb(auxData[i*4+4:i*4+8]))

    def print(self):
        print('auxLevlLen' ,self.auxLevlLen)
        print(self.auxLevl[0:10], '...')

    def plot(self):
        import matplotlib
        import matplotlib.pyplot as plt
        plt.plot(self.auxLevl)
        plt.savefig('aux')

class factChunk(Chunk):
    """
    The fact chunk <fact–ck> is required for all WAVE formats other than WAVE_FORMAT_PCM.
    It stores file–dependent information about the contents of the WAVE data.
    It currently specifies the time length of the data in samples.
    """
    def __init__(self, ckData):
        self.dwFileSize = intb(ckData)

class SwedishRadioAudioFile:
    def __init__(self):
        Chunk.__init__(self)

    def read(self, file, read_until=''):
        with open(file, "rb") as f:
            ckID = 'foo'
            while ckID != read_until:

                ckID = f.read(4).decode('ascii')
                ckSize = intb(f.read(4))
                if not ckID =='RIFF':
                    ckData = f.read(ckSize)
                if ckID == 'RIFF':
                    self.riff_size = ckSize
                    self.file_type_header = f.read(4).decode('ascii')

                elif ckID == 'JUNK':
                    self.junkData = ckData # Dummy DATA
                elif ckID == 'bext':
                    self.bext = self.BextChunk(ckData)
                elif ckID == 'fmt ':
                    self.fmt = self.fmtChunk(ckData)
                elif ckID == 'fact':
                    self.fact = self.factChunk(ckData)
                elif ckID =='mext':
                    self.mext = self.mextChunk(ckData)
                elif ckID == 'data':
                    self.data = self.dataChunk(ckData)
                elif ckID == 'levl':
                    self.levl = self.levlChunk(ckData)
                elif ckID == 'aux ':
                    self.aux = self.auxChunk(ckData)
                elif ckID == 'cue ':
                    self.cue = self.cueChunk(ckData)
                elif ckID == 'LIST':
                    self.LIST = self.LISTchunk(ckData)
                elif ckID == 'r64m':
                    self.r64m = r64mChunk(ckData)

    def get_comment(self, file):
        self.read(file, read_until='bext')
        start_of_empty_bytes = self.bext.description.find("\x00")
        return self.bext.description[:start_of_empty_bytes]

if __name__ == '__main__':
    file = '/Users/admin/Dropbox/000000/SR160866_299DF59B6E294D658AAAB0C9A9BC1B31.WAV'
    #file = '/Users/admin/Desktop/sr/wavread/SR160873_CBA3EC15514B45F3A2D03C5283C8EB7D.WAV'
    #file = 'manymarker.WAV'
    #file = '/Users/admin/Downloads/SR181220_2A42F9FCC9CC4231ABA1F7579AD92BD3.WAV'
    file = '/Users/admin/Dropbox/sr/wavread/SR160873_A62419708806407CBB7D1C68335F99DD.WAV'
    file = r'/Users/admin/Dropbox/workspace/levelbox/input/SR160873_5CF54A90FCA049C4B9BBF0D92651FAD6.WAV'
    print('file:', file)

    sraf = SwedishRadioAudioFile()
    sraf.read(file)
    #comment = sraf.get_comment(file)
    #print(sraf.bext.description)

#s = Settings()
#s.print()



