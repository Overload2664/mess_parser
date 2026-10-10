import json

from char_map import code_to_char, char_to_code, magic_syntax, parse_magic_syntax, is_simple_command, is_complex_command, complex_commands, format_magic_byte, parse_magic_byte

class Mess:
    def __init__(self):
        self.content = []

    def read(self, path):
        with open(path, "rb") as mess_file:
            data = mess_file.read(4) # First 4 bytes are max_bank size
            # Bank number is more like max_bank - 1, because one is reserved for the byte just after the file
            max_bank = int.from_bytes(data, byteorder="big", signed=True) - 1 

            banks_table_offset = mess_file.read(4) # Second 4 bytes are offset to the bank table
            banks_table_offset = int.from_bytes(banks_table_offset, byteorder="big", signed=True)
            mess_file.seek(banks_table_offset)

            bank_table_offsets = {}
            for i in range(max_bank):
                bank_table_index = mess_file.read(2)
                bank_table_index = int.from_bytes(bank_table_index, byteorder="big", signed=False)

                bank_table_offset = mess_file.read(2)
                bank_table_offset = int.from_bytes(bank_table_offset, byteorder="big", signed=False)

                bank_table_offsets[bank_table_index] = bank_table_offset

            max_bank = len(bank_table_offsets) # Bank number is more like max_bank - 1 for some reason

            bank_offsets_offset = 4 # After the first 2 bytes is where the offsets are listed
            bank_offsets = []
            for i in range(max_bank):
                mess_file.seek(bank_offsets_offset + bank_table_offsets[i] * 4)
                bank_offset = mess_file.read(4)
                bank_offset = int.from_bytes(bank_offset, byteorder="big", signed=True)

                bank_offsets.append(bank_offset)

            for i in range(max_bank):
                bank_content = []

                mess_file.seek(bank_offsets[i])
                max_index = mess_file.read(4)
                max_index = int.from_bytes(max_index, byteorder="big", signed=True)

                indices_offset = []
                for j in range(max_index):
                    index_offset = mess_file.read(4)
                    index_offset = int.from_bytes(index_offset, byteorder="big", signed=True)

                    indices_offset.append(index_offset)

                for j in range(len(indices_offset)):
                    byte_array = bytearray()
                    mess_file.seek(bank_offsets[i] + indices_offset[j])
                    
                    while(True):
                        next_byte = mess_file.read(1)
                        byte_array += next_byte

                        if(next_byte == b'\x00'):
                            break

                    bank_content.append(byte_array)


                self.content.append(bank_content)

    def write(self, path):
        content = bytearray()
        # max_bank is more like bank number + 1 because one is reserved for the byte just after the end of the file
        max_bank = len(self.content) + 1
        max_bank_data = bytearray(max_bank.to_bytes(4, byteorder="big", signed=True))
        content += max_bank_data

        bank_table_offset = 4 + 4 + max_bank * 4
        content += bytearray(bank_table_offset.to_bytes(4, byteorder="big", signed=True))

        bank_offsets_locations = []
        for i in range(max_bank):
            bank_offsets_locations.append(len(content))
            content += b'\x00\x00\x00\x00'

        for i in range(len(self.content)):
            index = i
            offset = i + 1
            content += bytearray(index.to_bytes(2, byteorder="big", signed=False))
            content += bytearray(offset.to_bytes(2, byteorder="big", signed=False))

        for i in range(len(self.content)):
            bank = self.content[i]
            bank_offset = len(content)
            content[bank_offsets_locations[i]:bank_offsets_locations[i]+4] = bank_offset.to_bytes(4, byteorder="big", signed=True)

            max_index = len(bank)
            content += bytearray(max_index.to_bytes(4, byteorder="big", signed=True))

            index_offsets_locations = []
            for j in range(max_index + 1): # An extra index for the offset of the next byte right after the end of the bank
                index_offsets_locations.append(len(content))
                content += b'\x00\x00\x00\x00'

            for j in range(len(bank)):
                index_offset = len(content) - bank_offset
                content[index_offsets_locations[j]:index_offsets_locations[j]+4] = index_offset.to_bytes(4, byteorder="big", signed=True)
                content += bank[j]

                pad_size = (4 - len(content) % 4) % 4
                content += pad_size * b'\x00'

            after_indices_offset = len(content) - bank_offset
            content[index_offsets_locations[-1]:index_offsets_locations[-1]+4] = after_indices_offset.to_bytes(4, byteorder="big", signed=True)

        end_offset = len(content)
        content[bank_offsets_locations[-1]:bank_offsets_locations[-1]+4] = end_offset.to_bytes(4, byteorder="big", signed=True)

        with open(path, "wb") as f:
            f.write(content)

    def get(self, id):
        bank_id = id >> 16
        index_id = id  & 0xFFFF

        return self.content[bank_id][index_id]

    def change(self, id, byte_array):
        bank_id = id >> 16
        index_id = id  & 0xFFFF

        self.content[bank_id][index_id] = byte_array

    def add_bank(self):
        self.content.append([])

    def add(self, bank_id, byte_array):
        self.content[bank_id].append(byte_array)

    def to_json(self):
        content = []

        for bank in self.content:
            json_bank = []
            for mess in bank:
                mess_human = []
                i = 1 # The first is always the clear command so ignore it
                while i < len(mess) - 1: # Ignore the last character as it's null termination
                    code = mess[i]

                    if 48 <= code < 255:
                        char = code_to_char[code]
                        if char == "":
                            char = format_magic_byte(code)
                        mess_human.append(char)

                    elif code < 48 or code == 255:
                        if is_simple_command(code):
                            mess_human.append(magic_syntax(code))
                        elif is_complex_command(code):
                            if i + 1 >= len(mess):
                                raise ValueError("Complex command is missing its index")

                            index = mess[i + 1]
                            mess_human.append(magic_syntax(code, index))
                            i += 1  # Skip the index; it was consumed above
                        else:
                            mess_human.append(format_magic_byte(code))

                    else:
                        raise ValueError(f"Invalid number token: {code}")

                    i += 1

                json_bank.append("".join(mess_human))

            content.append(json_bank)
    
        return json.dumps(content, ensure_ascii=False, indent=4)

    def from_json(self, mess_json):
        content = json.loads(mess_json)

        new_content = []
        for bank in content:
            new_bank = []
            for mess in bank:
                new_mess = bytearray()
                new_mess += b'\x0B'
                i = 0
                while i < len(mess):
                    char = mess[i]
                    if(char == " "):
                        magic_code = parse_magic_syntax(char)
                        new_mess += magic_code.to_bytes(1, byteorder="big")
                    elif(char == "<"):
                        magic = [char]
                        while char != ">":
                            i += 1
                            char = mess[i]
                            magic.append(char)
                        magic = "".join(magic)
                        if(magic[1:3] == "0x"):
                            magic_code = parse_magic_byte(magic)
                            new_mess += magic_code.to_bytes(1, byteorder="big")
                        else:
                            magic_codes = parse_magic_syntax(magic)
                            for magic_code in magic_codes:
                                new_mess += magic_code.to_bytes(1, byteorder="big")
                    elif(char == "["):
                        shape = [char]
                        while char != "]":
                            i += 1
                            char = mess[i]
                            shape.append(char)
                        shape = "".join(shape)
                        shape_code = char_to_code[shape]
                        new_mess += shape_code.to_bytes(1, byteorder="big")
                    else:
                        code = char_to_code[char]
                        new_mess += code.to_bytes(1, byteorder="big")

                    i += 1
                new_mess += b'\x00'
                new_bank.append(new_mess)
            new_content.append(new_bank)

        self.content = new_content


lol = Mess()
lol.read("board_e.dat")
lol.write("bordo.dat")
xd = lol.to_json()

lmao = Mess()
lmao.from_json(xd)
lmao.write("bordo2.dat")

from pathlib import Path

Path("lol.json").write_text(
    xd,
    encoding="utf-16",
)
