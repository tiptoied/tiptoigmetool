import struct

class GmeFile:
    def __init__(self, input_buffer):
        self.gme_file_buffer = input_buffer
        self.play_script_table_offset = struct.unpack("<I", self.gme_file_buffer[0x00:0x04])[0]
        self.media_table_offset = struct.unpack("<I", self.gme_file_buffer[0x04:0x08])[0]
        self.game_table_offset = struct.unpack("<I", self.gme_file_buffer[0x10:0x14])[0]
        self.product_id = struct.unpack("<I", self.gme_file_buffer[0x14:0x18])[0]
        self.raw_xor = struct.unpack("<I", self.gme_file_buffer[0x1C:0x20])[0]
        self.copy_media_table_offset = struct.unpack("<I", self.gme_file_buffer[0x60:0x64])[0]

        self.game1_binaries_table = struct.unpack("<I", self.gme_file_buffer[0x90:0x94])[0]
        self.game2N_binaries_table = struct.unpack("<I", self.gme_file_buffer[0x98:0x9C])[0]
        self.main1_binary_table = struct.unpack("<I", self.gme_file_buffer[0xA0:0xA4])[0]
        self.main2N_binary_table = struct.unpack("<I", self.gme_file_buffer[0xA8:0xAC])[0]
        self.main3L_binary_table = struct.unpack("<I", self.gme_file_buffer[0xC8:0xCC])[0]
        self.game3L_binaries_table = struct.unpack("<I", self.gme_file_buffer[0xCC:0xD0])[0]

        if self.copy_media_table_offset == 0:
            self.media_table_size = struct.unpack("<I", self.gme_file_buffer[self.media_table_offset:self.media_table_offset + 4])[0] - self.media_table_offset
        else:
            self.media_table_size = self.copy_media_table_offset - self.media_table_offset

        self.media_segments = []  # parse media table to json
        for i in range(0, self.media_table_size, 8):
            json = {
                "offset": struct.unpack("<I", self.gme_file_buffer[self.media_table_offset + i:self.media_table_offset + i + 4])[0],
                "size": struct.unpack("<I", self.gme_file_buffer[self.media_table_offset + i + 4:self.media_table_offset + i + 8])[0],
                "number": len(self.media_segments)
            }
            self.media_segments.append(json)

        if self.gme_file_buffer[self.media_segments[0]["offset"] + 1] == self.gme_file_buffer[self.media_segments[0]["offset"] + 2]:
            self.xor = ord("O") ^ self.gme_file_buffer[self.media_segments[0]["offset"]]
        elif self.gme_file_buffer[self.media_segments[0]["offset"] + 2] == self.gme_file_buffer[self.media_segments[0]["offset"] + 3]:
            self.xor = ord("R") ^ self.gme_file_buffer[self.media_segments[0]["offset"]]
        else:
            print("Cant get xor value")

    def crypt(self, input_buffer):
        inv_key = self.xor ^ 0xFF
        return bytes(x if x in [0x00, 0xff, self.xor, inv_key] else x ^ self.xor for x in input_buffer)

    def replace_media_file(self, content, media_id):
        enc_content = self.crypt(content)
        offset = self.media_segments[media_id]["offset"]
        size = self.media_segments[media_id]["size"]

        if len(enc_content) > size:
            print(f"Warning: File with id {media_id} is too large, it will be cut off.")

        self.gme_file_buffer = self.gme_file_buffer[:offset] + enc_content + self.gme_file_buffer[offset + size:]

    def add_media_file(self, content, media_id):
        enc_content = self.crypt(content)
        media_offset = len(self.gme_file_buffer) - 4
        checksum = self.gme_file_buffer[-4:]  # TODO: public checksum
        new_buffer_arr = [self.gme_file_buffer[:-4], enc_content, checksum]
        self.gme_file_buffer = b"".join(new_buffer_arr)

        self.media_segments[media_id]["offset"] = media_offset
        self.media_segments[media_id]["size"] = len(enc_content)
        self.media_segments[media_id]["relocated"] = True

    def extract_file(self, media_id):
        offset = self.media_segments[media_id]["offset"]
        size = self.media_segments[media_id]["size"]
        enc_content = self.gme_file_buffer[offset:offset + size]
        return self.crypt(enc_content)

    def write_media_table(self):  # after using this, tttool can no longer read this file
        if self.media_table_size != len(self.media_segments) * 8:
            print("Media table has different size")

        for i, segment in enumerate(self.media_segments):
            struct.pack_into("<I", self.gme_file_buffer, self.media_table_offset + i * 8, segment["offset"])
            struct.pack_into("<I", self.gme_file_buffer, self.media_table_offset + i * 8 + 4, segment["size"])

        for i, segment in enumerate(self.media_segments):
            struct.pack_into("<I", self.gme_file_buffer, self.media_table_offset + self.media_table_size + i * 8, segment["offset"])
            struct.pack_into("<I", self.gme_file_buffer, self.media_table_offset + self.media_table_size + i * 8 + 4, segment["size"])

    def change_smart_media(self, content, media_id):
        if self.media_segments[media_id]["size"] >= len(content):
            self.replace_media_file(content, media_id)
        else:
            self.add_media_file(content, media_id)

    def change_product_id(self, new_id):
        struct.pack_into("<I", self.gme_file_buffer, 0x14, new_id)
